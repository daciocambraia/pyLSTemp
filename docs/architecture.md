# Architecture

## Overview

The codebase is split into a small public layer and a modular algorithm layer.

```text
pylstemp/
  api.py
  registry.py
  validation.py
  utils.py
  algorithms/
    emissivity/
    single_channel/
    split_window/
    thermal/
    vegetation/
    radiative_transfer/
```

## Design principles

- one file should ideally have one main responsibility
- the public API should stay stable even if the internal algorithm set grows
- adding a method should not require editing a central registry by hand
- adding a family should not require editing a central list in the API

## Two discovery layers

### Method discovery inside a family

Each family package calls `discover_algorithms(...)` from `pylstemp/registry.py`.

Each algorithm module exposes:

- its implementation class
- one module-level `ALGORITHM_SPEC`

The registry loads those modules and registers them automatically.

### Family discovery

`pylstemp/algorithms/__init__.py` scans all family folders and collects any exposed `<family_name>_registry` into `FAMILY_REGISTRIES`.

That map is then used by `list_algorithms()` to build the catalog dynamically.

## Public orchestration

The public functions in `pylstemp/api.py` orchestrate the workflow:

- validate inputs
- build masks
- call vegetation and thermal helpers
- select the requested algorithm from the proper family registry
- return final arrays in the requested unit

## Why this structure is useful

- adding a new split-window method is local to `pylstemp/algorithms/split_window/`
- adding a new emissivity method is local to `pylstemp/algorithms/emissivity/`
- adding a future family such as `atmosphere/` or `indices/` is mostly local to one new package
