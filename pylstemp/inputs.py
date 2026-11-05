"""Explicit quality-raster inputs for prepared Landsat 8/9 C2 arrays."""
from pathlib import Path
import numpy as np
from .calibration.quality import _quality_mask_from_arrays
from .messages import contextual_errors
from .validation import ensure_bool


@contextual_errors
def quality_mask(qa_pixel_path, qa_radsat_path, *, reference_path, exclude_water=False):
    """Read BOTH required QA files and return an aligned invalid-pixel mask.

    Parameters
    ----------
    qa_pixel_path, qa_radsat_path : path-like
        Original Collection 2 QA_PIXEL and QA_RADSAT GeoTIFFs for the same
        Landsat 8/9 scene. Both are mandatory; neither may be None.
    reference_path : path-like
        Input GeoTIFF whose shape, CRS and transform BOTH QA files must match.
        For cropped inputs supply identically cropped QA rasters. No resampling
        or reprojection is performed. The caller must verify scene identity.
    exclude_water : bool, default False
        Add QA_PIXEL water bit 7. Use True for the terrestrial Wang PWV recipe.

    Returns
    -------
    numpy.ndarray of bool
        True for invalid pixels: QA_PIXEL bits 0..5, QA_RADSAT optical B2/B4/B5
        saturation or terrain occlusion, QA nodata, and optionally water.
        QA_RADSAT optical bits do not encode thermal saturation.

    Notes
    -----
    Requires rasterio (the examples extra). Call BEFORE calibration, DOS/COST
    fitting, emissivity, PWV and LST; combine with each input's nodata mask and
    pass the result as mask= to each calculation. This is quality screening,
    separate from diagnostic confidence flags and atmospheric correction.
    """
    exclude_water = ensure_bool("exclude_water", exclude_water)
    import rasterio
    paths = dict(QA_PIXEL=qa_pixel_path, QA_RADSAT=qa_radsat_path,
                 reference_path=reference_path)
    for name, path in paths.items():
        if path is None or not Path(path).is_file():
            raise ValueError(f"{name} requires an existing GeoTIFF path: {path}")
    with rasterio.open(reference_path) as ref:
        if ref.crs is None:
            raise ValueError("reference_path must have a CRS.")
        grid = (ref.shape, ref.crs, ref.transform)
    values = {}
    invalid = np.zeros(grid[0], dtype=bool)
    for name in ("QA_PIXEL", "QA_RADSAT"):
        with rasterio.open(paths[name]) as src:
            if src.count != 1:
                raise ValueError(f"{name} must be a single-band QA raster.")
            if (src.shape, src.crs, src.transform) != grid:
                raise ValueError(f"Unaligned {name}: shape, CRS and transform must match reference_path.")
            data = src.read(1, masked=True)
            if not np.issubdtype(data.dtype, np.integer):
                raise ValueError(f"{name} must contain integer QA bit values, not calibrated data.")
            invalid |= np.ma.getmaskarray(data)
            values[name] = data.filled(0)
    return invalid | _quality_mask_from_arrays(values["QA_PIXEL"], values["QA_RADSAT"],
                                  exclude_water=exclude_water)
