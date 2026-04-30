"""Gopinadh 2018 emissivity implementation."""

from __future__ import annotations

import numpy as np

from ...metadata import AlgorithmSpec
from ...validation import to_float_array
from .base import BaseEmissivityAlgorithm


class ComputeEmissivityGopinadh2018(BaseEmissivityAlgorithm):
    """
    Estimate Band 10 and Band 11 emissivity using Rongali et al. (2018).

    The method blends soil and vegetation emissivity coefficients according
    to fractional vegetation cover derived from NDVI.

    Notes
    -----
    - This method returns separate emissivity arrays for Band 10 and Band 11.
    - It is suitable for split-window workflows that require both thermal
      emissivity channels.
    """

    emissivity_soil_10 = 0.971
    emissivity_veg_10 = 0.987
    emissivity_soil_11 = 0.977
    emissivity_veg_11 = 0.989
    ndvi_soil = 0.15
    ndvi_vegetation = 0.48

    @classmethod
    def fractional_vegetation_cover(cls, ndvi) -> np.ndarray:
        """
        Compute the linear FVC used by Rongali et al. (2018).

        The study reports NDVIsoil = 0.15 and NDVIvegetation = 0.48 for the
        evaluated Landsat 8 scene. Values outside this interval are clipped to
        keep the linear mixture physically bounded.
        """
        ndvi_array = to_float_array("ndvi", ndvi)
        fvc = (ndvi_array - cls.ndvi_soil) / (cls.ndvi_vegetation - cls.ndvi_soil)
        return np.clip(fvc, 0, 1)

    def _compute_emissivity(self, *, ndvi: np.ndarray, red_band: np.ndarray | None):
        """
        Compute Band 10 and Band 11 emissivity.

        Parameters
        ----------
        ndvi : ndarray
            NDVI image.
        red_band : ndarray or None
            Ignored by this method.

        Returns
        -------
        tuple of ndarray
            Emissivity arrays for Band 10 and Band 11.
        """
        fvc = self.fractional_vegetation_cover(ndvi)
        emissivity_10 = (self.emissivity_soil_10 * (1 - fvc)) + (self.emissivity_veg_10 * fvc)
        emissivity_11 = (self.emissivity_soil_11 * (1 - fvc)) + (self.emissivity_veg_11 * fvc)
        return emissivity_10, emissivity_11


ALGORITHM_SPEC = AlgorithmSpec(
    key="gopinadh-2018",
    factory=ComputeEmissivityGopinadh2018,
    name="Gopinadh 2018 emissivity",
    reference="Rongali et al. (2018)",
    citation=(
        "Rongali, G., et al. "
        "Split-window algorithm for retrieval of land surface temperature using Landsat 8 thermal infrared data. "
        "Journal of Geovisualization and Spatial Analysis, 2018."
    ),
)
