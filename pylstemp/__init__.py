"""Public package interface for pyLSTemp."""

from .api import (
    brightness_band_10,
    brightness_band_11,
    emissivity_band_10,
    emissivity_band_11,
    list_algorithms,
    spectral_indices,
    single_window,
    split_window,
    water_vapor,
)
from .references import ORIGINAL_LIBRARY_CREDIT

__all__ = [
    "brightness_band_10",
    "brightness_band_11",
    "emissivity_band_10",
    "emissivity_band_11",
    "list_algorithms",
    "spectral_indices",
    "single_window",
    "split_window",
    "water_vapor",
    "ORIGINAL_LIBRARY_CREDIT",
]

__version__ = "1.4.1"
