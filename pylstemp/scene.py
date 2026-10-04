"""Read aligned Landsat Level-1 scenes, with optional rasterio or Pillow.

The Pillow backend preserves verified GeoTIFF tags; it is useful where GDAL
DLL loading is unavailable. Reading via Pillow may cache a full band in RAM.
"""
from pathlib import Path
import warnings
import numpy as np
from .calibration import read_mtl, toa_reflectance, brightness_from_mtl, quality_mask

GEOTAGS = (33550, 33922, 34264, 34735, 34736, 34737)


class LandsatScene:
    """An aligned B2/B4/B5/B10/B11 + QA scene; inputs are never modified."""

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
        tokens = ["B2", "B4", "B5", "B10", "B11", "QA_PIXEL", "QA_RADSAT"]
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
                if token == "B2":
                    self.grid = grid
                    self.shape = (src.height, src.width)
                elif grid != self.grid:
                    raise ValueError(f"Unaligned band: {token}. Reprojection must be explicit.")
        except Exception:
            self.close()
            raise

    def read(self, token, window=None):
        """window is (row_start, row_stop, column_start, column_stop)."""
        src = self.sources[token]
        if window is None:
            window = (0, self.shape[0], 0, self.shape[1])
        r0, r1, c0, c1 = window
        if not (0 <= r0 < r1 <= self.shape[0] and 0 <= c0 < c1 <= self.shape[1]):
            raise ValueError("Read window lies outside scene.")
        if self.backend == "rasterio":
            return src.read(1, window=((r0, r1), (c0, c1)))
        return np.array(src.crop((c0, r0, c1, r1)))

    def calibrated(self, window=None, *, exclude_water=False):
        """Return aligned TOA optical reflectance, BT kelvin and boolean QA."""
        mask = quality_mask(self.read("QA_PIXEL", window), self.read("QA_RADSAT", window),
                            exclude_water=exclude_water)
        optical = {}
        sun = None
        if "SZA" in self.sources:
            # USGS angle-band units are hundredths of a degree.
            sza = self.read("SZA", window)
            sun = 90 - sza.astype(float) * 0.01
            mask |= (sza == -32768) | (sza < 0) | (sza >= 9000)
        for band in (2, 4, 5):
            optical[band] = toa_reflectance(self.read(f"B{band}", window),
                metadata=self.metadata, band=band, mask=mask, sun_elevation=sun)
        thermal = {band: brightness_from_mtl(self.read(f"B{band}", window),
            metadata=self.metadata, band=band, mask=mask) for band in (10, 11)}
        return optical, thermal, mask

    def write_geotiff(self, path, array, *, window=None, units=""):
        """Write float32 GeoTIFF, preserving projection and shifted origin."""
        if self.backend == "rasterio":
            from rasterio.windows import Window, transform
            import rasterio
            profile = self.sources["B2"].profile.copy()
            profile.update(dtype="float32", count=1, height=array.shape[0],
                           width=array.shape[1], nodata=np.nan, compress="deflate")
            if window is not None:
                r0, r1, c0, c1 = window
                profile["transform"] = transform(Window(c0, r0, c1-c0, r1-r0), profile["transform"])
            with rasterio.open(path, "w", **profile) as dst:
                dst.write(np.asarray(array, dtype=np.float32), 1)
                dst.update_tags(units=units, product_id=self.product_id)
        else:
            from PIL import Image, TiffImagePlugin
            tags = TiffImagePlugin.ImageFileDirectory_v2()
            original = self.sources["B2"].tag_v2
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
            tags[42113] = "nan"
            tags.tagtype[42113] = 2
            tags[270] = f"pyLSTemp; {self.product_id}; units={units}"
            Image.fromarray(np.asarray(array, dtype=np.float32)).save(path,
                compression="tiff_adobe_deflate", tiffinfo=tags)

    def close(self):
        for source in getattr(self, "sources", {}).values():
            source.close()

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()
