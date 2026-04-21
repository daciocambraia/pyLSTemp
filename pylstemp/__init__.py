"""Public package interface for pyLSTemp."""

from .api import (
    brightness_band_10,
    brightness_band_11,
    emissivity_band_10,
    emissivity_band_11,
    list_algorithms,
    ndvi,
    single_window,
    split_window,
    water_vapor_wang_2015,
)
from .references import ORIGINAL_LIBRARY_CREDIT

__all__ = [
    "brightness_band_10",
    "brightness_band_11",
    "emissivity_band_10",
    "emissivity_band_11",
    "list_algorithms",
    "ndvi",
    "single_window",
    "split_window",
    "water_vapor_wang_2015",
    "ORIGINAL_LIBRARY_CREDIT",
]

__version__ = "1.3.0"
