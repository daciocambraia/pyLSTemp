"""Sobrino 1993 split-window temperature algorithm."""

from __future__ import annotations

from ...exceptions import assert_required_keywords_provided
from ...metadata import AlgorithmSpec
from .base import SplitWindowParentLST


class SplitWindowSobrino1993LST(SplitWindowParentLST):
    """Sobrino 1993 split-window LST."""

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

        diff_tb = tb_10 - tb_11
        diff_e = emissivity_10 - emissivity_11
        result = (
            tb_10
            + (1.06 * diff_tb)
            + (0.46 * diff_tb**2)
            + (53 * (1 - emissivity_10))
            - (53 * diff_e)
        )
        return result, mask


ALGORITHM_SPEC = AlgorithmSpec(
    key="sobrino-1993",
    factory=SplitWindowSobrino1993LST,
    name="Sobrino 1993 split-window LST",
    reference="Sobrino et al. (1993)",
    citation=(
        "Sobrino, J. A., Caselles, V., and Coll, C. Theoretical split window "
        "algorithms for determining the actual surface temperature. Il Nuovo "
        "Cimento, 1993."
    ),
)
