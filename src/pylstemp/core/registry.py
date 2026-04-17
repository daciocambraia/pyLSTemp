"""Extensible algorithm registry used across the package."""

from __future__ import annotations

from typing import Generic, TypeVar

from ..exceptions import InvalidMethodRequested
from .metadata import AlgorithmMetadata

T = TypeVar("T")


class AlgorithmRegistry(Generic[T]):
    """Registry that keeps factories and reference metadata together."""

    def __init__(self, family: str):
        self.family = family
        self._factories: dict[str, type[T]] = {}
        self._aliases: dict[str, str] = {}
        self._metadata: dict[str, AlgorithmMetadata] = {}

    def register(
        self,
        key: str,
        factory: type[T],
        *,
        name: str,
        reference: str,
        citation: str,
        aliases: tuple[str, ...] = (),
    ) -> None:
        canonical_key = key.lower()
        self._factories[canonical_key] = factory
        self._metadata[canonical_key] = AlgorithmMetadata(
            key=canonical_key,
            name=name,
            family=self.family,
            reference=reference,
            citation=citation,
            aliases=aliases,
        )
        for alias in aliases:
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

