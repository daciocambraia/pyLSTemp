# Changelog

## Jimenez single-channel and documentation (2026-10-05)

- Added jimenez-munoz-sc-2014 with explicit Band-10 TOA radiance/PWV and operational PWV screen [0,3].
- Restored function-by-function image examples and v1.10-style README organization, with links for every algorithm.
- Added SC to the full workflow and single-channel notebook; corrected Kerr bibliographic attribution.


## Image examples and workspace cleanup (2026-10-05)

- Replace synthetic-array usage examples with direct Landsat image reading and connected algorithms.
- Add a runnable image workflow; simplify the six notebooks and remove the hidden example-input helper.
- Consolidate current validation docs and preserve historical reports in the local verification archive.
- Remove exact duplicate verification products by SHA-256 and disposable build/cache files.

## Explicit TOA reflectance API (2026-10-05)

- Remove the redundant public `reflectance` dispatcher and its unused Level-2 selection branch.
- Use `toa_reflectance` directly for Level-1 TOA reflectance; retained calibration/retrieval equations are unchanged.
- Remove obsolete dispatcher-specific tests and update imports, help, API docs and release artifacts.

## Radiance workflow and EVI removal (2026-10-05)

- Remove unused EVI implementation, discovery entry, imports and active examples; retain one canonical NDVI.
- Add metadata-driven TOA radiance conversion; expose TOA reflectance explicitly.
- Move public brightness to calibration: default input TOA radiance, output TOA BT in K; DN requires input_quantity="dn".
- Standardize scene/examples/validation workflow on optical radiance and make B2 optional.
- Document quantity units, prevent double calibration, and compare radiance/reflectance NDVI on both supplied scenes.

## 1.11.0 - 2026-10-04 (updated 2026-10-05)

- Verify retained scope: 619 tests, 106 subtests, 486 real cases and 102 unchanged GeoTIFFs; see docs/ESCOPO_LEVEL1_v1.11.md.
- Remove Xiaolei implementation and catalog entry; retained emissivity methods are Avdan and Gopinadh. Old Xiaolei calls now raise InvalidMethodRequested.
- Clarify NDVI radiance/reflectance inputs; retain TOA-based scene calibration and optional SR scaling.
- Fix undefined NDVI ratios and nonfinite EVI inputs; keep one canonical NDVI catalog entry with legacy import aliases.
- Add explicit Level-1 TOA / Collection 2 Level-2 SR reflectance conversion with product-level guards.
- Add actionable public workflow errors, method input metadata and warnings for unused PWV; validate Du scalar PWV.
- Earlier index-correction stage: revalidate both supplied scenes with 813 tests, 106 subtests and 120 GeoTIFFs; see docs/CORRECOES_INDICES_REFLECTANCIA_v1.11.md.
- Correct SI units in mono-window; remove invalid upper LST cutoff.
- Correct Jimenez coefficient and Wang symmetric regression.
- Resolve Avdan soil constant using Table 2; document remaining source ambiguities.
- Require physical surface reflectance for Xiaolei; no automatic fixed DN scaling.
- Add MTL-driven TOA/BT calibration, per-pixel solar angles and C2 QA.
- Propagate nonfinite values, central NoData and explicit workflow masks.
- Vectorize Wang in bounded-memory chunks; test against scalar windows.
- Add independent regressions, calibrated notebooks and scene validation reports.
- Restore repository-root packaging/CI; use SPDX license metadata.

Migration: Xiaolei has been removed from the selected release scope.
Use Avdan for single-channel or Gopinadh for single-channel/split-window.
Earlier numerical corrections still change outputs relative to v1.10.
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
