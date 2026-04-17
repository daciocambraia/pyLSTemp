"""McMillin split-window temperature algorithm."""

from __future__ import annotations

from ...exceptions import assert_required_keywords_provided
from .base import SplitWindowParentLST


class SplitWindowMcMillinLST(SplitWindowParentLST):
    """McMillin split-window LST."""

    def _compute_lst(self, **kwargs):
        required_keywords = [
            "brightness_temperature_10",
            "brightness_temperature_11",
            "mask",
        ]
        assert_required_keywords_provided(required_keywords, **kwargs)

        tb_10 = kwargs["brightness_temperature_10"]
        tb_11 = kwargs["brightness_temperature_11"]
        mask = self._validate_inputs(
            mask=kwargs["mask"],
            brightness_temperature_10=tb_10,
            brightness_temperature_11=tb_11,
        )

        result = (1.035 * tb_10) + (3.046 * (tb_10 - tb_11)) - 10.93
        return result, mask

