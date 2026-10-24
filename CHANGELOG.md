# Changelog

## Consistent Jimenez-Munoz SC/SW selectors (2026-10-23)

- Use jimenez-munoz-2014-sw and jimenez-munoz-2014-sc, placing SC/SW after the year in both selectors. Update catalog, source cards, examples and documentation.
- Keep jimenez-munoz-2014 (SW) and jimenez-munoz-sc-2014 (SC) as compatibility aliases. Other method names, equations, coefficients and units are unchanged.

## Examples per method (2026-10-22)

- Replace aggregate/family guides and comparison scripts with 17 focused notebooks in exemple/, one for each method selector.
- Present a short introduction, required inputs, general call and parameter details before each image example.
- Preserve superseded examples in the local verification archive; keep equations and the public API unchanged.

## Unified family API (2026-10-22)

- Accept prepared band emissivities in split_window; remove the separate public entry point.
- Select Sobrino with emissivity(method=...) and Chavez with optical_correction(method=...), including reusable fitting parameters.
- Include all 17 method selectors in the catalog and remove the empty reserved family.
- Add a complete image-based notebook with parameter, unit, option and configuration details.

## Methodological audit completion (2026-10-22)

- Ship 20 reviewed method cards with source locations, coefficients, domains and explicit sensor/optical adaptations.
- Add optional LST/intermediate diagnostics and reproducible scene provenance, with optional complete imagery hashes.
- Apply caller masks to the Wang global NDVI scan; reject GeoTIFF output-window shape mismatches.
- Run independent synthetic scientific regressions against the installed wheel in CI; retain the complete scene suite and private data locally.


## Optical source contracts (2026-10-22)

- Record method-specific optical decisions from the supplied original Avdan, Rongali, Wang, Ren and Sobrino PDFs. Preserve unresolved conventions and scene-specific threshold transfers explicitly.
- Add source sensor, source location, optical input contract and review status to catalog metadata. Correct input-help text that could imply optical quantities are interchangeable.
- Preserve retrieval formulas, coefficients, default scene calibration and internal NDVI; no universal optical conversion is introduced.

## Internal NDVI and simpler public API (2026-10-22)

- Remove the public spectral-index dispatcher, its registry and legacy namespaces; use a single internal NDVI helper. The catalog has 13 algorithms.
- Emissivity, PWV, Sobrino and Kerr prepared-emissivity calls accept red/nir and compute NDVI internally. Prepared NDVI remains an alternative for numerical reuse; mixed input forms are rejected.
- Migrate workflows, examples and documentation; preserve prior modules/notebook locally under Verificacao.

## Ren/MSWCVR and documentation (2026-10-22)

- Add independent `ren-2015` PWV from verified original Eqs.1b/1c/2, with local NDVI screening, diagnostics and explicit domain/support choices.
- Allow Ren in Du scene raster/mean workflows with automatic halo and diagnostic exports; preserve Wang numerical defaults.
- Simplify the README image example to scene calibration, function calls and GeoTIFF output, without row/column configuration. Preserve the public documentation layout and update API, references and method limits.
- Keep scientific tests and detailed reports in the local verification archive.

## Source-checked image methods (2026-10-22)

- Added rozenstein-2014 with explicit atmospheric profiles, published fit intervals and PWV domain [0.5,3].
- Added prepared-emissivity SW API and Sobrino TM6/parameterized 2008 functions without assigning unsupported TIRS constants.
- Added reusable Chavez DOS/COST scene parameters, masks and an image-based example.
- Scientific tests, articles and real-scene outputs remain local; Ren was pending access to primary equations in that round.


## Public repository cleanup (2026-10-22)

- Moved scientific tests, scene validators and internal reports to the ignored local verification archive.
- Kept public API, examples, scientific contracts and validation status in the repository.
- CI and release workflows now check installation, imports and packaging without requiring local tests.


## Du raster PWV and explicit scene workflow (2026-10-22)

- Du accepts aligned PWV rasters with per-pixel coefficient selection and inclusive overlap averaging of LST estimates. General/scalar behavior is preserved.
- Invalid/out-of-domain raster PWV becomes NaN; mismatched shapes are rejected.
- Added general/mean/raster scene workflow for the alternative Wang -> Du chain, automatic halo, scene-wide NDVI bounds and provenance exports.
- Added boundary, independent-equation, tiled and real-scene validation. See docs/validation.md for actual results.
- At this earlier stage, the original Du/Ren estimator was pending source-equation audit; it is supplied by the Ren addition documented above.


## Publication structure review (2026-10-05)

- Documented the complete repository tree, all algorithms and calibration helpers.
- Updated scene validation scripts to cover Jimenez SC and optional B2 inputs.
- Added publication guidance and tests/tag/distribution checks to the publish workflow.
- Added contribution and conduct documents to the sdist; no RTE implementation added.


## Jimenez single-channel and documentation (2026-10-05)

- Added jimenez-munoz-2014-sc with explicit Band-10 TOA radiance/PWV and operational PWV screen [0,3].
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
