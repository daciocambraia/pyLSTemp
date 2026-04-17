# pyLSTemp

[![CI](https://github.com/daciocambraia/pyLSTemp/actions/workflows/ci.yml/badge.svg)](https://github.com/daciocambraia/pyLSTemp/actions/workflows/ci.yml)
[![License](https://img.shields.io/badge/license-Apache%202.0-blue.svg)](LICENSE)

`pyLSTemp` is a professional rebuild of the original library with a cleaner architecture, publication-ready documentation, and room for future algorithm expansion.

Repository: <https://github.com/daciocambraia/pyLSTemp>

## Goals

- preserve the public conversion workflow: `ndvi`, `brightness_temperature`, `emissivity`, `single_window`, `split_window`
- keep the published formulas and bibliographic references used by the original project
- make it easy to add new algorithms without restructuring the package
- include validation, automated tests and CI from the start
- retain visible credit to the original library by Oladimeji Mudele

## Project layout

```text
pyLSTemp/
  src/pylstemp/
    core/
    vegetation/
      ndvi.py
    thermal/
      brightness.py
    emissivity/
      base.py
      avdan.py
      xiaolei.py
      gopinadh.py
      registry.py
    temperature/
      base.py
      mono_window.py
      registry.py
      split_window/
        base.py
        jiminez_munoz.py
        kerr.py
        mc_millin.py
        price.py
        sobrino_1993.py
    api.py
    references.py
  tests/
  docs/
  .github/workflows/
  pyproject.toml
```

## Public API

```python
from pylstemp import (
    ndvi,
    brightness_temperature,
    emissivity,
    single_window,
    split_window,
)
```

The signatures of the main conversion functions were preserved so the migration path stays simple.

Internally, the project is now organized by domain:

- `vegetation/` for vegetation indices such as NDVI
- `thermal/` for thermal band conversions such as brightness temperature
- `emissivity/` for emissivity models
- `temperature/` for land surface temperature algorithms
- `core/` for registries, metadata and validation

## Extensibility

New algorithms are meant to be registered through internal registries instead of being hardcoded into the public API. That allows future additions with minimal changes:

1. implement a new algorithm class
2. register it in the correct registry
3. expose its metadata and tests

The codebase now uses a domain-first layout and one file per algorithm in the main execution path.

## Credits

This rebuild keeps explicit credit to the original project:

- Original library: `pylandtemp`
- Original author: `Oladimeji Mudele`
- Original repository: <https://github.com/pylandtemp/pylandtemp>

See [docs/references.md](docs/references.md) for the bibliographic references and [CREDITS.md](CREDITS.md) for attribution details.

## Documentation

- [Installation](docs/installation.md)
- [Usage Guide](docs/usage.md)
- [API Reference](docs/api-reference.md)
- [Extending the Library](docs/extending.md)
- [References](docs/references.md)

## Development

Install locally:

```bash
pip install -e .[dev]
```

Run tests:

```bash
pytest
```

## Publishing Notes

- PyPI/project name: `pyLSTemp`
- Python import name: `pylstemp`
- repository: `https://github.com/daciocambraia/pyLSTemp`
