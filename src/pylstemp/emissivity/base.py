"""Shared base class for emissivity algorithms."""

from __future__ import annotations

import numpy as np

from ..core.validation import ensure_same_shape, to_float_array


class BaseEmissivityAlgorithm:
    """Common validation and masking logic for emissivity methods.

    Keeping this in its own module makes future emissivity objects easier to add
    without touching sibling algorithm files.
    """

    ndvi_min = -1.0
    ndvi_max = 1.0
    baresoil_ndvi_max = 0.2
    vegetation_ndvi_min = 0.5

    def __call__(self, *, ndvi, red_band=None) -> tuple[np.ndarray, np.ndarray | None]:
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
        raise NotImplementedError

    def _landcover_masks(self, ndvi: np.ndarray) -> dict[str, np.ndarray]:
        """Split NDVI into bare soil, mixed pixels and vegetation masks."""
        return {
            "baresoil": (ndvi >= self.ndvi_min) & (ndvi < self.baresoil_ndvi_max),
            "mixed": (ndvi >= self.baresoil_ndvi_max) & (ndvi <= self.vegetation_ndvi_min),
            "vegetation": (ndvi > self.vegetation_ndvi_min) & (ndvi <= self.ndvi_max),
        }

