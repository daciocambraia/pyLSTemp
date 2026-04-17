"""Vegetation algorithms discovered from this folder."""

from ...registry import discover_algorithms
from .ndvi import NDVIAlgorithm, ndvi

vegetation_registry = discover_algorithms(__name__, "vegetation")
default_algorithms = vegetation_registry.as_mapping()

__all__ = ["NDVIAlgorithm", "ndvi", "default_algorithms", "vegetation_registry"]
