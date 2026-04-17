"""Kerr split-window temperature algorithm."""

from __future__ import annotations

from ...exceptions import assert_required_keywords_provided
from ...utils import fractional_vegetation_cover
from .base import SplitWindowParentLST


class SplitWindowKerrLST(SplitWindowParentLST):
    """Kerr split-window LST."""

    def _compute_lst(self, **kwargs):
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

        pv = fractional_vegetation_cover(ndvi)
        result = (
            (tb_10 * ((0.5 * pv) + 3.1))
            + (tb_11 * ((-0.5 * pv) - 2.1))
            - ((5.5 * pv) + 3.1)
        )
        return result, mask

