"""Jiminez-Munoz split-window temperature algorithm."""

from __future__ import annotations

from ...exceptions import assert_required_keywords_provided
from .base import SplitWindowParentLST


class SplitWindowJiminezMunozLST(SplitWindowParentLST):
    """Jiminez-Munoz split-window LST."""

    cwv = 0.013

    def _compute_lst(self, **kwargs):
        required_keywords = [
            "emissivity_10",
            "emissivity_11",
            "brightness_temperature_10",
            "brightness_temperature_11",
            "mask",
        ]
        assert_required_keywords_provided(required_keywords, **kwargs)

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

        mean_e = (emissivity_10 + emissivity_11) / 2
        diff_e = emissivity_10 - emissivity_11
        diff_tb = tb_10 - tb_11

        result = (
            tb_10
            + (1.387 * diff_tb)
            + (0.183 * (diff_tb**2))
            - 0.268
            + ((54.3 - (2.238 * self.cwv)) * (1 - mean_e))
            + ((-129.2 + (16.4 * self.cwv)) * diff_e)
        )
        return result, mask

