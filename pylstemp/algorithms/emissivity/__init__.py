"""Emissivity algorithms discovered from this folder."""

from ...registry import discover_algorithms
from .avdan import ComputeMonoWindowEmissivity
from .base import BaseEmissivityAlgorithm
from .gopinadh import ComputeEmissivityGopinadh
from .xiaolei import ComputeEmissivityNBEM

emissivity_registry = discover_algorithms(__name__, "emissivity")
default_algorithms = emissivity_registry.as_mapping()

__all__ = [
    "BaseEmissivityAlgorithm",
    "ComputeEmissivityGopinadh",
    "ComputeEmissivityNBEM",
    "ComputeMonoWindowEmissivity",
    "default_algorithms",
    "emissivity_registry",
]
