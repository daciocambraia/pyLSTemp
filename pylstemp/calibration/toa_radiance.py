"""Level-1 DN to TOA spectral radiance."""
import numpy as np
from ..messages import contextual_errors
from ..utils import apply_mask
from ..validation import to_float_array, ensure_boolean_mask
from .metadata import _level1, _number


@contextual_errors
def toa_radiance(dn, *, metadata, band, mask=None):
    """Level-1 DN -> TOA spectral radiance [W m-2 sr-1 um-1], bands 1..11.

    Uses the matching MTL: L = RADIANCE_MULT_BAND_x * DN + RADIANCE_ADD_BAND_x.
    DN <= 0, nonfinite values and mask=True become NaN. No solar correction,
    atmospheric correction, emissivity correction or clipping is performed.


    Quality inputs
    --------------
    Before this calculation, call quality_mask(qa_pixel_path,
    qa_radsat_path, reference_path=...) and pass the aligned boolean result
    combined with input nodata as mask=. True means invalid. QA files are
    not read by this numerical function; mask=None applies no QA screening.
    LandsatScene.calibrated() prepares and returns its QA mask automatically.
    """
    _level1(metadata)
    if isinstance(band, (bool, np.bool_)) or not isinstance(band, (int, np.integer)) or band not in range(1, 12):
        raise ValueError("Radiance band must be an integer from 1 to 11.")
    image = to_float_array("dn", dn)
    gain = _number(metadata, f"RADIANCE_MULT_BAND_{band}")
    bias = _number(metadata, f"RADIANCE_ADD_BAND_{band}")
    if gain <= 0:
        raise ValueError("Radiance gain must be positive.")
    invalid = ~np.isfinite(image) | (image <= 0)
    if mask is not None:
        invalid |= ensure_boolean_mask(mask, shape=image.shape)
    with np.errstate(over="ignore", invalid="ignore"):
        value = gain * image + bias
    return apply_mask(value, invalid | ~np.isfinite(value))
