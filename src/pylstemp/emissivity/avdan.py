"""Avdan emissivity implementation."""

from __future__ import annotations

import numpy as np

from .base import BaseEmissivityAlgorithm


class ComputeMonoWindowEmissivity(BaseEmissivityAlgorithm):
    """Mono-window emissivity from Avdan and Jovanovska (2016)."""

    emissivity_soil_10 = 0.97
    emissivity_veg_10 = 0.99

    def _compute_emissivity(self, *, ndvi: np.ndarray, red_band: np.ndarray | None):
        emissivity = np.full(ndvi.shape, np.nan, dtype=float)
        masks = self._landcover_masks(ndvi)

        # The numeric expression is intentionally preserved from the original implementation.
        emissivity[masks["baresoil"]] = self.emissivity_soil_10
        emissivity[masks["vegetation"]] = self.emissivity_veg_10
        emissivity[masks["mixed"]] = (
            0.004 * (((ndvi[masks["mixed"]] - 0.2) / (0.5 - 0.2)) ** 2)
        ) + 0.986
        return emissivity, emissivity.copy()

