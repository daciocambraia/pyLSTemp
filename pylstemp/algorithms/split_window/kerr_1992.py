"""Kerr 1992 split-window temperature algorithm."""

from __future__ import annotations

import numpy as np

from ...exceptions import assert_required_keywords_provided
from ...metadata import AlgorithmSpec
from .base import SplitWindowParentLST


class SplitWindowKerr1992LST(SplitWindowParentLST):
    """
    Compute split-window LST following Kerr et al. (1992).

    The method uses Band 10 and Band 11 brightness temperatures and a linear
    NDVI-derived vegetation proportion to interpolate the coefficients
    reported by the article.

    Notes
    -----
    - This implementation follows the article's reported NDVI endmembers:
      bare soil = 0.11 and vegetation = 0.72.
    - The method does not require explicit emissivity inputs.
    - It is retained as a Landsat Band 10/11 adaptation.
    """

    ndvi_bare_soil = 0.11
    ndvi_vegetation = 0.72

    def _compute_lst(self, **kwargs):
        """
        Compute raw Kerr et al. split-window LST.

        Parameters
        ----------
        brightness_temperature_10 : array-like
            Band 10 brightness temperature in Kelvin.
        brightness_temperature_11 : array-like
            Band 11 brightness temperature in Kelvin.
        ndvi : array-like
            NDVI image used to estimate vegetation proportion.
        mask : array-like of bool or None
            Boolean mask where True values indicate invalid pixels.

        Returns
        -------
        tuple
            Raw LST image in Kelvin and validated mask.
        """
        required_keywords = [
            "brightness_temperature_10",
            "brightness_temperature_11",
            "ndvi",
            "mask",
        ]
        assert_required_keywords_provided(required_keywords, **kwargs)

        tb_10 = kwargs["brightness_temperature_10"]
        tb_11 = kwargs["brightness_temperature_11"]
        ndvi = kwargs["ndvi"]
        mask = self._validate_inputs(
            mask=kwargs["mask"],
            brightness_temperature_10=tb_10,
            brightness_temperature_11=tb_11,
            ndvi=ndvi,
        )

        pv = (ndvi - self.ndvi_bare_soil) / (self.ndvi_vegetation - self.ndvi_bare_soil)
        pv = np.clip(pv, 0, 1)
        result = (
            (tb_10 * ((0.5 * pv) + 3.1))
            + (tb_11 * ((-0.5 * pv) - 2.1))
            + (3.1 - (5.5 * pv))
        )
        return result, mask


ALGORITHM_SPEC = AlgorithmSpec(
    key="kerr-1992",
    factory=SplitWindowKerr1992LST,
    name="Kerr 1992 split-window LST",
    reference="Kerr et al. (1992)",
    citation=(
        "Kerr, Y. H., Lagouarde, J. P., Nerry, F., and Ottle, C. A semiempirical "
        "approach to the retrieval of land surface temperature from AVHRR data. "
        "Remote Sensing of Environment, 1992. This implementation interpolates "
        "the bare-soil and vegetation coefficients reported in Table 1 using "
        "the article's linear NDVI cover with NDVIbs=0.11 and NDVIv=0.72, "
        "cited from Begue (1991)."
    ),
)
