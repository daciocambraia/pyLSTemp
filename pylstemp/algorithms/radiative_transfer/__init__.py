"""Radiative-transfer algorithms will live in this folder as they are added."""

from ...registry import discover_algorithms

radiative_transfer_registry = discover_algorithms(__name__, "radiative_transfer")
default_algorithms = radiative_transfer_registry.as_mapping()

__all__ = ["default_algorithms", "radiative_transfer_registry"]
