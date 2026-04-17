"""Gopinadh emissivity implementation."""

from __future__ import annotations

import numpy as np

from ..utils import fractional_vegetation_cover
from .base import BaseEmissivityAlgorithm


class ComputeEmissivityGopinadh(BaseEmissivityAlgorithm):
    """Weighted emissivity blend from Rongali et al. (2018)."""

    emissivity_soil_10 = 0.971
    emissivity_veg_10 = 0.987
    emissivity_soil_11 = 0.977
    emissivity_veg_11 = 0.989

    def _compute_emissivity(self, *, ndvi: np.ndarray, red_band: np.ndarray | None):
        fvc = fractional_vegetation_cover(ndvi)

        # This stays intentionally compact because the reference is a direct weighted blend.
        emissivity_10 = (self.emissivity_soil_10 * (1 - fvc)) + (
            self.emissivity_veg_10 * fvc
        )
        emissivity_11 = (self.emissivity_soil_11 * (1 - fvc)) + (
            self.emissivity_veg_11 * fvc
        )
        return emissivity_10, emissivity_11

