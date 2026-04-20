"""Avdan 2016 emissivity implementation."""

from __future__ import annotations

import numpy as np

from ...metadata import AlgorithmSpec
from ...utils import fractional_vegetation_cover
from .base import BaseEmissivityAlgorithm


class ComputeEmissivityAvdan2016(BaseEmissivityAlgorithm):
    """Mono-window emissivity from Avdan and Jovanovska (2016)."""

    water_emissivity = 0.991
    soil_emissivity = 0.996
    vegetation_emissivity = 0.973
    roughness_correction = 0.005

    def _compute_emissivity(self, *, ndvi: np.ndarray, red_band: np.ndarray | None):
        emissivity = np.full(ndvi.shape, np.nan, dtype=float)
        fvc = fractional_vegetation_cover(ndvi)

        water = (ndvi >= self.ndvi_min) & (ndvi < 0)
        soil = (ndvi >= 0) & (ndvi < self.baresoil_ndvi_max)
        mixed = (ndvi >= self.baresoil_ndvi_max) & (ndvi <= self.vegetation_ndvi_min)
        vegetation = (ndvi > self.vegetation_ndvi_min) & (ndvi <= self.ndvi_max)

        emissivity[water] = self.water_emissivity
        emissivity[soil] = self.soil_emissivity
        emissivity[mixed] = (
            (self.vegetation_emissivity * fvc[mixed])
            + (self.soil_emissivity * (1 - fvc[mixed]))
            + self.roughness_correction
        )
        emissivity[vegetation] = self.vegetation_emissivity
        return emissivity, emissivity.copy()


ALGORITHM_SPEC = AlgorithmSpec(
    key="avdan-2016",
    factory=ComputeEmissivityAvdan2016,
    name="Avdan 2016 emissivity",
    reference="Avdan and Jovanovska (2016)",
    citation=(
        "Avdan, U., and Jovanovska, G. Algorithm for automated mapping of land "
        "surface temperature using LANDSAT 8 satellite data. Journal of Sensors, 2016."
    ),
)
