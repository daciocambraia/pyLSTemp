# Changelog

## 1.11.0 - 2026-10-04 (updated 2026-10-05)

- Fix undefined NDVI ratios and nonfinite EVI inputs; keep one canonical NDVI catalog entry with legacy import aliases.
- Add explicit Level-1 TOA / Collection 2 Level-2 SR reflectance conversion with product-level guards.
- Add actionable public workflow errors, method input metadata and warnings for unused PWV; validate Du scalar PWV.
- Revalidate both supplied scenes: 813 tests, 106 subtests and 120 GeoTIFFs; see docs/CORRECOES_INDICES_REFLECTANCIA_v1.11.md.
- Correct SI units in mono-window; remove invalid upper LST cutoff.
- Correct Jimenez coefficient and Wang symmetric regression.
- Resolve Avdan soil constant using Table 2; document remaining source ambiguities.
- Require physical surface reflectance for Xiaolei; no automatic fixed DN scaling.
- Add MTL-driven TOA/BT calibration, per-pixel solar angles and C2 QA.
- Propagate nonfinite values, central NoData and explicit workflow masks.
- Vectorize Wang in bounded-memory chunks; test against scalar windows.
- Add independent regressions, calibrated notebooks and scene validation reports.
- Restore repository-root packaging/CI; use SPDX license metadata.

Migration: Xiaolei now expects surface reflectance in [0,1]. Numerical outputs change.
See docs/scientific-methods.md.


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
