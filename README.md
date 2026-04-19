# pyLSTemp

[![CI](https://github.com/daciocambraia/pyLSTemp/actions/workflows/ci.yml/badge.svg)](https://github.com/daciocambraia/pyLSTemp/actions/workflows/ci.yml)
[![License](https://img.shields.io/badge/license-Apache%202.0-blue.svg)](LICENSE)

`pyLSTemp` is a modular Python library for land surface temperature workflows built from Landsat imagery.

Repository: <https://github.com/daciocambraia/pyLSTemp>

## Goals

- preserve the public workflow: `ndvi`, `brightness_band_10`, `brightness_band_11`, `emissivity_band_10`, `emissivity_band_11`, `single_window`, `split_window`
- make `brightness_band_10(...)` and `brightness_band_11(...)` the explicit radiometric conversion steps before LST workflows
- support Landsat 8 and Landsat 9 through a `sensor` argument plus sensor-specific constants
- keep the published formulas and bibliographic references used by the original project
- make new algorithms easy to add by dropping a new `.py` file into the correct family folder
- keep the repository clean and readable, with one main responsibility per file
- retain visible credit to the original library by Oladimeji Mudele

## Current layout

```text
pyLSTemp/
  pylstemp/
    api.py
    registry.py
    sensors/
    validation.py
    utils.py
    algorithms/
      emissivity/
      single_channel/
      split_window/
      thermal/
      vegetation/
      radiative_transfer/
  docs/
  tests/
  tutorial/
```

## Public API

```python
from pylstemp import (
    ndvi,
    brightness_band_10,
    brightness_band_11,
    emissivity_band_10,
    emissivity_band_11,
    single_window,
    split_window,
    list_algorithms,
)
```

The public functions stay small and stable while the implementations live in modular families under `pylstemp/algorithms/`.
Sensor-specific thermal constants live under `pylstemp/sensors/`.

`brightness_band_10(...)` and `brightness_band_11(...)` are the explicit radiometric conversion steps. `single_window(...)` and `split_window(...)` expect brightness temperature arrays that were computed beforehand.

Typical thermal workflow:

1. compute `brightness_band_10(...)` and, when needed, `brightness_band_11(...)` using `sensor`, `rad_gain`, and `rad_bias`
2. pass the resulting brightness temperature arrays into `single_window(...)` or `split_window(...)`

## Modular architecture

The project now supports automatic discovery at two levels:

- algorithm discovery inside a family:
  add a new `.py` file with an `ALGORITHM_SPEC`
- family discovery inside `pylstemp/algorithms/`:
  add a new family package that exposes `<family_name>_registry`

That means `list_algorithms()` grows with the codebase instead of depending on a central hardcoded list.

## Documentation

- [Documentation Index](docs/index.md)
- [Installation](docs/installation.md)
- [Usage Guide](docs/usage.md)
- [API Reference](docs/api-reference.md)
- [Architecture](docs/architecture.md)
- [Extending the Library](docs/extending.md)
- [References](docs/references.md)

## Development

Install locally:

```bash
pip install -e .[dev]
```

Confirm that Python is importing this checkout:

```bash
python -c "import pylstemp; print(pylstemp.__file__)"
```

Run tests:

```bash
pytest
```

## Credits

This rebuild keeps explicit credit to the original project:

- Original library: `pylandtemp`
- Original author: `Oladimeji Mudele`
- Original repository: <https://github.com/pylandtemp/pylandtemp>

See [docs/references.md](docs/references.md) and [CREDITS.md](CREDITS.md) for attribution details.
