# Documentation

This folder contains the user-facing documentation for the current modular `pyLSTemp` codebase.

## Suggested reading order

1. [installation.md](installation.md)
2. [usage.md](usage.md)
3. [api-reference.md](api-reference.md)
4. [architecture.md](architecture.md)
5. [extending.md](extending.md)
6. [references.md](references.md)

## Main ideas

- the public API stays small and stable
- the real implementations live in `pylstemp/algorithms/`
- new algorithms are discovered automatically from their family folder
- new families can also be discovered automatically when they expose a family registry
