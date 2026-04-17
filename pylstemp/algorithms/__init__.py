"""Algorithm families grouped by execution strategy."""

from __future__ import annotations

import importlib
import pkgutil

FAMILY_REGISTRIES: dict[str, object] = {}


def _load_family_registries() -> dict[str, object]:
    registries: dict[str, object] = {}

    for module_info in pkgutil.iter_modules(__path__):
        if not module_info.ispkg or module_info.name.startswith("_"):
            continue

        family_name = module_info.name
        module = importlib.import_module(f"{__name__}.{family_name}")
        registry_name = f"{family_name}_registry"
        registry = getattr(module, registry_name, None)
        if registry is None:
            continue

        registries[family_name] = registry
        globals()[registry_name] = registry

    return registries


FAMILY_REGISTRIES = _load_family_registries()

__all__ = ["FAMILY_REGISTRIES"] + [f"{family}_registry" for family in sorted(FAMILY_REGISTRIES)]
