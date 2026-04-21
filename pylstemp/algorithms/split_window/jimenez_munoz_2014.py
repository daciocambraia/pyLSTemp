"""Jimenez-Munoz 2014 split-window temperature algorithm."""

from __future__ import annotations

import numpy as np

from ...exceptions import assert_required_keywords_provided
from ...metadata import AlgorithmSpec
from ...validation import ensure_same_shape
from .base import SplitWindowParentLST


class SplitWindowJimenezMunoz2014LST(SplitWindowParentLST):
    """Jimenez-Munoz 2014 split-window LST."""

    def _compute_lst(self, **kwargs):
        required_keywords = [
            "emissivity_10",
            "emissivity_11",
            "brightness_temperature_10",
            "brightness_temperature_11",
            "mask",
        ]
        assert_required_keywords_provided(required_keywords, **kwargs)

        water_vapor = kwargs.get("water_vapor")
        if water_vapor is None:
            raise ValueError(
                "'jimenez-munoz-2014' requires water_vapor in g/cm2. "
                "Use water_vapor_wang_2015(...) or provide an external estimate."
            )

        tb_10 = kwargs["brightness_temperature_10"]
        tb_11 = kwargs["brightness_temperature_11"]
        emissivity_10 = kwargs["emissivity_10"]
        emissivity_11 = kwargs["emissivity_11"]
        mask = self._validate_inputs(
            mask=kwargs["mask"],
            brightness_temperature_10=tb_10,
            brightness_temperature_11=tb_11,
            emissivity_10=emissivity_10,
            emissivity_11=emissivity_11,
        )
        cwv = np.asarray(water_vapor, dtype=float)
        if cwv.ndim > 0:
            ensure_same_shape(
                water_vapor=cwv,
                brightness_temperature_10=tb_10,
            )

        mean_e = (emissivity_10 + emissivity_11) / 2
        diff_e = emissivity_10 - emissivity_11
        diff_tb = tb_10 - tb_11

        result = (
            tb_10
            + (1.387 * diff_tb)
            + (0.183 * (diff_tb**2))
            - 0.268
            + ((54.3 - (2.238 * cwv)) * (1 - mean_e))
            + ((-129.2 + (16.4 * cwv)) * diff_e)
        )
        return result, mask


ALGORITHM_SPEC = AlgorithmSpec(
    key="jimenez-munoz-2014",
    factory=SplitWindowJimenezMunoz2014LST,
    name="Jimenez-Munoz 2014 split-window LST",
    reference="Jimenez-Munoz et al. (2014)",
    citation=(
        "Jimenez-Munoz, J.-C., Sobrino, J. A., Skokovic, D., Mattar, C., "
        "and Cristobal, J. Land surface temperature retrieval methods from "
        "Landsat-8 thermal infrared sensor data. IEEE Geoscience and Remote "
        "Sensing Letters, 2014."
    ),
)
