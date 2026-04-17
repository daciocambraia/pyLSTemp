"""Xiaolei/NBEM emissivity implementation."""

from __future__ import annotations

import numpy as np

from ..utils import cavity_effect, fractional_vegetation_cover, rescale_band
from .base import BaseEmissivityAlgorithm


class ComputeEmissivityNBEM(BaseEmissivityAlgorithm):
    """NBEM emissivity approach used by the original library."""

    emissivity_soil_10 = 0.9668
    emissivity_veg_10 = 0.9863
    emissivity_soil_11 = 0.9747
    emissivity_veg_11 = 0.9896

    def _compute_emissivity(self, *, ndvi: np.ndarray, red_band: np.ndarray | None):
        if red_band is None:
            raise ValueError("red_band must be provided for the 'xiaolei' emissivity method.")

        masks = self._landcover_masks(ndvi)
        red_band_rescaled = rescale_band(red_band)
        fvc = fractional_vegetation_cover(ndvi)

        emissivity_10 = np.full(ndvi.shape, np.nan, dtype=float)
        emissivity_11 = np.full(ndvi.shape, np.nan, dtype=float)

        cavity_10 = cavity_effect(self.emissivity_veg_10, self.emissivity_soil_10, fvc)
        cavity_11 = cavity_effect(self.emissivity_veg_11, self.emissivity_soil_11, fvc)

        # Bare-soil, mixed, and vegetation branches are kept explicit to make review easier.
        emissivity_10[masks["baresoil"]] = 0.973 - (
            0.047 * red_band_rescaled[masks["baresoil"]]
        )
        emissivity_11[masks["baresoil"]] = 0.984 - (
            0.026 * red_band_rescaled[masks["baresoil"]]
        )

        emissivity_10[masks["mixed"]] = (
            (self.emissivity_veg_10 * fvc[masks["mixed"]])
            + (self.emissivity_soil_10 * (1 - fvc[masks["mixed"]]))
            + cavity_10[masks["mixed"]]
        )
        emissivity_11[masks["mixed"]] = (
            (self.emissivity_veg_11 * fvc[masks["mixed"]])
            + (self.emissivity_soil_11 * (1 - fvc[masks["mixed"]]))
            + cavity_11[masks["mixed"]]
        )

        emissivity_10[masks["vegetation"]] = (
            self.emissivity_veg_10 + cavity_10[masks["vegetation"]]
        )
        emissivity_11[masks["vegetation"]] = (
            self.emissivity_veg_11 + cavity_11[masks["vegetation"]]
        )

        return emissivity_10, emissivity_11

