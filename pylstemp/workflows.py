"""General Landsat scene composition with explicit raw/screened outputs."""
from dataclasses import dataclass
import json
from pathlib import Path
import numpy as np
from .api import split_window, water_vapor
from .utils import _compute_ndvi
from .validation import ensure_boolean_mask, ensure_bool, normalize_temperature_unit
from .quality import validate_quality_mode, QualityFlag, quality_legend
from .messages import contextual_errors
from ._version import __version__


@dataclass
class DuSceneResult:
    """Selected products, independent raw/screened chains and processing identity."""
    lst: np.ndarray
    pwv: object
    pwv_raw: object
    invalid_mask: np.ndarray
    provenance: dict
    window: tuple
    pwv_diagnostics: object = None
    intermediates: object = None
    lst_raw: object = None
    lst_screened: object = None
    pwv_screened: object = None
    quality_flags: object = None

    def export(self, scene, folder):
        """Write products, uint8 masks, uint16 flags and JSON processing/legend."""
        dest = Path(folder)
        dest.mkdir(parents=True, exist_ok=True)
        identity = dict(family="split_window", method="du-2015",
                        quality_mode=self.provenance["quality_mode"],
                        provenance_schema=self.provenance["provenance_schema"])
        def write(name, value, units, **kwargs):
            if value is not None:
                stage = dict(identity, product=Path(name).stem,
                             run_quality_mode=self.provenance["quality_mode"])
                if name.startswith("pwv"):
                    stage.update(family="water_vapor",method=self.provenance["pwv_method"])
                elif name.startswith("bt"):
                    stage.update(family="calibration",method="brightness")
                elif name.startswith("optical_"):
                    stage.update(family="calibration",method="toa-radiance" if self.provenance["optical_quantity"]=="radiance" else "toa-reflectance")
                elif name.startswith("emissivity_"):
                    stage.update(family="emissivity",method=self.provenance["emissivity_method"])
                elif name=="ndvi.tif":
                    stage.update(family="internal",method="ndvi")
                if "_raw" in name:stage["quality_mode"]="diagnostic"
                elif "_screened" in name:stage["quality_mode"]="screened"
                scene.write_geotiff(dest/name, value, window=self.window, units=units,
                                    metadata=stage, **kwargs)
        unit = self.provenance["lst_units"]
        write("lst_du.tif", self.lst, unit)
        write("lst_raw.tif", self.lst_raw, unit)
        write("lst_screened.tif", self.lst_screened, unit)
        write("lst_invalid.tif", self.invalid_mask, "boolean_true_is_invalid", dtype="uint8", nodata=None)
        for name, value in (("pwv",self.pwv),("pwv_raw",self.pwv_raw),("pwv_screened",self.pwv_screened)):
            write(name+".tif", value, "g/cm2")
        if self.pwv is not None:
            write("pwv_invalid.tif", ~np.isfinite(self.pwv), "boolean_true_is_invalid", dtype="uint8", nodata=None)
        write("quality_flags.tif", self.quality_flags, "bit_flags", dtype="uint16", nodata=None)
        if self.pwv_diagnostics is not None:
            for name, unit in (("ratio","dimensionless"),("chi_squared","dimensionless"),
                               ("sample_count","pixel_count"),("r_squared","dimensionless")):
                if name in self.pwv_diagnostics:
                    write("pwv_"+name+".tif", self.pwv_diagnostics[name], unit)
        if self.intermediates is not None:
            for name,value in self.intermediates.items():
                units = "kelvin" if name.startswith("bt") else (
                    "W m-2 sr-1 um-1" if name.startswith("optical_") and self.provenance["optical_quantity"]=="radiance" else "dimensionless")
                write(name+".tif", value, units)
        (dest/"provenance.json").write_text(json.dumps(self.provenance, indent=2, allow_nan=False),encoding="utf-8")
        (dest/"quality_legend.json").write_text(json.dumps(quality_legend(),indent=2),encoding="utf-8")


def scene_ndvi_range(scene, *, optical_quantity="radiance", block_rows=256, mask=None):
    """Scan all scene land pixels; reuse these bounds for every Wang tile."""
    if isinstance(block_rows, bool) or not isinstance(block_rows, int) or block_rows < 1:
        raise ValueError("block_rows must be a positive integer.")
    user_mask = None if mask is None else ensure_boolean_mask(mask, shape=scene.shape)
    lower, upper = np.inf, -np.inf
    height, width = scene.shape
    for row in range(0, height, block_rows):
        optical, thermal, invalid = scene.calibrated(
            (row, min(row + block_rows, height), 0, width),
            exclude_water=True, optical_quantity=optical_quantity)
        invalid = invalid | ~np.isfinite(thermal[10]) | ~np.isfinite(thermal[11])
        if user_mask is not None:
            invalid = invalid | user_mask[row:min(row + block_rows, height)]
        ndvi = _compute_ndvi(nir=optical[5], red=optical[4], mask=invalid)
        valid = ndvi[np.isfinite(ndvi)]
        if valid.size:
            lower, upper = min(lower, float(valid.min())), max(upper, float(valid.max()))
    if not np.isfinite(lower):
        raise ValueError("Scene has no valid land NDVI for Wang grouping.")
    return lower, upper


