"""Avdan 2016 mono-window land-surface temperature algorithm."""

from __future__ import annotations

import numpy as np

from ...exceptions import assert_required_keywords_provided
from ...metadata import AlgorithmSpec
from .base import BaseTemperatureAlgorithm


class MonoWindow2016LST(BaseTemperatureAlgorithm):
    """Band 10 mono-window LST from Avdan and Jovanovska (2016)."""

    wavelength_band_10 = 10.895e-6
    rho = 14380

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
            1 + (((self.wavelength_band_10 * brightness_temperature_10) / self.rho) * np.log(emissivity_10))
        )
        return self._finalize(result, mask=mask)


ALGORITHM_SPEC = AlgorithmSpec(
    key="mono-window-2016",
    factory=MonoWindow2016LST,
    name="Mono-window 2016 LST",
    reference="Avdan and Jovanovska (2016)",
    citation=(
        "Avdan, U., and Jovanovska, G. Algorithm for automated mapping of land "
        "surface temperature using LANDSAT 8 satellite data. Journal of Sensors, 2016."
    ),
)
