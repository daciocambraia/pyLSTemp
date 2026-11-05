"""Emissivity algorithms discovered from this folder."""

from ...registry import discover_algorithms
from .avdan_2016 import ComputeEmissivityAvdan2016
from .base import BaseEmissivityAlgorithm
from .rongali_2018 import ComputeEmissivityRongali2018

emissivity_registry = discover_algorithms(__name__, "emissivity")
default_algorithms = emissivity_registry.as_mapping()

__all__ = [
    "BaseEmissivityAlgorithm",
    "ComputeEmissivityAvdan2016",
    "ComputeEmissivityRongali2018",
    "default_algorithms",
    "emissivity_registry",
]
