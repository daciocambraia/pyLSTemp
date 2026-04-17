"""Thermal algorithms discovered from this folder."""

from ...registry import discover_algorithms
from .brightness import BrightnessTemperatureLandsat, brightness_temperature

thermal_registry = discover_algorithms(__name__, "thermal")
default_algorithms = thermal_registry.as_mapping()

__all__ = [
    "BrightnessTemperatureLandsat",
    "brightness_temperature",
    "default_algorithms",
    "thermal_registry",
]
