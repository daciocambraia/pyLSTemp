# Diagnostic PWV and LST mode

The default `quality_mode="screened"` keeps the existing numerical outputs, exceptions and legacy diagnostic dictionary format. `quality_mode="diagnostic"` always returns a dictionary containing raw estimates and flags. Flags describe quality/applicability concerns; they are not probabilities or independent field validation.

```python
from pylstemp import water_vapor, single_window
from pylstemp.quality import QualityFlag, quality_legend

pwv = water_vapor(bt10, bt11, red=red, nir=nir, method="ren-2015",
                  window_size=33, quality_mode="diagnostic", mask=invalid)
lst = single_window(bt10, emissivity_10=e10, radiance_band_10=L10,
                    water_vapor=pwv["water_vapor"],
                    pwv_quality_flags=pwv["quality_flags"],
                    lst_method="jimenez-munoz-2014-sc",
                    quality_mode="diagnostic", unit="celsius", mask=invalid)
# lst['lst'] == lst['raw_lst']; units follow the requested temperature unit.
# Bits accumulate: a pixel can carry several reasons at once.
extrapolated = (lst['quality_flags'] & QualityFlag.PWV_OUT_OF_DOMAIN) != 0
```

## Returned arrays

PWV dictionaries include `water_vapor`/`raw_water_vapor` (g/cm2), `screened_water_vapor` (the original estimator), `sample_count`, `quality_flags` (uint16), `quality_acceptable`, `invalid_mask`, and a JSON-compatible `quality_legend`. Ren adds `ratio` and `chi_squared` (the squared thermal correlation, not a confidence probability). Wang adds count-weighted `r_squared` and `minimum_group_r_squared`.

LST dictionaries include `lst`/`raw_lst`, `screened_lst`, `lst_quality_flags` (local LST concerns), and `quality_flags` (local plus incoming PWV concerns). `screened_lst` applies the original LST screening to the SAME supplied PWV; reconstructing the original complete chain requires `screened_water_vapor` and its original spatial aggregation as well. Nonfinite scalars in diagnostic mode produce flagged NaNs; shape/parameter errors still raise.

`quality_acceptable` checks bits 1–64. Bits describing spatial aggregation or legacy coefficients remain visible even if that Boolean is true. That Boolean is a declared operational screen, not a claim that remaining pixels are accurate. It need not reproduce the legacy estimator: Wang originally rejects groups BEFORE aggregating; its raw and screened outputs can differ even when both are finite.

## Bit legend

| Value | Flag | Meaning |
|---:|---|---|
| 1 | INPUT_MASKED | Explicit input mask or required invalid/missing input |
| 2 | UNDEFINED | Mathematical undefined/nonfinite estimate |
| 4 | LOW_QUALITY | Thermal relation below threshold; Wang: at least one contributing group |
| 8 | INSUFFICIENT_SAMPLES | Below operational minimum; two samples still required for regression |
| 16 | PWV_OUT_OF_DOMAIN | Outside the method-specific source/operational PWV range |
| 32 | NONPHYSICAL | Negative PWV, nonpositive covariance, or nonpositive output Kelvin |
| 64 | ILL_CONDITIONED | Positive variance below the screened numerical tolerance |
| 128 | SPATIAL_MEAN_PWV | Caller supplied a spatially aggregated PWV |
| 256 | LEGACY_SENSOR_TRANSFER | Historical AVHRR-to-Landsat formulation |
| 512 | DU_GENERAL_FALLBACK | Du uses its published all-CWV coefficients outside per-PWV bins |

An explicit input mask is respected. No values are fabricated for missing data, zero variance, zero regression denominators or nonfinite expressions. Upstream calibration and radiometric/emissivity input contracts remain unchanged. Diagnostic mode removes operational PWV acceptance cuts, not the definition of each estimator: Wang NDVI groups/thermal sample selection and Ren's explicitly selected NDVI filtering remain part of the configured calculation. Use `ndvi_filter=False` explicitly for the thermal-only Ren variant.

Ren raw regression uses any mathematically calculable window (at least two samples, nonzero variances and finite PWV); count <10, weak covariance, tiny variance, negative PWV and source range violations become flags. Thresholds and source coefficients are unchanged. Wang raw regression aggregates all mathematically calculable groups; the screened estimator still selects accepted groups with the original threshold, variance and nonnegative-PWV controls.

SC retains the same polynomial beyond 0–3 g/cm2 and flags extrapolation. Jimenez SW retains its equation, including finite negative PWV with flags and values above its evaluated 0–6 range. Du has NO per-PWV coefficient set outside 0–6.3: diagnostic mode explicitly uses its existing published all-CWV row and sets both domain and fallback flags. This is a change of coefficient policy, not a justified extrapolation or clipping to the nearest bin. Invalid emissivity/BT/radiance input contracts remain enforced.

Spatial aggregation must be explicit. Callers can OR quality flags of finite contributing PWV pixels and add `SPATIAL_MEAN_PWV`, then pass that aligned uint16 array to LST. The second study run does this conservatively; one flagged donor can flag the aggregate. Keep contributor counts and acceptance fractions to interpret that aggregation.

Diagnostic mode is supported by the active temperature APIs. `du_from_scene` retains its existing screened semantics; use the public PWV/LST functions to construct an explicit diagnostic chain.
