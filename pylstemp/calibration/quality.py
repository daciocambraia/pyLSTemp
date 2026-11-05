"""Decode Collection-2 Landsat QA arrays before calibration."""
import numpy as np
from ..messages import contextual_errors
from ..validation import ensure_same_shape, ensure_bool


@contextual_errors
def _quality_mask_from_arrays(qa_pixel, qa_radsat=None, *, exclude_water=False):
    """C2 Landsat 8/9 mask: fill, dilated cloud, cirrus, cloud, shadow, snow.

    QA_RADSAT excludes saturation in B2/B4/B5 and terrain occlusion.
    Thermal saturation is not encoded in these QA_RADSAT optical bits.
    Water is preserved unless exclude_water=True (use True for Wang over land).
    """
    exclude_water = ensure_bool("exclude_water", exclude_water)
    qa = np.asarray(qa_pixel)
    if not np.issubdtype(qa.dtype, np.integer) or np.any(qa < 0) or np.any(qa > 65535):
        raise ValueError("QA_PIXEL must contain unsigned 16-bit integer values.")
    bits = 0b111111 | ((1 << 7) if exclude_water else 0)
    invalid = (qa.astype(np.uint16) & bits) != 0
    if qa_radsat is not None:
        sat = np.asarray(qa_radsat)
        ensure_same_shape(qa_pixel=qa, qa_radsat=sat)
        if not np.issubdtype(sat.dtype, np.integer) or np.any(sat < 0) or np.any(sat > 65535):
            raise ValueError("QA_RADSAT must contain unsigned 16-bit integer values.")
        invalid |= (sat.astype(np.uint16) & ((1 << 1) | (1 << 3) | (1 << 4) | (1 << 11))) != 0
    return invalid
