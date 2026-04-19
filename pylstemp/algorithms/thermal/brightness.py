"""Brightness temperature calculations for Landsat 8 and Landsat 9 thermal bands."""

from __future__ import annotations

import numpy as np

from ...metadata import AlgorithmSpec
from ...sensors import get_landsat_thermal_constants
from ...utils import compute_brightness_temperature
from ...validation import ensure_boolean_mask, ensure_same_shape, to_float_array


class BrightnessTemperatureLandsat:
    """Convert Landsat 8 or Landsat 9 thermal bands to brightness temperature.

    The ``sensor`` argument must be either ``"landsat_8"`` or ``"landsat_9"``.
    Default radiance gain and bias values are loaded from the selected sensor metadata.
    The user may override them in the function call if needed.
    These radiance values are distinct from the sensor constants ``K1`` and ``K2``.
    """

    def compute_band_10(
        self,
        thermal_band,
        sensor: str,
        rad_gain: float | None = None,
        rad_bias: float | None = None,
        mask=None,
    ) -> np.ndarray:
        constants = get_landsat_thermal_constants(sensor)
        thermal_image = to_float_array("thermal_band", thermal_band)

        validated_mask = None
        if mask is not None:
            validated_mask = ensure_boolean_mask(mask, shape=thermal_image.shape)

        effective_rad_gain = constants.radiance_mult_band_10 if rad_gain is None else float(rad_gain)
        effective_rad_bias = constants.radiance_add_band_10 if rad_bias is None else float(rad_bias)

        return compute_brightness_temperature(
            thermal_image,
            effective_rad_gain,
            effective_rad_bias,
            constants.k1_constant_10,
            constants.k2_constant_10,
            mask=validated_mask,
        )

    def compute_band_11(
        self,
        thermal_band,
        sensor: str,
        rad_gain: float | None = None,
        rad_bias: float | None = None,
        mask=None,
    ) -> np.ndarray:
        constants = get_landsat_thermal_constants(sensor)
        thermal_image = to_float_array("thermal_band", thermal_band)

        validated_mask = None
        if mask is not None:
            validated_mask = ensure_boolean_mask(mask, shape=thermal_image.shape)

        effective_rad_gain = constants.radiance_mult_band_11 if rad_gain is None else float(rad_gain)
        effective_rad_bias = constants.radiance_add_band_11 if rad_bias is None else float(rad_bias)

        return compute_brightness_temperature(
            thermal_image,
            effective_rad_gain,
            effective_rad_bias,
            constants.k1_constant_11,
            constants.k2_constant_11,
            mask=validated_mask,
        )

def brightness_band_10(
    band_10,
    sensor: str,
    rad_gain: float | None = None,
    rad_bias: float | None = None,
    mask=None,
):
    """Compute brightness temperature for Landsat thermal band 10.

    Default values:
    - ``landsat_8``: ``rad_gain=0.0003342``, ``rad_bias=0.1``
    - ``landsat_9``: ``rad_gain=0.00038``, ``rad_bias=0.1``

    Pass ``rad_gain`` and ``rad_bias`` explicitly to override the sensor defaults.
    """

    return BrightnessTemperatureLandsat().compute_band_10(
        band_10,
        sensor=sensor,
        rad_gain=rad_gain,
        rad_bias=rad_bias,
        mask=mask,
    )


def brightness_band_11(
    band_11,
    sensor: str,
    rad_gain: float | None = None,
    rad_bias: float | None = None,
    mask=None,
):
    """Compute brightness temperature for Landsat thermal band 11.

    Default values:
    - ``landsat_8``: ``rad_gain=0.0003342``, ``rad_bias=0.1``
    - ``landsat_9``: ``rad_gain=0.000349``, ``rad_bias=0.1``

    Pass ``rad_gain`` and ``rad_bias`` explicitly to override the sensor defaults.
    """

    return BrightnessTemperatureLandsat().compute_band_11(
        band_11,
        sensor=sensor,
        rad_gain=rad_gain,
        rad_bias=rad_bias,
        mask=mask,
    )


ALGORITHM_SPEC = AlgorithmSpec(
    key="brightness",
    factory=BrightnessTemperatureLandsat,
    name="Brightness temperature",
    reference="Landsat 8 and Landsat 9 thermal calibration constants",
    citation=(
        "Brightness temperature conversion using sensor-specific Landsat K1 and K2 constants "
        "with explicit per-band radiance gain and bias inputs."
    ),
    aliases=(),
)
