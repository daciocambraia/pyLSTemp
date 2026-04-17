# pyLSTemp Project Context Backup

This file records the implementation context and project decisions used while rebuilding the library.

## Project identity

- Public project name: `pyLSTemp`
- Python import package: `pylstemp`
- Repository: <https://github.com/daciocambraia/pyLSTemp>
- Publication target: GitHub and PyPI

## Origin and attribution

This project is a clean rebuild inspired by the original `pylandtemp` library by Oladimeji Mudele.

- Original project: <https://github.com/pylandtemp/pylandtemp>
- Original credit is intentionally preserved in:
  - `CREDITS.md`
  - `docs/references.md`
  - `src/pylstemp/references.py`

## Core design decisions

- Keep the conversion methods and formulas aligned with the bibliographic references used in the original library.
- Reorganize the package by domain instead of mirroring the original folder structure.
- Use one file per algorithm where it improves readability and future expansion.
- Keep validation, metadata and registries centralized.
- Prepare the repository for future algorithm additions without restructuring the package.

## Final package structure

```text
src/pylstemp/
  core/
  vegetation/
  thermal/
  emissivity/
  temperature/
```

## Domain responsibilities

- `vegetation/`: vegetation-related calculations such as NDVI
- `thermal/`: brightness temperature and future thermal utilities
- `emissivity/`: emissivity algorithms and their registry
- `temperature/`: land surface temperature algorithms and registries
- `core/`: registry, metadata and validation infrastructure

## Scientific methods preserved

### Emissivity

- `avdan`
- `xiaolei`
- `gopinadh`

### Temperature

- Single-window:
  - `mono-window`
- Split-window:
  - `jiminez-munoz`
  - `kerr`
  - `mc-millin`
  - `price`
  - `sobrino-1993`

## Naming choices

- We intentionally use `pyLSTemp` as the project/package name for branding and repository visibility.
- We intentionally use `pylstemp` as the Python import name because lowercase imports are more idiomatic and tooling-friendly.

## Validation status

The new package was validated with pytest using the locally installed Python runtime.

- Result at handoff: `19 passed`

## Repository preparation

The project includes:

- `README.md`
- `CHANGELOG.md`
- `CONTRIBUTING.md`
- `CODE_OF_CONDUCT.md`
- GitHub issue templates
- pull request template
- CI workflow
- publish workflow for PyPI

## Environment note

An actual `.git` repository could not be initialized automatically in this environment because the `git` executable was not available here.

That does not block publication:

- you can upload the directory contents directly to GitHub
- or initialize git locally on your machine after copying this directory

