"""Explicit scene workflows; low-level split_window semantics are unchanged."""
from dataclasses import dataclass
import json
from pathlib import Path
import numpy as np
from .api import split_window, water_vapor
from .utils import _compute_ndvi
from .validation import ensure_boolean_mask


@dataclass
class DuSceneResult:
    """Aligned outputs and provenance. True mask values identify rejected pixels."""
    lst: np.ndarray
    pwv: object
    pwv_raw: object
    invalid_mask: np.ndarray
    provenance: dict
    window: tuple
    pwv_diagnostics: object = None

    def export(self, scene, folder):
        """Export LST, PWV, rejection masks and a JSON provenance sidecar."""
        dest = Path(folder)
        dest.mkdir(parents=True, exist_ok=True)
        scene.write_geotiff(dest / "lst_du.tif", self.lst,
                            window=self.window, units=self.provenance["lst_units"])
        scene.write_geotiff(dest / "lst_invalid.tif", self.invalid_mask,
                            window=self.window, units="boolean_true_is_invalid")
        if self.pwv is not None:
            for name, value in (("pwv", self.pwv), ("pwv_raw", self.pwv_raw)):
                scene.write_geotiff(dest / (name + ".tif"), value,
                                    window=self.window, units="g/cm2")
            scene.write_geotiff(dest / "pwv_invalid.tif", ~np.isfinite(self.pwv),
                                window=self.window, units="boolean_true_is_invalid")
        if self.pwv_diagnostics is not None:
            for key,unit in (("ratio","dimensionless"),("chi_squared","dimensionless"),
                             ("sample_count","pixel_count")):
                scene.write_geotiff(dest / ("pwv_"+key+".tif"),
                    self.pwv_diagnostics[key],window=self.window,units=unit)
        (dest / "provenance.json").write_text(
            json.dumps(self.provenance, indent=2, allow_nan=False), encoding="utf8")


def scene_ndvi_range(scene, *, optical_quantity="radiance", block_rows=256):
    """Scan all scene land pixels; reuse these bounds for every Wang tile."""
    if isinstance(block_rows, bool) or not isinstance(block_rows, int) or block_rows < 1:
        raise ValueError("block_rows must be a positive integer.")
    lower, upper = np.inf, -np.inf
    height, width = scene.shape
    for row in range(0, height, block_rows):
        optical, thermal, mask = scene.calibrated(
            (row, min(row + block_rows, height), 0, width),
            exclude_water=True, optical_quantity=optical_quantity)
        mask = mask | ~np.isfinite(thermal[10]) | ~np.isfinite(thermal[11])
        ndvi = _compute_ndvi( nir=optical[5], red=optical[4], mask=mask)
        valid = ndvi[np.isfinite(ndvi)]
        if valid.size:
            lower, upper = min(lower, float(valid.min())), max(upper, float(valid.max()))
    if not np.isfinite(lower):
        raise ValueError("Scene has no valid land NDVI for Wang grouping.")
    return lower, upper


