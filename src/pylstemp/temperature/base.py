"""Shared base class for land-surface temperature algorithms."""

from __future__ import annotations

import numpy as np

from ..core.validation import ensure_boolean_mask, ensure_same_shape


class BaseTemperatureAlgorithm:
    """Provide shared validation and post-processing for temperature algorithms."""

    max_earth_temp = 273.15 + 56.7

    def _validate_inputs(self, *, mask, **images) -> np.ndarray:
        ensure_same_shape(mask=mask, **images)
        return ensure_boolean_mask(mask, shape=next(iter(images.values())).shape)

    def _finalize(self, result, *, mask: np.ndarray) -> np.ndarray:
        output = np.asarray(result, dtype=float).copy()
        output[output > self.max_earth_temp] = np.nan
        output[mask] = np.nan
        return output

