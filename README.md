# pyLSTemp

[![CI](https://github.com/daciocambraia/pyLSTemp/actions/workflows/ci.yml/badge.svg)](https://github.com/daciocambraia/pyLSTemp/actions/workflows/ci.yml)
[![License](https://img.shields.io/badge/license-Apache%202.0-blue.svg)](LICENSE)

`pyLSTemp` is a modular Python library for land surface temperature workflows built from Landsat imagery.

Repository: <https://github.com/daciocambraia/pyLSTemp>

## Scientific status (v1.11.0)

Use [scientific-methods.md](docs/scientific-methods.md) for decisions, limitations and migration.
Landsat 8/9 Level-1 radiometric calibration is metadata-driven. Retrieval coefficient
transfer to Landsat 9 is experimental. No ground-truth LST accuracy is claimed.
Available emissivity methods are Avdan and Gopinadh. Xiaolei has been removed
from this release; no available retrieval method requires an additional SR product.
NDVI is the single retained spectral index and uses TOA radiance in the default workflow.
EVI was removed because it is not used by the retrieval methods. The calibration module
provides MTL-driven TOA radiance, optional TOA reflectance and TOA brightness temperature.

Install examples with `pip install -e ".[examples]"`. Process scenes with:
`python scripts/validate_scenes.py --input ../Imagens --output Verificacao/v1.11.0`.
Outputs include calibrated TOA GeoTIFFs, LST, PWV ROIs, maps and reports.
Choose a new output folder for each run.

## Goals

- preserve the public workflow: `spectral_index`, `brightness`, `emissivity`, `water_vapor`, `single_window`, `split_window`
- make `brightness(...)` the explicit radiometric conversion step before LST workflows
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
      spectral_index/
      radiative_transfer/
  docs/
  tests/
  exemples/
  scripts/
```

## Public API

```python
from pylstemp import (
    spectral_index,
    brightness,
    emissivity,
    water_vapor,
    single_window,
    split_window,
    list_algorithms,
    reflectance,
    toa_radiance,
    toa_reflectance,
    read_mtl,
)
```

The public functions stay small and stable while the implementations live in modular families under `pylstemp/algorithms/`.
Sensor-specific thermal constants live under `pylstemp/sensors/`.

`brightness(...)` is the explicit radiometric conversion step. `single_window(...)` and `split_window(...)` expect brightness temperature arrays that were computed beforehand.

Typical thermal workflow:

1. calibrate Level-1 DN using `toa_radiance(..., metadata=mtl, band=...)` (W m-2 sr-1 um-1)
2. compute NDVI with calibrated B5/B4 radiance using `spectral_index(index="ndvi", ...)`
3. compute TOA BT with `brightness(radiance, band=10/11, metadata=mtl)` (K)
4. compute emissivity from NDVI; optionally estimate PWV with `water_vapor(method="wang-2015", ...)` (g/cm2)
5. pass BT in K and B4/B5 radiance into `single_window(...)` or `split_window(...)`

`LandsatScene.calibrated()` follows this radiance workflow. TOA reflectance is
available explicitly with `optical_quantity="reflectance"`. B2 is optional.
The DN shortcut in `brightness` requires `input_quantity="dn"`; its default
now expects radiance. Do not supply gain/bias with already calibrated radiance.
NDVI-derived emissivity thresholds need a compatible radiometric convention;
execution tests do not establish their scientific accuracy in a new convention.

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
- [Scientific methods and migration](docs/scientific-methods.md)
- [Validation report v1.11](docs/VALIDACAO_v1.11.md)
- [All-model test report](docs/TESTES_TODOS_MODELOS_v1.11.md)
- [Deep module and combination validation](docs/AVALIACAO_MODULOS_v1.11.md)
- [Improvements identified after validation](docs/MELHORIAS_MODULOS_v1.11.md)
- [Index corrections, reflectance conversion and method messages](docs/CORRECOES_INDICES_REFLECTANCIA_v1.11.md)
- [Previous scope: Xiaolei removal](docs/ESCOPO_LEVEL1_v1.11.md)
- [Radiance workflow, calibration and EVI removal](docs/FLUXO_RADIANCIA_v1.11.md)

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
