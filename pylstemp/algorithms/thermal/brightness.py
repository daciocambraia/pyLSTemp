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

    def __call__(
        self,
        band_10,
        sensor: str,
        rad_gain_band_10: float,
        rad_bias_band_10: float,
        band_11=None,
        rad_gain_band_11: float | None = None,
        rad_bias_band_11: float | None = None,
        mask=None,
    ) -> tuple[np.ndarray, np.ndarray | None]:
        band_10_image = to_float_array("band_10", band_10)
        band_11_image = None if band_11 is None else to_float_array("band_11", band_11)
        ensure_same_shape(band_10=band_10_image, band_11=band_11_image)

        brightness_10 = self.compute_band_10(
            band_10_image,
            sensor=sensor,
            rad_gain=rad_gain_band_10,
            rad_bias=rad_bias_band_10,
            mask=mask,
        )

        brightness_11 = None
        if band_11_image is not None:
            if rad_gain_band_11 is None or rad_bias_band_11 is None:
                raise ValueError(
                    "band_11 requires explicit rad_gain_band_11 and rad_bias_band_11 "
                    "passed in the function call."
                )
            brightness_11 = self.compute_band_11(
                band_11_image,
                sensor=sensor,
                rad_gain=rad_gain_band_11,
                rad_bias=rad_bias_band_11,
                mask=mask,
            )

        return brightness_10, brightness_11


def brightness_temperature_band_10(
    thermal_band,
    sensor: str,
    rad_gain: float,
    rad_bias: float,
    mask=None,
):
    """Compute brightness temperature for Landsat thermal band 10."""

    return BrightnessTemperatureLandsat().compute_band_10(
        thermal_band,
        sensor=sensor,
        rad_gain=rad_gain,
        rad_bias=rad_bias,
        mask=mask,
    )


def brightness_temperature_band_11(
    thermal_band,
    sensor: str,
    rad_gain: float,
    rad_bias: float,
    mask=None,
):
    """Compute brightness temperature for Landsat thermal band 11."""

    return BrightnessTemperatureLandsat().compute_band_11(
        thermal_band,
        sensor=sensor,
        rad_gain=rad_gain,
        rad_bias=rad_bias,
        mask=mask,
    )


def brightness_temperature(
    landsat_band_10,
    sensor: str,
    rad_gain_band_10: float,
    rad_bias_band_10: float,
    landsat_band_11=None,
    rad_gain_band_11: float | None = None,
    rad_bias_band_11: float | None = None,
    mask=None,
):
    """Compute brightness temperature for Landsat 8 or Landsat 9.

    ``sensor`` must be ``"landsat_8"`` or ``"landsat_9"``.
    ``rad_gain_band_10`` and ``rad_bias_band_10`` must be informed explicitly
    in the function call for band 10.
    ``rad_gain_band_11`` and ``rad_bias_band_11`` must be informed explicitly
    in the function call for band 11.
    These radiance terms are different from the sensor constants ``K1`` and ``K2``.
    """

    band_10 = to_float_array("landsat_band_10", landsat_band_10)
    band_11 = None if landsat_band_11 is None else to_float_array("landsat_band_11", landsat_band_11)
    ensure_same_shape(landsat_band_10=band_10, landsat_band_11=band_11)

    validated_mask = None
    if mask is not None:
        validated_mask = ensure_boolean_mask(mask, shape=band_10.shape)

    return BrightnessTemperatureLandsat()(
        band_10,
        sensor=sensor,
        rad_gain_band_10=rad_gain_band_10,
        rad_bias_band_10=rad_bias_band_10,
        band_11=band_11,
        rad_gain_band_11=rad_gain_band_11,
        rad_bias_band_11=rad_bias_band_11,
        mask=validated_mask,
    )


ALGORITHM_SPEC = AlgorithmSpec(
    key="landsat-brightness",
    factory=BrightnessTemperatureLandsat,
    name="Landsat brightness temperature",
    reference="Landsat 8 and Landsat 9 thermal calibration constants",
    citation=(
        "Brightness temperature conversion using sensor-specific Landsat K1 and K2 constants "
        "with explicit per-band radiance gain and bias inputs."
    ),
    aliases=("landsat-8-brightness", "landsat-9-brightness", "landsat8-brightness", "landsat9-brightness"),
)
