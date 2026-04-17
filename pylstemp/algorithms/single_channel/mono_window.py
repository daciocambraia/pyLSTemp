"""Mono-window land-surface temperature algorithm."""

from __future__ import annotations

import numpy as np

from ...exceptions import assert_required_keywords_provided
from ...metadata import AlgorithmSpec
from .base import BaseTemperatureAlgorithm


class MonoWindowLST(BaseTemperatureAlgorithm):
    """Mono-window LST from Avdan and Jovanovska (2016)."""

    def __call__(self, **kwargs) -> np.ndarray:
        required_keywords = ["brightness_temperature_10", "emissivity_10", "mask"]
        assert_required_keywords_provided(required_keywords, **kwargs)

        brightness_temperature_10 = kwargs["brightness_temperature_10"]
        emissivity_10 = kwargs["emissivity_10"]
        mask = self._validate_inputs(
            mask=kwargs["mask"],
            brightness_temperature_10=brightness_temperature_10,
            emissivity_10=emissivity_10,
        )

        result = brightness_temperature_10 / (
            1 + (((0.0000115 * brightness_temperature_10) / 14380) * np.log(emissivity_10))
        )
        return self._finalize(result, mask=mask)


ALGORITHM_SPEC = AlgorithmSpec(
    key="mono-window",
    factory=MonoWindowLST,
    name="Mono-window LST",
    reference="Avdan and Jovanovska (2016)",
    citation=(
        "Avdan, U., and Jovanovska, G. Algorithm for automated mapping of land "
        "surface temperature using LANDSAT 8 satellite data. Journal of Sensors, 2016."
    ),
)
