"""Vegetation family implementation for NDVI."""

from __future__ import annotations

import numpy as np

from ...metadata import AlgorithmSpec
from ...utils import compute_ndvi
from ...validation import ensure_boolean_mask, ensure_same_shape, to_float_array


def ndvi(landsat_band_5, landsat_band_4, mask=None) -> np.ndarray:
    """Compute NDVI using Landsat band 5 (NIR) and band 4 (red)."""
    band_5 = to_float_array("landsat_band_5", landsat_band_5)
    band_4 = to_float_array("landsat_band_4", landsat_band_4)
    ensure_same_shape(landsat_band_5=band_5, landsat_band_4=band_4)

    validated_mask = None
    if mask is not None:
        validated_mask = ensure_boolean_mask(mask, shape=band_5.shape)

    return compute_ndvi(band_5, band_4, mask=validated_mask)


class NDVIAlgorithm:
    """Object wrapper that lets NDVI participate in the shared family discovery."""

    def __call__(self, landsat_band_5, landsat_band_4, mask=None):
        return ndvi(landsat_band_5, landsat_band_4, mask=mask)


ALGORITHM_SPEC = AlgorithmSpec(
    key="ndvi",
    factory=NDVIAlgorithm,
    name="Normalized Difference Vegetation Index",
    reference="Rouse et al. (1974)",
    citation=(
        "Rouse, J. W., Haas, R. H., Schell, J. A., and Deering, D. W. Monitoring "
        "vegetation systems in the Great Plains with ERTS. NASA SP-351, 1974."
    ),
)
