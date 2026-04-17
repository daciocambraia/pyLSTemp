"""Immutable metadata records for discovered algorithms."""

from dataclasses import dataclass


@dataclass(frozen=True)
class AlgorithmMetadata:
    """Small immutable record used to document registered algorithms."""

    key: str
    name: str
    family: str
    reference: str
    citation: str
    aliases: tuple[str, ...] = ()


@dataclass(frozen=True)
class AlgorithmSpec:
    """Module-level declaration consumed by the registry auto-discovery."""

    key: str
    factory: type
    name: str
    reference: str
    citation: str
    aliases: tuple[str, ...] = ()
