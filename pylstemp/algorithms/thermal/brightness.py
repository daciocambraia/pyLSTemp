"""Brightness temperature calculations for thermal Landsat bands."""

from __future__ import annotations

import numpy as np

from ...metadata import AlgorithmSpec
from ...utils import compute_brightness_temperature
from ...validation import ensure_boolean_mask, ensure_same_shape, to_float_array


class BrightnessTemperatureLandsat:
    """Convert Landsat thermal bands to brightness temperature."""

    mult_factor = 0.0003342
    add_factor = 0.1
    k1_constant_10 = 774.89
    k1_constant_11 = 480.89
    k2_constant_10 = 1321.08
    k2_constant_11 = 1201.14

    def __call__(self, band_10, band_11=None, mask=None) -> tuple[np.ndarray, np.ndarray | None]:
        band_10_image = to_float_array("band_10", band_10)
        band_11_image = None if band_11 is None else to_float_array("band_11", band_11)
        ensure_same_shape(band_10=band_10_image, band_11=band_11_image)

        validated_mask = None
        if mask is not None:
            validated_mask = ensure_boolean_mask(mask, shape=band_10_image.shape)

        brightness_10 = compute_brightness_temperature(
            band_10_image,
            self.mult_factor,
            self.add_factor,
            self.k1_constant_10,
            self.k2_constant_10,
            mask=validated_mask,
        )

        brightness_11 = None
        if band_11_image is not None:
            brightness_11 = compute_brightness_temperature(
                band_11_image,
                self.mult_factor,
                self.add_factor,
                self.k1_constant_11,
                self.k2_constant_11,
                mask=validated_mask,
            )

        return brightness_10, brightness_11


def brightness_temperature(landsat_band_10, landsat_band_11=None, mask=None):
    """Compute brightness temperature for Landsat thermal bands."""
    band_10 = to_float_array("landsat_band_10", landsat_band_10)
    band_11 = None if landsat_band_11 is None else to_float_array("landsat_band_11", landsat_band_11)
    ensure_same_shape(landsat_band_10=band_10, landsat_band_11=band_11)

    validated_mask = None
    if mask is not None:
        validated_mask = ensure_boolean_mask(mask, shape=band_10.shape)

    return BrightnessTemperatureLandsat()(band_10, band_11, mask=validated_mask)

ALGORITHM_SPEC = AlgorithmSpec(
    key="landsat-brightness",
    factory=BrightnessTemperatureLandsat,
    name="Landsat brightness temperature",
    reference="Landsat 8 TIRS calibration constants",
    citation=(
        "Brightness temperature conversion using the published multiplicative, "
        "additive, K1, and K2 calibration constants preserved from the original library."
    ),
)
