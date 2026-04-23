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
    """
    Compute the Enhanced Vegetation Index (EVI).

    The source article names this formulation SARVI2. pyLSTemp exposes it as
    EVI because the implemented coefficients match the common EVI structure.

    Parameters
    ----------
    nir : array-like
        Near-infrared band.
    red : array-like
        Red band.
    blue : array-like
        Blue band.
    mask : array-like of bool, optional
        Boolean mask where True values indicate invalid pixels.

    Returns
    -------
    numpy.ndarray
        EVI image computed as
        `2.5 * ((NIR - RED) / (NIR + 6 * RED - 7.5 * BLUE + 1))`.

    Notes
    -----
    - Input arrays must have the same shape and spatial alignment.
    - Use reflectance-like optical bands for physically meaningful values.
    - Masked pixels are returned as `NaN`.

    Examples
    --------
    >>> from pylstemp import spectral_index
    >>> evi_image = spectral_index(index="evi", nir=nir, red=red, blue=blue)
    """
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
        """
        Compute EVI through the registry-compatible algorithm interface.

        Parameters
        ----------
        nir : array-like
            Near-infrared band.
        red : array-like
            Red band.
        blue : array-like
            Blue band.
        mask : array-like of bool, optional
            Boolean mask where True values indicate invalid pixels.

        Returns
        -------
        ndarray
            EVI image.
        """
        return evi(nir=nir, red=red, blue=blue, mask=mask)


ALGORITHM_SPEC = AlgorithmSpec(
    key="evi",
    factory=EVIAlgorithm,
    name="Enhanced Vegetation Index",
    reference="Huete et al. (1997)",
    citation=(
        "Huete, A. R., Liu, H. Q., Batchily, K., and van Leeuwen, W. "
        "A comparison of vegetation indices over a global set of TM images for EOS-MODIS. "
        "Remote Sensing of Environment, 1997."
    ),
)
