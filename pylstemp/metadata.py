"""Immutable metadata records for discovered algorithms."""

from dataclasses import dataclass


@dataclass(frozen=True)
class AlgorithmMetadata:
    """
    Immutable metadata record for a registered algorithm.

    Attributes
    ----------
    key : str
        Canonical algorithm key.
    name : str
        Human-readable algorithm name.
    family : str
        Algorithm family name.
    reference : str
        Short reference label.
    citation : str
        Full citation text.
    aliases : tuple of str
        Alternative keys accepted by the registry.
    """

    key: str
    name: str
    family: str
    reference: str
    citation: str
    aliases: tuple[str, ...] = ()


@dataclass(frozen=True)
class AlgorithmSpec:
    """
    Module-level algorithm declaration used by registry discovery.

    Attributes
    ----------
    key : str
        Canonical algorithm key.
    factory : type
        Algorithm class or callable factory.
    name : str
        Human-readable algorithm name.
    reference : str
        Short reference label.
    citation : str
        Full citation text.
    aliases : tuple of str
        Alternative keys accepted by the registry.
    """

    key: str
    factory: type
    name: str
    reference: str
    citation: str
    aliases: tuple[str, ...] = ()
