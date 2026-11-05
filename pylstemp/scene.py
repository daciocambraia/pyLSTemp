"""Read aligned Landsat Level-1 scenes, with optional rasterio or Pillow.

The Pillow backend preserves verified GeoTIFF tags; it is useful where GDAL
DLL loading is unavailable. Reading via Pillow may cache a full band in RAM.
"""
from pathlib import Path
import warnings
import json
from ._version import __version__
from .messages import contextual_errors
from .validation import ensure_bool
import numpy as np
from .calibration import read_mtl, toa_reflectance, toa_radiance, brightness_from_mtl
from .calibration.quality import _quality_mask_from_arrays

GEOTAGS = (33550, 33922, 34264, 34735, 34736, 34737)


class LandsatScene:
    """An aligned B4/B5/B10/B11 + QA scene (B2 is optional); inputs are never modified."""

    def __init__(self, folder, *, backend="auto"):
        self.folder = Path(folder)
        mtls = list(self.folder.glob("*_MTL.txt"))
        if len(mtls) != 1:
            raise ValueError("Scene folder must contain exactly one *_MTL.txt.")
        self.mtl_path = mtls[0]
        self.metadata = read_mtl(self.mtl_path)
        self.sensor = self.metadata["SPACECRAFT_ID"].lower()
        self.product_id = str(self.metadata["LANDSAT_PRODUCT_ID"])
        if not str(self.metadata.get("PROCESSING_LEVEL", "")).startswith("L1"):
            raise ValueError("This reader requires Level-1 B* DN, not Level-2 ST/SR.")
        if backend not in ("auto", "rasterio", "pillow"):
            raise ValueError("backend must be auto, rasterio or pillow.")
        rasterio = None
        if backend != "pillow":
            try:
                import rasterio
            except (ImportError, OSError) as exc:
                if backend == "rasterio":
                    raise
                warnings.warn(f"Rasterio unavailable; using Pillow GeoTIFF reader: {exc}", RuntimeWarning)
        self.backend = "rasterio" if rasterio is not None else "pillow"
        self.sources, self.paths = {}, {}
        tokens = ["B4", "B5", "B10", "B11", "QA_PIXEL", "QA_RADSAT"]
        if (self.folder / f"{self.product_id}_B2.TIF").exists():
            tokens.append("B2")
        sza = self.folder / f"{self.product_id}_SZA.TIF"
        if sza.exists():
            tokens.append("SZA")
        try:
            for token in tokens:
                path = self.folder / f"{self.product_id}_{token}.TIF"
                if not path.exists():
                    raise ValueError(f"Missing scene file: {path.name}")
                self.paths[token] = path
                if rasterio is not None:
                    src = rasterio.open(path)
                    grid = (src.height, src.width, src.crs, src.transform)
                else:
                    from PIL import Image
                    src = Image.open(path)
                    grid = (src.height, src.width) + tuple(tuple(src.tag_v2.get(t, ())) if t != 34737
                        else str(src.tag_v2.get(t, "")) for t in GEOTAGS)
                    if not src.tag_v2.get(34735) or not (src.tag_v2.get(33550) and src.tag_v2.get(33922) or src.tag_v2.get(34264)):
                        raise ValueError("GeoTIFF coordinate/transform tags are required.")
                self.sources[token] = src
                if token == "B4":
                    self.grid = grid
                    self.shape = (src.height, src.width)
                elif grid != self.grid:
                    raise ValueError(f"Unaligned band: {token}. Reprojection must be explicit.")
        except Exception:
            self.close()
            raise

    @contextual_errors
    def read(self, token, window=None, *, masked=False):
        """Read a raw band; masked=True respects stored nodata and nonfinite pixels."""
        masked = ensure_bool("masked", masked)
        if token not in self.sources:
            raise ValueError(f"Unknown band token {token!r}; available: {sorted(self.sources)}.")
        src = self.sources[token]
        window = (0,self.shape[0],0,self.shape[1]) if window is None else tuple(window)
        if len(window)!=4 or any(isinstance(v,(bool,np.bool_)) or not isinstance(v,(int,np.integer)) for v in window):
            raise ValueError("Read window must contain four integer bounds.")
        r0,r1,c0,c1=window
        if not (0<=r0<r1<=self.shape[0] and 0<=c0<c1<=self.shape[1]):
            raise ValueError("Read window lies outside scene.")
        if self.backend == "rasterio":
            return src.read(1,window=((r0,r1),(c0,c1)),masked=masked)
        data=np.array(src.crop((c0,r0,c1,r1)))
        if not masked:return data
        invalid=~np.isfinite(data)
        nodata=getattr(src,"tag_v2",{}).get(42113)
        if nodata is not None:
            nodata=float(nodata)
            invalid |= np.isnan(data) if np.isnan(nodata) else data==nodata
        return np.ma.array(data,mask=invalid)

    @contextual_errors
    def quality_mask(self, window=None, *, exclude_water=False):
        """Decode both aligned QA rasters, including their stored nodata."""
        qa=self.read("QA_PIXEL",window,masked=True)
        sat=self.read("QA_RADSAT",window,masked=True)
        invalid=np.ma.getmaskarray(qa)|np.ma.getmaskarray(sat)
        return invalid|_quality_mask_from_arrays(qa.filled(0),sat.filled(0),exclude_water=exclude_water)

    def calibrated(self, window=None, *, exclude_water=False, optical_quantity="radiance"):
        """Return optical bands, thermal TOA BT [K], and invalid-pixel QA mask.

        optical_quantity='radiance' (default): TOA L [W m-2 sr-1 um-1].
        optical_quantity='reflectance': TOA rho [dimensionless], SZA/MTL-corrected.
        B4/B5 are always returned; B2 is returned only if present. Both modes
        use the same conservative B2/B4/B5 QA policy and valid-solar-angle mask
        when SZA is supplied, to make controlled quantity comparisons possible.
        """
        if optical_quantity not in {"radiance", "reflectance"}:
            raise ValueError("optical_quantity must be 'radiance' or 'reflectance'.")
        mask = self.quality_mask(window, exclude_water=exclude_water)
        optical = {}
        sun = None
        if "SZA" in self.sources:
            # USGS angle-band units are hundredths of a degree.
            sza = self.read("SZA", window, masked=True).astype(float).filled(np.nan)
            sun = 90 - sza * 0.01
            mask |= ~np.isfinite(sza) | (sza == -32768) | (sza < 0) | (sza >= 9000)
        for band in (2, 4, 5):
            if f"B{band}" not in self.sources:
                continue
            dn = self.read(f"B{band}", window, masked=True)
            if optical_quantity == "radiance":
                optical[band] = toa_radiance(dn, metadata=self.metadata, band=band, mask=mask)
            else:
                optical[band] = toa_reflectance(dn, metadata=self.metadata, band=band, mask=mask, sun_elevation=sun)
        thermal = {band: brightness_from_mtl(self.read(f"B{band}", window, masked=True),
            metadata=self.metadata, band=band, mask=mask) for band in (10, 11)}
        return optical, thermal, mask

    @contextual_errors
    def write_geotiff(self, path, array, *, window=None, units="", dtype=None, nodata="auto", metadata=None):
        """Export floats, masks or flags without changing the spatial grid.

        dtype=None uses uint8 for Boolean masks, preserves supported integer
        dtypes, and uses float32 for floating measurements. nodata='auto' is
        NaN for floats and None for integer masks/flags; zero remains valid.
        metadata must be JSON-serializable and is stored in the GeoTIFF.
        """
        array = np.asarray(array)
        selected_dtype = np.dtype(dtype or ("uint8" if array.dtype.kind=="b" else
                                  array.dtype if array.dtype.kind in "iu" else "float32"))
        if selected_dtype.name not in {"uint8","uint16","uint32","int16","int32","float32","float64"}:
            raise ValueError("Unsupported export dtype; use uint8/uint16/uint32/int16/int32/float32/float64.")
        if array.dtype.kind not in "biuf":
            raise ValueError("Export array must contain real numeric measurements, masks or flags.")
        if selected_dtype.kind in "iu":
            limits = np.iinfo(selected_dtype)
            if not np.isfinite(array).all() or np.any(array < limits.min) or np.any(array > limits.max) or np.any(array != np.floor(array)):
                raise ValueError("Integer export would lose values; use a matching integer dtype or a float dtype.")
        selected_nodata = (np.nan if selected_dtype.kind=="f" else None) if isinstance(nodata,str) and nodata=="auto" else nodata
        if selected_nodata is not None and selected_dtype.kind in "iu":
            if not np.isfinite(selected_nodata) or selected_nodata != int(selected_nodata) or not limits.min <= selected_nodata <= limits.max:
                raise ValueError("nodata must fit the selected integer dtype; use None to preserve all mask values.")
        processing = dict(metadata or {})
        serialized = json.dumps(processing, allow_nan=False, sort_keys=True)
        output_tags = dict(units=units, product_id=self.product_id, pylstemp_version=__version__,
                           processing_metadata=serialized)
        for key in ("family","method","quality_mode"):
            if key in processing: output_tags[key] = str(processing[key])
        core = (0, self.shape[0], 0, self.shape[1]) if window is None else tuple(window)
        if len(core) != 4 or any(isinstance(v, (bool, np.bool_)) or
                not isinstance(v, (int, np.integer)) for v in core):
            raise ValueError("Export window must contain four integer bounds.")
        r0, r1, c0, c1 = core
        if not (0 <= r0 < r1 <= self.shape[0] and 0 <= c0 < c1 <= self.shape[1]):
            raise ValueError("Export window lies outside scene.")
        if array.ndim != 2 or array.shape != (r1-r0, c1-c0):
            raise ValueError("Export array shape must match the scene or specified window.")
        if self.backend == "rasterio":
            from rasterio.windows import Window, transform
            import rasterio
            profile = self.sources["B4"].profile.copy()
            profile.update(dtype=selected_dtype.name, count=1, height=array.shape[0],
                           width=array.shape[1], nodata=selected_nodata, compress="deflate")
            if not profile.get("tiled", False):
                # GDAL strip outputs must not inherit tiled-only block options.
                profile.pop("blockxsize", None)
                profile.pop("blockysize", None)
            if window is not None:
                r0, r1, c0, c1 = window
                profile["transform"] = transform(Window(c0, r0, c1-c0, r1-r0), profile["transform"])
            with rasterio.open(path, "w", **profile) as dst:
                dst.write(np.asarray(array, dtype=selected_dtype), 1)
                dst.update_tags(**output_tags, AREA_OR_POINT=self.sources["B4"].tags().get("AREA_OR_POINT", "Area"))
        else:
            if selected_dtype.name not in {"uint8","uint16","int32","float32"}:
                raise ValueError("Pillow exports support uint8/uint16/int32/float32; use the Rasterio backend for this dtype.")
            from PIL import Image, TiffImagePlugin
            tags = TiffImagePlugin.ImageFileDirectory_v2()
            original = self.sources["B4"].tag_v2
            for key in GEOTAGS:
                if key in original:
                    tags[key] = original[key]
                    tags.tagtype[key] = original.tagtype[key]
            if window is not None:
                if 34264 in original:
                    raise ValueError("Pillow cropped matrix-transform export is unsupported.")
                r0, _, c0, _ = window
                sx, sy, sz = original[33550]
                tie = list(original[33922])
                tie[3] += c0*sx
                tie[4] -= r0*sy
                tags[33922] = tuple(tie)
            if selected_nodata is not None:
                tags[42113] = str(selected_nodata)
                tags.tagtype[42113] = 2
            tags[270] = json.dumps(output_tags, allow_nan=False, sort_keys=True)
            Image.fromarray(np.asarray(array, dtype=selected_dtype)).save(path,
                compression="tiff_adobe_deflate", tiffinfo=tags)

    def close(self):
        for source in getattr(self, "sources", {}).values():
            source.close()

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()
