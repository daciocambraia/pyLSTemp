"""Level-1 optical DN to solar-corrected TOA reflectance."""
import numpy as np
from ..messages import contextual_errors
from ..utils import apply_mask
from ..validation import to_float_array, ensure_boolean_mask, ensure_same_shape
from .metadata import _level1, _number


@contextual_errors
def toa_reflectance(dn, *, metadata, band, mask=None, sun_elevation=None):
    """Convert Level-1 optical DN to TOA reflectance (dimensionless).

    sun_elevation may be a scalar or an aligned per-pixel angle in degrees.
    By default the MTL scene-centre angle is used. Values are not clipped to
    [0, 1]: outliers remain available for quality assessment.


    Quality inputs
    --------------
    Before this calculation, call quality_mask(qa_pixel_path,
    qa_radsat_path, reference_path=...) and pass the aligned boolean result
    combined with input nodata as mask=. True means invalid. QA files are
    not read by this numerical function; mask=None applies no QA screening.
    LandsatScene.calibrated() prepares and returns its QA mask automatically.
    """
    _level1(metadata)
    if isinstance(band, (bool, np.bool_)) or not isinstance(band, (int, np.integer)) or band not in range(1, 10):
        raise ValueError("Optical band must be an integer from 1 to 9.")
    image = to_float_array("dn", dn)
    gain = _number(metadata, f"REFLECTANCE_MULT_BAND_{band}")
    bias = _number(metadata, f"REFLECTANCE_ADD_BAND_{band}")
    if gain <= 0:
        raise ValueError("Reflectance gain must be positive.")
    elevation = np.asarray(_number(metadata, "SUN_ELEVATION") if sun_elevation is None else sun_elevation, dtype=float)
    if elevation.ndim:
        ensure_same_shape(dn=image, sun_elevation=elevation)
    invalid_angle = ~np.isfinite(elevation) | (elevation <= 0) | (elevation > 90)
    if elevation.ndim == 0 and invalid_angle:
        raise ValueError("SUN_ELEVATION must be within (0, 90] degrees.")
    invalid = ~np.isfinite(image) | (image <= 0) | invalid_angle
    if mask is not None:
        invalid |= ensure_boolean_mask(mask, shape=image.shape)
    with np.errstate(divide="ignore", invalid="ignore"):
        reflectance = (gain * image + bias) / np.sin(np.deg2rad(elevation))
    return apply_mask(reflectance, invalid | ~np.isfinite(reflectance))
