"""Avdan 2016 mono-window land-surface temperature algorithm."""

from __future__ import annotations

import numpy as np

from ...exceptions import assert_required_keywords_provided
from ...metadata import AlgorithmSpec
from .base import BaseTemperatureAlgorithm


class MonoWindow2016LST(BaseTemperatureAlgorithm):
    """
    Compute Band 10 mono-window LST from Avdan and Jovanovska (2016).

    The method converts precomputed Band 10 brightness temperature and
    Band 10 emissivity into land-surface temperature using the single-channel
    correction equation.

    Notes
    -----
    - This method is designed for Band 10.
    - Brightness temperature must be computed before calling this algorithm.
    - Emissivity should represent Band 10 emissivity.
    """

    wavelength_band_10 = 10.895e-6
    rho = 14380

    def __call__(self, **kwargs) -> np.ndarray:
        """
        Compute mono-window land-surface temperature.

        Parameters
        ----------
        brightness_temperature_10 : array-like
            Precomputed Band 10 brightness temperature in Kelvin.
        emissivity_10 : array-like
            Band 10 land-surface emissivity.
        mask : array-like of bool or None
            Boolean mask where True values indicate invalid pixels.

        Returns
        -------
        ndarray
            Land-surface temperature in Kelvin.
        """
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
