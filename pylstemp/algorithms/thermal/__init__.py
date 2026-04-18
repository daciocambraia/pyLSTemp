"""Thermal algorithms discovered from this folder."""

from ...registry import discover_algorithms
from .brightness import (
    BrightnessTemperatureLandsat,
    brightness_temperature,
    brightness_temperature_band_10,
    brightness_temperature_band_11,
)

thermal_registry = discover_algorithms(__name__, "thermal")
default_algorithms = thermal_registry.as_mapping()

__all__ = [
    "BrightnessTemperatureLandsat",
    "brightness_temperature",
    "brightness_temperature_band_10",
    "brightness_temperature_band_11",
    "default_algorithms",
    "thermal_registry",
]
