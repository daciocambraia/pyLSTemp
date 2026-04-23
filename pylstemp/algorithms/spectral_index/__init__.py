"""Spectral index algorithms discovered from this folder."""

from ...registry import discover_algorithms
from .evi import EVIAlgorithm, evi
from .ndvi import NDVIAlgorithm, ndvi

spectral_index_registry = discover_algorithms(__name__, "spectral_index")
default_algorithms = spectral_index_registry.as_mapping()

__all__ = [
    "EVIAlgorithm",
    "NDVIAlgorithm",
    "evi",
    "ndvi",
    "default_algorithms",
    "spectral_index_registry",
]
