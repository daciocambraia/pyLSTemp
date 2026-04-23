"""Spectral index implementation for EVI.

The source article names this formulation SARVI2. The public API exposes it as
EVI because the coefficients match the widely used enhanced vegetation index
formulation.
"""

from __future__ import annotations

import numpy as np

from ...metadata import AlgorithmSpec
from ...utils import apply_mask
from ...validation import ensure_boolean_mask, ensure_same_shape, to_float_array


def evi(nir, red, blue, mask=None) -> np.ndarray:
    """Compute EVI from near-infrared, red, and blue reflectance bands."""
    nir_array = to_float_array("nir", nir)
    red_array = to_float_array("red", red)
    blue_array = to_float_array("blue", blue)
    ensure_same_shape(nir=nir_array, red=red_array, blue=blue_array)

    validated_mask = None
    if mask is not None:
        validated_mask = ensure_boolean_mask(mask, shape=nir_array.shape)

    with np.errstate(divide="ignore", invalid="ignore"):
        output = 2.5 * (
            (nir_array - red_array)
            / (nir_array + (6.0 * red_array) - (7.5 * blue_array) + 1.0)
        )
    output[np.abs(output) > 1] = np.nan
    return apply_mask(output, validated_mask)


class EVIAlgorithm:
    """Object wrapper that lets EVI participate in shared family discovery."""

    def __call__(self, nir, red, blue, mask=None):
        return evi(nir=nir, red=red, blue=blue, mask=mask)


ALGORITHM_SPEC = AlgorithmSpec(
    key="evi",
    factory=EVIAlgorithm,
    name="Enhanced Vegetation Index",
    reference="Huete et al. (1997)",
    citation=(
        "Huete, A. R., Liu, H. Q., Batchily, K., and van Leeuwen, W. "
        "A comparison of vegetation indices over a global set of TM images for EOS-MODIS."
        "Remote Sensing of Environment, 1997."
    ),
)
