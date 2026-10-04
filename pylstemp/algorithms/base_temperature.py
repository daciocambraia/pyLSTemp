"""Shared base class for land-surface temperature algorithms."""

from __future__ import annotations

import numpy as np

from ..validation import ensure_boolean_mask, ensure_same_shape


class BaseTemperatureAlgorithm:
    """
    Base class for land-surface temperature algorithms.

    This class provides shared input validation and output post-processing
    for single-channel and split-window LST methods.

    Notes
    -----
    - All image inputs must have the same shape and spatial alignment.
    - Nonfinite and nonpositive absolute temperatures are invalid.
    - No arbitrary upper surface-temperature cutoff is applied.
    - User masks are applied after the temperature calculation.
    """

    # No global air-temperature cutoff is applicable to surface temperature.

    def _validate_inputs(self, *, mask, **images) -> np.ndarray:
        """
        Validate image shapes and normalize the mask.

        Parameters
        ----------
        mask : array-like of bool or None
            Boolean mask where True values indicate invalid pixels.
        **images : ndarray
            Input image arrays used by the algorithm.

        Returns
        -------
        ndarray
            Boolean mask with the same shape as the input images.
        """
        ensure_same_shape(mask=mask, **images)
        shape = next(iter(images.values())).shape
        invalid = np.zeros(shape, dtype=bool) if mask is None else ensure_boolean_mask(mask, shape=shape).copy()
        for name, image in images.items():
            invalid |= ~np.isfinite(image)
            if name.startswith("brightness_temperature"):
                invalid |= image <= 0
            if name.startswith("emissivity"):
                invalid |= (image <= 0) | (image > 1)
        return invalid

    def _finalize(self, result, *, mask: np.ndarray) -> np.ndarray:
        """
        Apply physical filtering and user mask to an LST result.

        Parameters
        ----------
        result : array-like
            Computed LST image in Kelvin.
        mask : ndarray of bool
            Validated mask where True values indicate invalid pixels.

        Returns
        -------
        ndarray
            Final LST image with invalid pixels set to NaN.
        """
        output = np.asarray(result, dtype=float).copy()
        output[~np.isfinite(output) | (output <= 0)] = np.nan
        output[mask] = np.nan
        return output
