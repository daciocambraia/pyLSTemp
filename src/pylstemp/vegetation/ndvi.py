"""NDVI calculation entry points.

This module gives vegetation-related calculations their own home so the package
structure reads more naturally as it grows.
"""

from __future__ import annotations

import numpy as np

from ..core.validation import ensure_boolean_mask, ensure_same_shape, to_float_array
from ..utils import compute_ndvi


def ndvi(landsat_band_5, landsat_band_4, mask=None) -> np.ndarray:
    """Compute NDVI using Landsat band 5 (NIR) and band 4 (red).

    Keeping NDVI in a dedicated vegetation module makes future additions like
    SAVI, EVI, or vegetation masks much easier to organize.
    """

    band_5 = to_float_array("landsat_band_5", landsat_band_5)
    band_4 = to_float_array("landsat_band_4", landsat_band_4)
    ensure_same_shape(landsat_band_5=band_5, landsat_band_4=band_4)

    validated_mask = None
    if mask is not None:
        validated_mask = ensure_boolean_mask(mask, shape=band_5.shape)

    return compute_ndvi(band_5, band_4, mask=validated_mask)

