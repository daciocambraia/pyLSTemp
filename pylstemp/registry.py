"""Extensible algorithm registry and module auto-discovery."""

from __future__ import annotations

import importlib
import pkgutil
from typing import Generic, TypeVar

from .exceptions import InvalidMethodRequested
from .metadata import AlgorithmMetadata, AlgorithmSpec

T = TypeVar("T")


class AlgorithmRegistry(Generic[T]):
    """Registry that keeps factories and reference metadata together."""

    def __init__(self, family: str):
        self.family = family
        self._factories: dict[str, type[T]] = {}
        self._aliases: dict[str, str] = {}
        self._metadata: dict[str, AlgorithmMetadata] = {}

    def register(self, spec: AlgorithmSpec) -> None:
        canonical_key = spec.key.lower()
        self._factories[canonical_key] = spec.factory
        self._metadata[canonical_key] = AlgorithmMetadata(
            key=canonical_key,
            name=spec.name,
            family=self.family,
            reference=spec.reference,
            citation=spec.citation,
            aliases=spec.aliases,
        )
        for alias in spec.aliases:
            self._aliases[alias.lower()] = canonical_key

    def resolve_key(self, key: str) -> str:
        lookup_key = key.lower()
        return self._aliases.get(lookup_key, lookup_key)

    def create(self, key: str) -> T:
        canonical_key = self.resolve_key(key)
        if canonical_key not in self._factories:
            raise InvalidMethodRequested(
                f"Requested method '{key}' is not registered. "
                f"Available methods: {sorted(self.available_keys())}"
            )
        return self._factories[canonical_key]()

    def metadata(self, key: str) -> AlgorithmMetadata:
        canonical_key = self.resolve_key(key)
        if canonical_key not in self._metadata:
            raise InvalidMethodRequested(
                f"Requested method '{key}' is not registered. "
                f"Available methods: {sorted(self.available_keys())}"
            )
        return self._metadata[canonical_key]

    def available_keys(self) -> tuple[str, ...]:
        return tuple(self._factories.keys())

    def describe(self) -> dict[str, AlgorithmMetadata]:
        return dict(self._metadata)

    def as_mapping(self) -> dict[str, type[T]]:
        return dict(self._factories)


def discover_algorithms(package_name: str, family: str) -> AlgorithmRegistry:
    """Import every module in a family package and register its declared algorithm."""
    package = importlib.import_module(package_name)
    registry = AlgorithmRegistry(family)

    for module_info in pkgutil.iter_modules(package.__path__):
        if module_info.name.startswith("_") or module_info.name == "base":
            continue
        module = importlib.import_module(f"{package_name}.{module_info.name}")
        spec = getattr(module, "ALGORITHM_SPEC", None)
        if spec is None:
            continue
        registry.register(spec)

    return registry
