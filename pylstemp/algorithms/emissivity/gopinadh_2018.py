"""Gopinadh 2018 emissivity implementation."""

from __future__ import annotations

import numpy as np

from ...metadata import AlgorithmSpec
from ...utils import fractional_vegetation_cover
from .base import BaseEmissivityAlgorithm


class ComputeEmissivityGopinadh2018(BaseEmissivityAlgorithm):
    """Weighted emissivity blend from Rongali et al. (2018)."""

    emissivity_soil_10 = 0.971
    emissivity_veg_10 = 0.987
    emissivity_soil_11 = 0.977
    emissivity_veg_11 = 0.989

    def _compute_emissivity(self, *, ndvi: np.ndarray, red_band: np.ndarray | None):
        fvc = fractional_vegetation_cover(ndvi)
        emissivity_10 = (self.emissivity_soil_10 * (1 - fvc)) + (self.emissivity_veg_10 * fvc)
        emissivity_11 = (self.emissivity_soil_11 * (1 - fvc)) + (self.emissivity_veg_11 * fvc)
        return emissivity_10, emissivity_11


ALGORITHM_SPEC = AlgorithmSpec(
    key="gopinadh-2018",
    factory=ComputeEmissivityGopinadh2018,
    name="Gopinadh 2018 emissivity",
    reference="Rongali et al. (2018)",
    citation=(
        "Rongali, G., et al."
        "Split-window algorithm for retrieval of land surface temperature using Landsat 8 thermal infrared data."
        "Journal of Geovisualization and Spatial Analysis, 2018."
    ),
)
