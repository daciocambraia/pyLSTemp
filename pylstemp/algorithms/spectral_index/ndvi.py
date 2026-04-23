"""Spectral index implementation for NDVI."""

from __future__ import annotations

import numpy as np

from ...metadata import AlgorithmSpec
from ...utils import compute_ndvi
from ...validation import ensure_boolean_mask, ensure_same_shape, to_float_array


def ndvi(nir, red, mask=None) -> np.ndarray:
    """
    Compute the Normalized Difference Vegetation Index (NDVI).

    Parameters
    ----------
    nir : array-like
        Near-infrared band.
    red : array-like
        Red band.
    mask : array-like of bool, optional
        Boolean mask where True values indicate invalid pixels.

    Returns
    -------
    numpy.ndarray
        NDVI image computed as `(NIR - RED) / (NIR + RED)`.

    Notes
    -----
    - Input arrays must have the same shape and spatial alignment.
    - NDVI values typically range from -1 to 1.
    - Masked pixels are returned as `NaN`.

    Examples
    --------
    >>> from pylstemp import spectral_index
    >>> ndvi_image = spectral_index(index="ndvi", nir=nir, red=red)
    """
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
        """
        Compute NDVI through the registry-compatible algorithm interface.

        Parameters
        ----------
        nir : array-like
            Near-infrared band.
        red : array-like
            Red band.
        mask : array-like of bool, optional
            Boolean mask where True values indicate invalid pixels.

        Returns
        -------
        ndarray
            NDVI image.
        """
        return ndvi(nir=nir, red=red, mask=mask)


ALGORITHM_SPEC = AlgorithmSpec(
    key="ndvi",
    factory=NDVIAlgorithm,
    name="Normalized Difference Vegetation Index",
    reference="Rouse et al. (1974)",
    citation=(
        "Rouse, J. W., Haas, R. H., Schell, J. A., and Deering, D. W. "
        "Monitoring vegetation systems in the Great Plains with ERTS. "
        "NASA SP-351, 1974."
    ),
)