@contextual_errors
def du_from_scene(scene, *, window=None, pwv_mode="general", method="wang-2015",
                  optical_quantity="radiance", unit="kelvin", window_size=None,
                  group_count=3, chunk_rows=8, ndvi_range=None, mask=None,
                  pwv_options=None, diagnostics=False, hash_inputs=False,
                  quality_mode="screened"):
    """Compose fixed Du/Rongali with Wang/Ren PWV and explicit screening.

    method selects PWV, not LST. Screened mode preserves the default chain;
    diagnostic mode selects raw estimates with flags. Both raw and screened
    chains remain available. Spatial means use finite contributors from their
    own selected chain; flags are OR-reduced and carry SPATIAL_MEAN_PWV.
    """
    from .provenance import scene_provenance, optical_contract
    diagnostics = ensure_bool("diagnostics", diagnostics)
    hash_inputs = ensure_bool("hash_inputs", hash_inputs)
    diagnostic = validate_quality_mode(quality_mode)
    optical_contract("rongali-2018",optical_quantity)
    units = normalize_temperature_unit(unit)
    if pwv_mode not in {"general","mean","raster"}:
        raise ValueError("pwv_mode must be general, mean or raster.")
    if method not in {"wang-2015","ren-2015"}:
        raise ValueError("method must be wang-2015 or ren-2015.")
    size = (33 if method=="ren-2015" else 21) if window_size is None else window_size
    if isinstance(size,(bool,np.bool_)) or not isinstance(size,(int,np.integer)) or size<3 or size%2==0:
        raise ValueError("window_size must be an odd integer >=3.")
    options = {} if pwv_options is None else dict(pwv_options)
    if set(options)-{"min_samples","quality_threshold","ndvi_filter"}:
        raise ValueError("pwv_options accepts min_samples, quality_threshold and ndvi_filter only.")
    if method=="wang-2015" and options:
        raise ValueError("pwv_options apply to Ren only.")
    if method=="ren-2015" and (ndvi_range is not None or group_count!=3):
        raise ValueError("Ren does not use Wang ndvi_range/group_count.")
    height,width=scene.shape
    core=(0,height,0,width) if window is None else tuple(window)
    if len(core)!=4 or any(isinstance(v,(bool,np.bool_)) or not isinstance(v,(int,np.integer)) for v in core):
        raise ValueError("window must contain four integer bounds.")
    r0,r1,c0,c1=core
    if not (0<=r0<r1<=height and 0<=c0<c1<=width):
        raise ValueError("window lies outside the scene.")
    caller_mask=None if mask is None else ensure_boolean_mask(mask,shape=scene.shape)
    radius=size//2 if pwv_mode!="general" else 0
    halo=(max(0,r0-radius),min(height,r1+radius),max(0,c0-radius),min(width,c1+radius))
    hr0,hr1,hc0,hc1=halo
    select=np.s_[r0-hr0:r1-hr0,c0-hc0:c1-hc0]
    optical,thermal,invalid=scene.calibrated(halo,exclude_water=pwv_mode!="general",optical_quantity=optical_quantity)
    if caller_mask is not None:invalid=invalid|caller_mask[hr0:hr1,hc0:hc1]
    raw=screened=pwv=details=None
    selected_input=screened_input=raw_input=None
    upstream=None
    bounds_source="unused"
    lower=.06 if method=="ren-2015" else .066
    mean_contributors=screened_contributors=raw_contributors=0
    def aggregate(values, *, require):
        valid=np.isfinite(values)
        if not valid.any():
            if require:raise ValueError("No accepted PWV samples in the output window; mean cannot be computed.")
            return np.full(values.shape,np.nan),valid
        return float(values[valid].mean()),valid
    if pwv_mode!="general":
        if method=="wang-2015":
            if ndvi_range is None and np.any(~invalid):
                ndvi_range=scene_ndvi_range(scene,optical_quantity=optical_quantity,mask=caller_mask)
                bounds_source="scene_scan"
            else:bounds_source="caller_full_scene" if ndvi_range is not None else "no_valid_halo_samples"
        else:bounds_source="local_ndvi_screen" if options.get("ndvi_filter",True) else "thermal_only"
        result=water_vapor(thermal[10],thermal[11],red=optical[4],nir=optical[5],method=method,
            mask=invalid,window_size=size,chunk_rows=chunk_rows,return_diagnostics=True,
            quality_mode=quality_mode,**(dict(group_count=group_count,ndvi_range=ndvi_range) if method=="wang-2015" else options))
        details={key:(value[select] if isinstance(value,np.ndarray) else value) for key,value in result.items()}
        raw=details["raw_water_vapor"]
        estimator_screened=details["screened_water_vapor"]
        screened=np.where((estimator_screened>=lower)&(estimator_screened<=6.3),estimator_screened,np.nan)
        pwv=raw if diagnostic else screened
        selected_input=pwv
        raw_input=raw
        screened_input=screened
        upstream=details["quality_flags"].copy()
        if pwv_mode=="mean":
            raw_input,raw_donors=aggregate(raw,require=False)
            screened_input,screened_donors=aggregate(screened,require=not diagnostic)
            selected_input=raw_input if diagnostic else screened_input
            raw_contributors=int(raw_donors.sum());screened_contributors=int(screened_donors.sum())
            mean_contributors=raw_contributors if diagnostic else screened_contributors
            merged=np.bitwise_or.reduce(upstream[raw_donors],initial=np.uint16(0))
            upstream=np.full(pwv.shape,int(merged)|int(QualityFlag.SPATIAL_MEAN_PWV),dtype=np.uint16)
    kwargs=dict(method="du-2015",unit=units,mask=invalid[select],optical_quantity=optical_quantity)
    optical_args=(thermal[10][select],thermal[11][select],optical[4][select],optical[5][select])
    result=split_window(*optical_args,water_vapor=raw_input,return_diagnostics=True,
                        quality_mode="diagnostic",pwv_quality_flags=upstream,**kwargs)
    complete_screened=split_window(*optical_args,water_vapor=screened_input,**kwargs)
    selected_lst=result["raw_lst"] if diagnostic else complete_screened
    intermediates=None
    if diagnostics:
        intermediates={name:result[name] for name in ("ndvi","emissivity_10","emissivity_11")}
        intermediates.update(optical_red=optical[4][select],optical_nir=optical[5][select],bt10=thermal[10][select],bt11=thermal[11][select])
    provenance=dict(version=__version__,product_id=scene.product_id,sensor=scene.sensor,
        family="split_window",method="du-2015",lst_method="du-2015",quality_mode=quality_mode,
        pwv_mode=pwv_mode,pwv_method=None if pwv_mode=="general" else method,
        emissivity_method="rongali-2018",optical_quantity=optical_quantity,lst_units=units,pwv_units="g/cm2",
        window=list(core),halo=list(halo),window_size=int(size),group_count=group_count,chunk_rows=chunk_rows,
        ndvi_range=None if ndvi_range is None else [float(x) for x in ndvi_range],ndvi_range_source=bounds_source,
        accepted_pwv_domain=[lower,6.3],ren_options=options if method=="ren-2015" else None,
        pwv_raw_semantics="mathematically calculable estimator before operational screening",
        pwv_screened_semantics="estimator screening followed by the Du-chain PWV domain",
        lst_raw_semantics="complete raw chain; Du uses the documented general fallback outside its PWV bins",
        lst_screened_semantics="complete screened chain, including screened PWV and its own spatial mean",
        mean_pwv=float(selected_input) if pwv_mode=="mean" and np.isscalar(selected_input) else None,
        mean_contributor_count=mean_contributors,raw_mean_contributor_count=raw_contributors,screened_mean_contributor_count=screened_contributors,
        flag_semantics="raw LST candidate with propagated PWV rejection reasons",
        pwv_accepted_pixels=0 if screened is None else int(np.isfinite(screened).sum()),
        pwv_invalid_pixels=0 if pwv is None else int((~np.isfinite(pwv)).sum()),
        lst_invalid_pixels=int((~np.isfinite(selected_lst)).sum()),total_pixels=int(selected_lst.size),
        user_mask_supplied=mask is not None,water_excluded=pwv_mode!="general",
        window_support_note="pixels on supplied grid; resampling does not create independent native TIRS samples",
        scientific_status="Numerical implementation checks; no field accuracy certification.")
    provenance.update(scene_provenance(scene,emissivity_method="rongali-2018",optical_quantity=optical_quantity,
                       mask=caller_mask,hash_inputs=hash_inputs,pwv_method=None if pwv_mode=="general" else method))
    provenance["intermediate_outputs"]=[] if intermediates is None else list(intermediates)
    return DuSceneResult(selected_lst,pwv,raw,~np.isfinite(selected_lst),provenance,core,
        details,intermediates,result["raw_lst"],complete_screened,screened,result["quality_flags"])
