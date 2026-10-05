"""Legacy namespace alias; not a separately registered algorithm family."""
from ..spectral_index import spectral_index_registry
from .ndvi import NDVIAlgorithm, ndvi

CANONICAL_FAMILY = "spectral_index"
spectral_indices_registry = spectral_index_registry
default_algorithms = {"ndvi": NDVIAlgorithm}
__all__ = ["NDVIAlgorithm", "ndvi", "default_algorithms", "spectral_indices_registry"]
