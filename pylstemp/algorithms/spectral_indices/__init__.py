"""Spectral index algorithms discovered from this folder."""

from ...registry import discover_algorithms
from .ndvi import NDVIAlgorithm, ndvi

spectral_indices_registry = discover_algorithms(__name__, "spectral_indices")
default_algorithms = spectral_indices_registry.as_mapping()

__all__ = ["NDVIAlgorithm", "ndvi", "default_algorithms", "spectral_indices_registry"]
