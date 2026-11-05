"""Scale existing Collection-2 Level-2 surface reflectance products."""
import numpy as np
from ..messages import contextual_errors
from ..utils import apply_mask
from ..validation import to_float_array, ensure_boolean_mask


@contextual_errors
def surface_reflectance(dn, *, scale=0.0000275, offset=-0.2, mask=None):
    """Scale C2 Level-2 SR_B* DN to surface reflectance; no sun correction.

    This does not perform atmospheric correction on Level-1 DN.
    """
    image = to_float_array("dn", dn)
    if not np.isfinite(scale) or scale <= 0 or not np.isfinite(offset):
        raise ValueError("SR scaling must be finite, with positive scale.")
    invalid = ~np.isfinite(image) | (image <= 0)
    if mask is not None:
        invalid |= ensure_boolean_mask(mask, shape=image.shape)
    return apply_mask(image * scale + offset, invalid)
