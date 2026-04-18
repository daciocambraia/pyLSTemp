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
    Radiance terms must be passed explicitly in the function call:
    ``rad_gain_band_x`` and ``rad_bias_band_x``.
    These values are distinct from the sensor constants ``K1`` and ``K2``.
    """

    def compute_band_10(
        self,
        thermal_band,
        sensor: str,
        rad_gain: float,
        rad_bias: float,
        mask=None,
    ) -> np.ndarray:
        constants = get_landsat_thermal_constants(sensor)
        thermal_image = to_float_array("thermal_band", thermal_band)

        validated_mask = None
        if mask is not None:
            validated_mask = ensure_boolean_mask(mask, shape=thermal_image.shape)

        return compute_brightness_temperature(
            thermal_image,
            float(rad_gain),
            float(rad_bias),
            constants.k1_constant_10,
            constants.k2_constant_10,
            mask=validated_mask,
        )

    def compute_band_11(
        self,
        thermal_band,
        sensor: str,
        rad_gain: float,
        rad_bias: float,
        mask=None,
    ) -> np.ndarray:
        constants = get_landsat_thermal_constants(sensor)
        thermal_image = to_float_array("thermal_band", thermal_band)

        validated_mask = None
        if mask is not None:
            validated_mask = ensure_boolean_mask(mask, shape=thermal_image.shape)

        return compute_brightness_temperature(
            thermal_image,
            float(rad_gain),
            float(rad_bias),
            constants.k1_constant_11,
            constants.k2_constant_11,
            mask=validated_mask,
        )

def brightness_temperature_band_10(
    band_10,
    sensor: str,
    rad_gain: float,
    rad_bias: float,
    mask=None,
):
    """Compute brightness temperature for Landsat thermal band 10."""

    return BrightnessTemperatureLandsat().compute_band_10(
        band_10,
        sensor=sensor,
        rad_gain=rad_gain,
        rad_bias=rad_bias,
        mask=mask,
    )


def brightness_temperature_band_11(
    band_11,
    sensor: str,
    rad_gain: float,
    rad_bias: float,
    mask=None,
):
    """Compute brightness temperature for Landsat thermal band 11."""

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
    aliases=("landsat-brightness", "landsat-8-brightness", "landsat-9-brightness", "landsat8-brightness", "landsat9-brightness"),
)
