"""Water vapor retrieval algorithms discovered from this folder."""

from ...registry import discover_algorithms
from .wang_2015 import WaterVaporWang2015

water_vapor_registry = discover_algorithms(__name__, "water_vapor")
default_algorithms = water_vapor_registry.as_mapping()

__all__ = [
    "WaterVaporWang2015",
    "default_algorithms",
    "water_vapor_registry",
]