def du_from_scene(scene, *, window=None, pwv_mode="general", pwv_method="wang-2015",
                  emissivity_method="gopinadh-2018", optical_quantity="radiance",
                  unit="kelvin", window_size=None, group_count=3, chunk_rows=8,
                  ndvi_range=None, mask=None, pwv_options=None):
    """Compute Du with general, mean or raster PWV, explicitly selecting Wang/Ren.

    Wang uses global scene NDVI bounds and a 21-pixel default. Ren uses local
    NDVI screening, diagnostics and a 33-pixel scene default (about 1 km on
    Landsat's usual 30-m delivery grid), an explicit resampling adaptation.
    Supply window_size for another grid/support; no spatial upsampling is done.
    Mean averages accepted PWV over the requested output window only.
    mask must span the whole scene so halo samples are excluded consistently.
    Ren pwv_options may set min_samples, quality_threshold and ndvi_filter.
    """
    if pwv_mode not in {"general", "mean", "raster"}:
        raise ValueError("pwv_mode must be general, mean or raster.")
    if pwv_method not in {"wang-2015","ren-2015"}:
        raise ValueError("pwv_method must be wang-2015 or ren-2015.")
    if window_size is None:
        window_size = 33 if pwv_method == "ren-2015" else 21
    if isinstance(window_size, bool) or not isinstance(window_size, int) or window_size < 3 or window_size % 2 == 0:
        raise ValueError("window_size must be an odd integer >= 3.")
    options = {} if pwv_options is None else dict(pwv_options)
    if set(options)-{"min_samples","quality_threshold","ndvi_filter"}:
        raise ValueError("Unsupported pwv_options; use min_samples, quality_threshold or ndvi_filter.")
    if pwv_method == "wang-2015" and options:
        raise ValueError("pwv_options apply to Ren only.")
    if pwv_method == "ren-2015" and (ndvi_range is not None or group_count != 3):
        raise ValueError("Ren does not use Wang global ndvi_range/group_count.")
    lower_domain = .06 if pwv_method == "ren-2015" else .066
    height, width = scene.shape
    core = (0, height, 0, width) if window is None else tuple(window)
    r0, r1, c0, c1 = core
    if not (0 <= r0 < r1 <= height and 0 <= c0 < c1 <= width):
        raise ValueError("Output window lies outside scene.")
    user_mask = None if mask is None else ensure_boolean_mask(mask, shape=scene.shape)
    radius = window_size // 2 if pwv_mode != "general" else 0
    halo = (max(0, r0-radius), min(height, r1+radius),
            max(0, c0-radius), min(width, c1+radius))
    hr0, hr1, hc0, hc1 = halo
    select = np.s_[r0-hr0:r1-hr0, c0-hc0:c1-hc0]
    optical, thermal, invalid = scene.calibrated(
        halo, exclude_water=pwv_mode != "general", optical_quantity=optical_quantity)
    if user_mask is not None:
        invalid = invalid | user_mask[hr0:hr1, hc0:hc1]
    bounds_source = "unused"
    raw = pwv = supplied = diagnostics = None
    if pwv_mode != "general":
        if pwv_method == "wang-2015":
            bounds_source = "caller_full_scene" if ndvi_range is not None else "scene_scan"
            if ndvi_range is None:
                ndvi_range = scene_ndvi_range(scene, optical_quantity=optical_quantity)
            raw = water_vapor(thermal[10], thermal[11], red=optical[4], nir=optical[5], method=pwv_method,
                              mask=invalid, window_size=window_size, group_count=group_count,
                              chunk_rows=chunk_rows, ndvi_range=ndvi_range)[select]
            accepted = raw
        else:
            result = water_vapor(thermal[10], thermal[11], red=optical[4], nir=optical[5], method=pwv_method,
                mask=invalid,window_size=window_size,chunk_rows=chunk_rows,
                return_diagnostics=True,**options)
            diagnostics = {key:value[select] for key,value in result.items()}
            raw = diagnostics["raw_water_vapor"]
            accepted = diagnostics["water_vapor"]
            bounds_source = "local_ndvi_screen" if options.get("ndvi_filter",True) else "thermal_only"
        pwv = np.where((accepted >= lower_domain) & (accepted <= 6.3), accepted, np.nan)
        supplied = pwv
        if pwv_mode == "mean":
            valid = pwv[np.isfinite(pwv)]
            if not valid.size:
                raise ValueError("No in-domain PWV samples in output window; mean cannot be computed.")
            supplied = float(valid.mean())
    lst = split_window(thermal[10][select], thermal[11][select],
                       optical[4][select], optical[5][select], lst_method="du-2015",
                       emissivity_method=emissivity_method, unit=unit,
                       water_vapor=supplied, mask=invalid[select])
    from . import __version__
    from .validation import normalize_temperature_unit
    provenance = dict(version=__version__, product_id=scene.product_id,
        sensor=scene.sensor, lst_method="du-2015", pwv_mode=pwv_mode,
        pwv_method=None if pwv_mode == "general" else pwv_method,
        chain="Du general" if pwv_mode == "general" else "Ren/MSWCVR -> Du" if pwv_method == "ren-2015" else "alternative Wang -> Du",
        coefficient_selection="general" if pwv_mode == "general" else "per-pixel" if pwv_mode == "raster" else "ROI mean",
        emissivity_method=emissivity_method, optical_quantity=optical_quantity,
        lst_units=normalize_temperature_unit(unit), pwv_units="g/cm2",
        window=list(core), halo=list(halo), window_size=window_size,
        group_count=group_count, chunk_rows=chunk_rows,
        ndvi_range=None if ndvi_range is None else [float(v) for v in ndvi_range],
        ndvi_range_source=bounds_source, accepted_pwv_domain=[lower_domain, 6.3],
        ren_options=None if diagnostics is None else dict(min_samples=options.get("min_samples",10), quality_threshold=options.get("quality_threshold",.95), ndvi_filter=options.get("ndvi_filter",True)),
        window_support_note="pixels on supplied grid; resampled pixels are not independent native TIRS samples",
        mean_pwv=float(supplied) if pwv_mode == "mean" else None,
        pwv_invalid_pixels=0 if raw is None else int((~np.isfinite(raw)).sum()),
        pwv_out_of_domain_pixels=0 if raw is None else int((np.isfinite(raw) & ((raw < lower_domain) | (raw > 6.3))).sum()),
        pwv_quality_rejected_pixels=0 if diagnostics is None else int((np.isfinite(raw) & (diagnostics["chi_squared"] < options.get("quality_threshold",.95))).sum()),
        pwv_accepted_pixels=0 if pwv is None else int(np.isfinite(pwv).sum()),
        lst_invalid_pixels=int((~np.isfinite(lst)).sum()), total_pixels=lst.size,
        user_mask_supplied=mask is not None,
        water_excluded=pwv_mode != "general",
        scientific_status="Implementation checks only; no field accuracy validation. Landsat 9 transfer experimental.")
    return DuSceneResult(lst, pwv, raw, ~np.isfinite(lst), provenance, core, diagnostics)
