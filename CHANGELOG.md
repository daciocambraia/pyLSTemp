# Changelog

## 2.0.0 - 2026-11-05

### Breaking API changes

- Use method as the only selector in all calculation families; remove lst_method and emissivity_method inputs. The fixed Du/Rongali scene composition selects Wang/Ren with method.
- Group radiometric conversions under calibrate. Keep direct numerical conversion functions and read_mtl available.
- Use avdan-2016 within single-channel LST and jimenez-munoz-2014 within each SC/SW family. Optical selectors are chavez-dos-1996 and chavez-cost-1996; previous names are rejected.
- Rename the public QA file reader to quality_mask; array decoding is private.
- Scientific identities use (family, method). Scene provenance schema 2 groups cards by family and method.

### Inputs, diagnostics and export

- Preserve masked-array exclusions, reject complex arrays and require explicit Boolean options.
- Add JSON-safe processing identity and selected-result aliases to diagnostics of all six families.
- Keep raw and screened PWV/LST separately, including Wang diagnostics and both complete scene chains. Preserve numerical default results and source coefficients.
- Propagate upstream flags in diagnostic dictionaries and spatial means; retain contributor counts.
- Distinguish applicability, domain and unused-parameter warnings.
- Export uint8 masks, uint16 flags, processing metadata and a JSON quality legend; reject lossy integer conversions.
- Provide 17 executable notebooks, dependency-complete development setup, independent synthetic integration tests and installed-wheel CI.
- Consolidate current documentation. Research datasets, manuscripts, scenario grids and research-specific reports are excluded from the library and its distributions.

See [migration](docs/method-selection.md), [result contracts](docs/result-contracts.md)
and [verification](docs/validation.md).

## [1.10.0] - 2026-04-30

### Changed

- Aligned `water_vapor(method="wang-2015")` defaults with Wang et al. (2015):
  `window_size=21` approximates the article's 20 by 20 template with a centered
  moving window, and `group_count=3` follows the article configuration.
- Changed Wang 2015 NDVI grouping to use scene-level NDVI group boundaries
  instead of recalculating NDVI boundaries independently for every local window.
- Aligned `emissivity_method="rongali-2018"` with Rongali et al. (2018) by
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
