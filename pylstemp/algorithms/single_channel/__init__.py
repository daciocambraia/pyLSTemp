"""Single-channel temperature algorithms discovered from this folder."""

from ...registry import discover_algorithms
from ..base_temperature import BaseTemperatureAlgorithm
from ..thermal import BrightnessTemperatureLandsat, brightness_band_10
from .mono_window_2016 import MonoWindow2016LST
from .jimenez_munoz_2014 import SingleChannelJimenezMunoz2014LST

single_channel_registry = discover_algorithms(__name__, "single_channel")
default_algorithms = single_channel_registry.as_mapping()

__all__ = [
    "BrightnessTemperatureLandsat",
    "brightness_band_10",
    "BaseTemperatureAlgorithm",
    "MonoWindow2016LST",
    "SingleChannelJimenezMunoz2014LST",
    "default_algorithms",
    "single_channel_registry",
]
