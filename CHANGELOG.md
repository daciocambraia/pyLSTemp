# Changelog

All notable changes to this project will be documented in this file.

The format is based on Keep a Changelog and this project follows Semantic Versioning.

## [1.10.0] - 2026-04-30

### Changed

- Aligned `water_vapor(method="wang-2015")` defaults with Wang et al. (2015):
  `window_size=21` approximates the article's 20 by 20 template with a centered
  moving window, and `group_count=3` follows the article configuration.
- Changed Wang 2015 NDVI grouping to use scene-level NDVI group boundaries
  instead of recalculating NDVI boundaries independently for every local window.
- Aligned `emissivity_method="gopinadh-2018"` with Rongali et al. (2018) by
  using a method-specific linear FVC with `NDVIsoil=0.15` and
  `NDVIvegetation=0.48`.
- Aligned `lst_method="du-2015"` with Du et al. (2015) by averaging the two LST
  estimates when atmospheric column water vapor falls inside overlapping CWV
  sub-ranges.

### Added

- Added `VERIFICACAO_ALGORITMOS_ARTIGOS.md` with a method-by-method scientific
  audit against the local article PDFs.

## [0.1.0] - 2026-04-16

### Added

- full rebuild of the original library with a cleaner domain-first architecture
- official public package name `pyLSTemp`
- official Python import package `pylstemp`
- algorithm registries for emissivity and temperature methods
- test suite covering API, registries, validation, domains and attribution
- user documentation in `docs/`
- CI workflow for automated test execution

### Notes

- original library credit is preserved in `CREDITS.md`
- scientific conversion formulas were kept aligned with the referenced methods
