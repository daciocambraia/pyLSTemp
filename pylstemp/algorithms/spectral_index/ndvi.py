"""Spectral index implementation for NDVI."""

from __future__ import annotations

import numpy as np

from ...metadata import AlgorithmSpec
from ...utils import compute_ndvi
from ...validation import ensure_boolean_mask, ensure_same_shape, to_float_array


def ndvi(nir, red, mask=None) -> np.ndarray:
    """Compute NDVI from near-infrared and red bands."""
    nir_array = to_float_array("nir", nir)
    red_array = to_float_array("red", red)
    ensure_same_shape(nir=nir_array, red=red_array)

    validated_mask = None
    if mask is not None:
        validated_mask = ensure_boolean_mask(mask, shape=nir_array.shape)

    return compute_ndvi(nir_array, red_array, mask=validated_mask)


class NDVIAlgorithm:
    """Object wrapper that lets NDVI participate in the shared family discovery."""

    def __call__(self, nir, red, mask=None):
        return ndvi(nir=nir, red=red, mask=mask)


ALGORITHM_SPEC = AlgorithmSpec(
    key="ndvi",
    factory=NDVIAlgorithm,
    name="Normalized Difference Vegetation Index",
    reference="Rouse et al. (1974)",
    citation=(
        "Rouse, J. W., Haas, R. H., Schell, J. A., and Deering, D. W."
        "Monitoring vegetation systems in the Great Plains with ERTS."
        "NASA SP-351, 1974."
    ),
)
