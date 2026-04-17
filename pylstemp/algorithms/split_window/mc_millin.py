"""McMillin split-window temperature algorithm."""

from __future__ import annotations

from ...exceptions import assert_required_keywords_provided
from ...metadata import AlgorithmSpec
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


ALGORITHM_SPEC = AlgorithmSpec(
    key="mc-millin",
    factory=SplitWindowMcMillinLST,
    name="McMillin split-window LST",
    reference="McMillin (1975)",
    citation=(
        "McMillin, L. M. Estimation of sea surface temperatures from two infrared "
        "window measurements with different absorption. Journal of Geophysical "
        "Research, 1975."
    ),
    aliases=("mc-clain",),
)
