"""Xiaolei 2014 NBEM emissivity implementation."""

from __future__ import annotations

import numpy as np

from ...metadata import AlgorithmSpec
from ...utils import cavity_effect, fractional_vegetation_cover, rescale_band
from .base import BaseEmissivityAlgorithm


class ComputeEmissivityXiaolei2014(BaseEmissivityAlgorithm):
    """
    Estimate narrow-band emissivity following Yu, Guo and Wu (2014).

    This method uses NDVI classes, fractional vegetation cover, red-band
    reflectance, and a cavity-effect correction to estimate separate Band 10
    and Band 11 emissivities.

    Notes
    -----
    - ``red_band`` is required by this method.
    - The output is appropriate for split-window workflows that require
      emissivity for both thermal bands.
    """

    emissivity_soil_10 = 0.9668
    emissivity_veg_10 = 0.9863
    emissivity_soil_11 = 0.9747
    emissivity_veg_11 = 0.9896

    def _compute_emissivity(self, *, ndvi: np.ndarray, red_band: np.ndarray | None):
        """
        Compute NBEM emissivity for Band 10 and Band 11.

        Parameters
        ----------
        ndvi : ndarray
            NDVI image.
        red_band : ndarray
            Red band image used to estimate bare-soil emissivity.

        Returns
        -------
        tuple of ndarray
            Emissivity arrays for Band 10 and Band 11.

        Raises
        ------
        ValueError
            If ``red_band`` is not provided.
        """
        if red_band is None:
            raise ValueError("red_band must be provided for the 'xiaolei-2014' emissivity method.")

        masks = self._landcover_masks(ndvi)
        red_band_rescaled = rescale_band(red_band)
        fvc = fractional_vegetation_cover(ndvi)

        emissivity_10 = np.full(ndvi.shape, np.nan, dtype=float)
        emissivity_11 = np.full(ndvi.shape, np.nan, dtype=float)

        cavity_10 = cavity_effect(self.emissivity_veg_10, self.emissivity_soil_10, fvc)
        cavity_11 = cavity_effect(self.emissivity_veg_11, self.emissivity_soil_11, fvc)

        emissivity_10[masks["baresoil"]] = 0.973 - (0.047 * red_band_rescaled[masks["baresoil"]])
        emissivity_11[masks["baresoil"]] = 0.984 - (0.026 * red_band_rescaled[masks["baresoil"]])

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

        emissivity_10[masks["vegetation"]] = self.emissivity_veg_10 + cavity_10[masks["vegetation"]]
        emissivity_11[masks["vegetation"]] = self.emissivity_veg_11 + cavity_11[masks["vegetation"]]

        return emissivity_10, emissivity_11


ALGORITHM_SPEC = AlgorithmSpec(
    key="xiaolei-2014",
    factory=ComputeEmissivityXiaolei2014,
    name="Xiaolei 2014 emissivity",
    reference="Yu, Guo and Wu (2014)",
    citation=(
        "Yu, X., Guo, X., and Wu, Z. "
        "Land surface temperature retrieval from Landsat 8 TIRS - comparison between radiative transfer "
        "equation-based method, split window algorithm and single channel method. "
        "Remote Sensing, 2014."
    ),
)
