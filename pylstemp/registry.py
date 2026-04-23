"""Extensible algorithm registry and module auto-discovery."""

from __future__ import annotations

import importlib
import pkgutil
from typing import Generic, TypeVar

from .exceptions import InvalidMethodRequested
from .metadata import AlgorithmMetadata, AlgorithmSpec

T = TypeVar("T")


class AlgorithmRegistry(Generic[T]):
    """
    Store algorithm factories and citation metadata for one family.

    Parameters
    ----------
    family : str
        Algorithm family name, such as ``spectral_index``, ``emissivity``,
        ``single_window``, or ``split_window``.

    Notes
    -----
    - Keys are normalized to lowercase.
    - Aliases resolve to canonical algorithm keys.
    - Metadata is stored alongside the factory to support documentation and
      catalog generation.
    """

    def __init__(self, family: str):
        """
        Initialize an empty algorithm registry.

        Parameters
        ----------
        family : str
            Algorithm family name associated with registered metadata.
        """
        self.family = family
        self._factories: dict[str, type[T]] = {}
        self._aliases: dict[str, str] = {}
        self._metadata: dict[str, AlgorithmMetadata] = {}

    def register(self, spec: AlgorithmSpec) -> None:
        """
        Register an algorithm specification.

        Parameters
        ----------
        spec : AlgorithmSpec
            Algorithm factory, key, aliases, and citation metadata.
        """
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
        """
        Resolve an alias or canonical key.

        Parameters
        ----------
        key : str
            Requested algorithm key or alias.

        Returns
        -------
        str
            Canonical lowercase algorithm key.
        """
        lookup_key = key.lower()
        return self._aliases.get(lookup_key, lookup_key)

    def create(self, key: str) -> T:
        """
        Instantiate a registered algorithm.

        Parameters
        ----------
        key : str
            Algorithm key or alias.

        Returns
        -------
        object
            New algorithm instance.

        Raises
        ------
        InvalidMethodRequested
            If the requested key is not registered.
        """
        canonical_key = self.resolve_key(key)
        if canonical_key not in self._factories:
            raise InvalidMethodRequested(
                f"Requested method '{key}' is not registered. "
                f"Available methods: {sorted(self.available_keys())}"
            )
        return self._factories[canonical_key]()

    def metadata(self, key: str) -> AlgorithmMetadata:
        """
        Return citation metadata for an algorithm.

        Parameters
        ----------
        key : str
            Algorithm key or alias.

        Returns
        -------
        AlgorithmMetadata
            Metadata for the requested algorithm.

        Raises
        ------
        InvalidMethodRequested
            If the requested key is not registered.
        """
        canonical_key = self.resolve_key(key)
        if canonical_key not in self._metadata:
            raise InvalidMethodRequested(
                f"Requested method '{key}' is not registered. "
                f"Available methods: {sorted(self.available_keys())}"
            )
        return self._metadata[canonical_key]

    def available_keys(self) -> tuple[str, ...]:
        """
        List registered canonical keys.

        Returns
        -------
        tuple of str
            Registered algorithm keys.
        """
        return tuple(self._factories.keys())

    def describe(self) -> dict[str, AlgorithmMetadata]:
        """
        Return all registered metadata.

        Returns
        -------
        dict
            Mapping from canonical key to metadata.
        """
        return dict(self._metadata)

    def as_mapping(self) -> dict[str, type[T]]:
        """
        Return registered factories as a plain mapping.

        Returns
        -------
        dict
            Mapping from canonical key to factory class.
        """
        return dict(self._factories)


def discover_algorithms(package_name: str, family: str) -> AlgorithmRegistry:
    """
    Discover and register algorithms from a package.

    Parameters
    ----------
    package_name : str
        Import path of the algorithm package.
    family : str
        Algorithm family name assigned to discovered metadata.

    Returns
    -------
    AlgorithmRegistry
        Registry populated with every module that declares ``ALGORITHM_SPEC``.

    Notes
    -----
    - Modules named ``base`` or starting with ``_`` are skipped.
    - Discovery imports modules so their ``ALGORITHM_SPEC`` objects can be read.
    """
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
