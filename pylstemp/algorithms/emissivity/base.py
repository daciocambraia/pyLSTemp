"""Shared base class for emissivity algorithms."""

from __future__ import annotations

import numpy as np

from ...validation import ensure_same_shape, to_float_array


class BaseEmissivityAlgorithm:
    """
    Base class for emissivity algorithms.

    This class centralizes input validation, shape checks, NaN propagation,
    and shared NDVI land-cover masks used by the emissivity methods.

    Notes
    -----
    - Subclasses must implement ``_compute_emissivity``.
    - Returned emissivity arrays are masked where the NDVI input is NaN.
    - The class expects NDVI values in the physical range from -1 to 1.
    """

    ndvi_min = -1.0
    ndvi_max = 1.0
    baresoil_ndvi_max = 0.2
    vegetation_ndvi_min = 0.5

    def __call__(self, *, ndvi, red_band=None) -> tuple[np.ndarray, np.ndarray | None]:
        """
        Validate inputs and compute thermal emissivity.

        Parameters
        ----------
        ndvi : array-like
            NDVI image used to estimate land-cover fraction.
        red_band : array-like, optional
            Red band image. Required only by methods that explicitly use
            reflectance information, such as ``xiaolei-2014``.

        Returns
        -------
        tuple of ndarray
            Emissivity for Band 10 and, when available, emissivity for Band 11.

        Notes
        -----
        - Input arrays must have the same shape and spatial alignment.
        - NaN pixels in ``ndvi`` are propagated to the output emissivity arrays.
        """
        ndvi_image = to_float_array("ndvi", ndvi)
        red_band_image = None if red_band is None else to_float_array("red_band", red_band)
        ensure_same_shape(ndvi=ndvi_image, red_band=red_band_image)

        emissivity_10, emissivity_11 = self._compute_emissivity(
            ndvi=ndvi_image,
            red_band=red_band_image,
        )

        invalid_mask = np.isnan(ndvi_image)
        emissivity_10 = np.asarray(emissivity_10, dtype=float)
        emissivity_10[invalid_mask] = np.nan

        if emissivity_11 is not None:
            emissivity_11 = np.asarray(emissivity_11, dtype=float)
            emissivity_11[invalid_mask] = np.nan

        return emissivity_10, emissivity_11

    def _compute_emissivity(self, *, ndvi: np.ndarray, red_band: np.ndarray | None):
        """
        Compute emissivity for a concrete method.

        Parameters
        ----------
        ndvi : ndarray
            Validated NDVI image.
        red_band : ndarray or None
            Optional validated red band image.

        Returns
        -------
        tuple of ndarray
            Emissivity arrays for Band 10 and optionally Band 11.
        """
        raise NotImplementedError

    def _landcover_masks(self, ndvi: np.ndarray) -> dict[str, np.ndarray]:
        """
        Build standard NDVI masks for bare soil, mixed cover, and vegetation.

        Parameters
        ----------
        ndvi : ndarray
            NDVI image.

        Returns
        -------
        dict of ndarray
            Boolean masks keyed by land-cover class.
        """
        return {
            "baresoil": (ndvi >= self.ndvi_min) & (ndvi < self.baresoil_ndvi_max),
            "mixed": (ndvi >= self.baresoil_ndvi_max) & (ndvi <= self.vegetation_ndvi_min),
            "vegetation": (ndvi > self.vegetation_ndvi_min) & (ndvi <= self.ndvi_max),
        }
