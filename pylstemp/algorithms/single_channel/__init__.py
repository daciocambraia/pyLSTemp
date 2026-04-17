"""Single-channel temperature algorithms discovered from this folder."""

from ...registry import discover_algorithms
from ..base_temperature import BaseTemperatureAlgorithm
from ..thermal import BrightnessTemperatureLandsat, brightness_temperature
from .mono_window import MonoWindowLST

single_channel_registry = discover_algorithms(__name__, "single_channel")
default_algorithms = single_channel_registry.as_mapping()

__all__ = [
    "BrightnessTemperatureLandsat",
    "brightness_temperature",
    "BaseTemperatureAlgorithm",
    "MonoWindowLST",
    "default_algorithms",
    "single_channel_registry",
]
