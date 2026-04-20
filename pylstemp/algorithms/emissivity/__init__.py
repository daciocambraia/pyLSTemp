"""Emissivity algorithms discovered from this folder."""

from ...registry import discover_algorithms
from .avdan_2016 import ComputeEmissivityAvdan2016
from .base import BaseEmissivityAlgorithm
from .gopinadh_2018 import ComputeEmissivityGopinadh2018
from .xiaolei_2014 import ComputeEmissivityXiaolei2014

emissivity_registry = discover_algorithms(__name__, "emissivity")
default_algorithms = emissivity_registry.as_mapping()

__all__ = [
    "BaseEmissivityAlgorithm",
    "ComputeEmissivityAvdan2016",
    "ComputeEmissivityGopinadh2018",
    "ComputeEmissivityXiaolei2014",
    "default_algorithms",
    "emissivity_registry",
]
