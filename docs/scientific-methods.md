# Scientific methods and migration - v1.11.0

## What has been verified

Independent numerical regression tests check formulas, units, masks and calibration.
Operational scene tests check execution and data consistency. Neither is a substitute
for validation against independent surface-temperature and atmospheric observations.
Near-surface air temperature is not a ground-truth substitute for skin temperature.

## Input contracts

- Thermal workflows use brightness temperature in kelvin, not DN or Level-2 ST_B10.
- NDVI accepts calibrated optical radiance or reflectance. Preserve the quantity, product type and calibration.
- Rouse et al. (1974) used radiance; common multiplicative scaling cancels in NDVI, band-specific gains and offsets generally do not.
- NDVI thresholds used by downstream methods require a compatible radiometric convention.
- NDVI is calculated internally where required; there is no public spectral-index API.
- Default optical inputs are TOA radiance [W m-2 sr-1 um-1]: L = M_L * DN + A_L.
- Level-1 TOA reflectance: (MTL gain * DN + MTL offset) / sin(solar elevation).
- Per-pixel SZA, when present, is stored in hundredths of degrees. Elevation = 90 - SZA/100.
- TOA BT: K2 / log(1 + K1 / L), in kelvin. brightness defaults to radiance; DN requires input_quantity="dn".
- All four thermal coefficients come from the scene MTL in the scene reader.
- C2 Level-2 SR_B* scaling is 0.0000275 * DN - 0.2. This scaling does not atmospherically correct Level-1.
- The emissivity dispatcher includes Avdan, Gopinadh and Sobrino2004/2008; Xiaolei was removed because its additional SR requirement is outside the selected release scope.
- QA excludes fill, dilated cloud, high-confidence cirrus/cloud/shadow/snow, selected optical saturation and terrain occlusion.
- Wang and Ren scene PWV workflows operate over land; exclude QA water. Cloud masking is an initial quality screen, not complete atmospheric correction.

Sources: [USGS Level-1 calibration](https://www.usgs.gov/landsat-missions/using-usgs-landsat-level-1-data-product),
[USGS C2 QA](https://www.usgs.gov/landsat-missions/landsat-collection-2-quality-assessment-bands),
[USGS Level-2 scale factors](https://www.usgs.gov/faqs/how-do-i-use-a-scale-factor-landsat-level-2-science-products).

## Optical conventions: source audit (2026-10-22)

Internal NDVI removes a public calculation step; it does not make radiance,
TOA reflectance and surface reflectance interchangeable. Source thresholds
must be assessed together with the optical quantity and study conditions.
The original PDFs were checked for the following decisions:

| Parametrization | Source location | Optical decision and remaining condition |
|---|---|---|
| Avdan 2016 | p.3, Sections 2.3.1-2.3.3, Eqs.3-6; p.4, Table 2 | The scene input quantity is not uniquely specified. The discussion links fixed global 0.2/0.5 endmembers to surface reflectivities and states that TOA thresholds depend on atmospheric conditions. Radiance/TOA use is an adaptation, not established equivalence. |
| Rongali 2018 (`gopinadh-2018`) | PDF pp.5-6, Steps 1/3-5, Eqs.3/5-7, Table 2; p.8 | Adopt Step 1, which includes optical TOA radiance, before NDVI. The 0.15/0.48 endpoints are study-scene averages; transferring them is explicit, not a universal calibration. The workflow figure alone does not establish a different optical quantity. |
| Sobrino 2004 TM6 | p.436, Sections 3/4, Eqs.9/13/14 | Section 4 constructs NDVI from TOA reflectivities as a first approximation and prefers surface reflectivities. Radiance is not established as equivalent. The function retains only the implemented mixed/vegetation classes and TM6 constants. |
| Sobrino 2008 | pp.317-318, Eqs.5-9 | Thresholds and endmembers require sensor/band and optical-convention justification. Full mode additionally requires surface red reflectance with compatible soil coefficients. Simplifying the mixture does not prove radiance/reflectance equivalence. |
| Wang 2015 | Section 2.3, Eqs.2-4, Figure 3 | The inspected description specifies NDVI groups, thermal sample selection and emissivity ratios, without explicitly fixing the optical radiometric quantity. Keep this uncertainty visible. |
| Ren 2015 | Section 4.2, local NDVI filter | The local +/-1.5 sigma criterion is specified; its optical radiometric quantity is not explicitly fixed in the inspected description. Record the operational quantity; thermal-only mode remains separate. |

These findings do not justify changing every workflow to one optical quantity.
The current scene radiance default is an operational convention, not proof
that all downstream parametrizations were calibrated in radiance. Rouse's
NDVI definition does not establish the validity of thresholds in later papers.
No optical conversion, coefficient or numerical formula was changed by this
source-contract update. Surface-reflectance input must come from an identified
surface product or declared correction, not from relabelling Level-1 data.

`list_algorithms()` now includes `source_sensor`, `source_location`,
`optical_input_contract` and `source_review_status`. A recorded source decision,
a passing numerical test and successful scene execution are distinct evidence.
All 13 registered methods and seven standalone conversion/variant entries now have
[reviewed source cards](method-cards.md), including equations, coefficient branches,
source locations, domains, sensor origin and explicit adaptations. Numerical tests
and empirical accuracy remain separate evidence states.
Sobrino and Chavez are selected through the family dispatchers and included in the catalog.

The low-level API receives arrays and cannot infer their radiometric units.
The caller must supply compatible calibrated quantities and preserve their
provenance. This limitation is documented rather than silently relabelling
unknown arrays or inventing an automatic atmospheric correction.

## Explicit source decisions

### Avdan and Jovanovska (2016)

Use Table 2 soil emissivity 0.966, rather than the contradictory prose value 0.996.
Retain the published NDVI classes, water 0.991, vegetation 0.973, squared vegetation
fraction for mixed pixels and C=0.005 in that mixed class. This gives mixed endpoints
0.971 and 0.978, without values above 1. Class boundaries still have discontinuities:
these are explicit consequences of the adopted piecewise parameterization, not smoothed
away as an undocumented change. Negative NDVI alone is an empirical water proxy,
not a universal land-cover classifier. Do not use these constants as universal emissivities.
The source has an additional class inconsistency: the vegetation branch of
Eq.6 prints soil emissivity plus C, while the prose and Table 2 assign 0.973.
The implementation adopts the prose/Table-2 vegetation value; it does not
claim literal reproduction of both conflicting definitions. Table-1 thermal
constant labels and illustrative gains are not substituted for the matching
scene MTL calibration.
Mono-window uses wavelength 10.895e-6 metres and rho=1.438e-2 metre kelvin.
The correction uses absolute temperature, even though source prose mentions Celsius.

### Wang et al. (2015)

Use Figure 3's symmetric regression estimate (R11,10 + 1/R10,11)/2.
Preserve means calculated before sample filtering, r-squared threshold 0.97,
scene-wide NDVI groups, count-weighted PWV and the source regression coefficients.
The centered 21x21 window is an explicit adaptation of the source 20x20 template.
Vectorization changes execution, not the numerical method, and is tested against scalar windows.
Chunk rows control memory. External spatial tiles require radius-sized halo pixels
and full-scene ndvi_range. Invalid central pixels are never implicitly interpolated.
Nonfinite/negative PWV is NaN. No arbitrary upper PWV clipping is applied; source-domain
extrapolations must be identified in reports.

### Ren et al. (2015)

The supplied PDF confirms Eqs.1b/1c and Eq.2: forward covariance divided by
B10 variance, with PWV = -9.674*Rji^2 + 0.653*Rji + 9.087. The implementation
uses local means and the Section 4.2 NDVI +/-1.5 sigma sample screen, assuming
unity emissivity ratio. It does not reuse Wang groups or Wang regression.
The source calibration domain is [0.06,6.3] g/cm2. Centered odd windows,
minimum 10 samples and a 0.95 quality screen are explicit operational choices.
The standalone default is 11 pixels; the scene workflow uses 33 pixels for
about 1 km on the usual 30-m delivery grid. Resampling does not create
independent native-TIRS observations. See [equations, diagnostics and support
choices](image-only-methods.md#ren-2015-mswcvr).

### Jimenez-Munoz et al. (2014)

Use Table I c1=1.378, with the other published coefficients.
Scalar PWV must be finite and nonnegative; invalid raster PWV pixels are masked.
Computable positive PWV does not imply calibration-domain validity.

### Price (1984), Kerr (1992), Sobrino (1993)

These are historical AVHRR formulations adapted to Landsat arrays, not calibrated
Landsat retrieval models. Price's scanned expression contains an apparent algebra/sign
inconsistency. Keep the existing factor (5.5-e)/4.5 explicitly as a first-order
inverse-emissivity correction: e^(-1/n) approximately 1+(1-e)/n for n=4.5.
Do not claim literal reproduction of the conflicting printed factor (3.5+e)/4.5.
Price is retained for reproducibility and comparison, with a runtime warning.
Use these adaptations only with an independently justified sensor-specific validation.

## Sensor and validation limits

Radiometric conversion supports Landsat 8 and Landsat 9 metadata. This does not establish
that Landsat-8 retrieval/emissivity coefficients are valid for Landsat 9. All Landsat-9
LST and PWV results here are experimental coefficient transfers.
The two supplied scenes have different acquisition dates and grids; differences between
them are not a cross-sensor accuracy measurement.
The Level-1 scene runs use TOA-derived NDVI and empirical emissivity as operational
demonstrations. Current NDVI-derived emissivity uses Avdan or Gopinadh.
Xiaolei and its associated synthetic-SR combinations have been removed.
No RMSE, bias against ground truth or scientific accuracy certification is claimed.

## Migration from v1.10

Numerical results change after unit/coefficient/reflectance corrections.
Xiaolei is not available in this release. Existing calls selecting it raise
InvalidMethodRequested; Avdan is available for single-channel and Gopinadh for
single-channel and split-window workflows.
Temperature above 56.7 C is no longer discarded. Nonfinite/nonpositive absolute
temperature and invalid emissivity are NaN. Workflow masks are explicit keyword arguments.
The public spectral-index dispatcher and legacy namespaces were removed; retained methods calculate NDVI internally.

## Primary references

The full papers were examined from the user's local Articles folder. They are not
redistributed in the repository. Bibliographic details remain in [references.md](references.md).
The original v1.10 audit and new local reports are preserved under Verificacao/.


Wang reference data: TIGR3 PWV spans 0.066 to 7.833 g/cm2 (source page 6).
The scene runner preserves raw diagnostic products and adds a range-extrapolation mask
and range-screened products. This screen does not establish ground-truth validity.
The supplied C2 SZA is for B4; using it for B2/B5 is an explicit common optical-angle approximation.
See [USGS angle files](https://www.usgs.gov/landsat-missions/solar-illumination-and-sensor-viewing-angle-coefficient-files).
Mono-window is an emissivity-only correction here; it does not explicitly retrieve atmospheric transmission or path radiance.

## Index and calibration update (2026-10-05)

NDVI no longer adds epsilon to a valid denominator. Undefined ratios and any
nonfinite optical input produce NaN for NDVI. The tolerance is 1e-15. Removing the bias can
change a piecewise emissivity class at an exact NDVI boundary.

NDVI now uses one shared internal helper, outside the algorithm catalog. Level-1 optical DN is converted directly with `toa_reflectance`.
The redundant public `reflectance` dispatcher has been removed. The separate internal
`surface_reflectance` helper only scales existing Level-2 SR; scaling is not atmospheric
correction. Current retrieval methods do not require an additional SR product.
See [correction report](validation.md).

## Current release scope (2026-10-05)

Xiaolei was removed from discovery, implementation, imports and active examples.
The current catalog has 13 algorithms; NDVI is an internal calculation.
TOA radiance is the default scene workflow. TOA reflectance remains an explicit
alternative. Public brightness is implemented in calibration and exported at
the root and API. Its default input is radiance; the legacy thermal family
helpers keep their documented DN convention for compatibility.
Radiance and reflectance NDVI generally differ because per-band coefficients
do not cancel. Published emissivity endmembers/classes are preserved, not
recalibrated implicitly. A radiance workflow needs independent justification
of these thresholds before scientific application. See the new verification
report for measured changes on both supplied scenes.
Rouse reference: [NASA original record](https://ntrs.nasa.gov/citations/19740022614).
See [current verification report](validation.md).

## Jimenez-Munoz single-channel addition (2026-10-05)

`jimenez-munoz-2014-sc` uses Eqs. (1), (2), (4), (6) of the 2014 paper.
For Band 10, b_gamma=1324 K. The rows of C multiply [w^2,w,1]:
(0.04019,0.02916,1.01523), (-0.38333,-1.50294,0.20324),
(0.00918,1.36072,-0.27514). They are distinct from SW Table I.
TOA radiance and BT must come from the same band and calibration.

The paper reports poor performance of polynomial atmospheric functions for
w>3 g/cm2. We therefore apply an explicit operational screen [0,3]:
invalid scalar PWV raises ValueError; invalid/out-of-range raster pixels
become NaN. We do not clip PWV into the range or imply ground-truth accuracy.
Three is an operational boundary; the paper describes better performance
below three, not a guarantee at that boundary. For humid atmospheres,
consider SW or independently estimated atmospheric functions; direct
atmospheric-function and RTE retrievals are not implemented by this addition.

The coefficient matrix is published for Landsat 8 Band 10 only. Landsat 9
results are experimental transfer. Radiometric calibration itself uses the
matching sensor MTL. Wang PWV requires both thermal bands even when LST SC
uses Band 10 only. The radiance NDVI convention and emissivity thresholds
retain their previously documented limitations.
[Original article](https://doi.org/10.1109/LGRS.2014.2312032).

## Additional source-checked methods (2026-10-22)

The catalog includes Rozenstein 2014 LST and Ren 2015 PWV. Sobrino 2004/2008
emissivity and Chavez DOS/COST optical correction use family dispatchers
with explicit band/domain requirements. They do not replace the
historical Sobrino 1993 AVHRR temperature adaptation or silently calibrate
TM coefficients for TIRS. See [additional methods](image-only-methods.md).

## Completed source audit and reproducibility

The [20 method cards](method-cards.md) accompany the installed package. Price
retains the explicitly documented inverse-emissivity adaptation, rather than
claiming literal reproduction of the conflicting printed factor. Kerr's .11/.72
endpoints specifically require atmospherically corrected NDVI in its source
(p.205); using radiance/TOA NDVI or transferring its AVHRR coefficients remains
an adaptation. No coefficients were changed merely to obtain plausible LST.

For array calls, `optical_quantity` declares radiance, TOA reflectance
(`reflectance`/`toa_reflectance`) or surface reflectance. It does not convert
between them or validate scene endpoints. The default `None` is recorded as
undeclared in optional diagnostics. `return_diagnostics=True` preserves NDVI
and emissivities alongside the LST result, with the optical contract.

`du_from_scene(..., diagnostics=True)` additionally retains calibrated optical
bands and BT. Its provenance records the installed source/card digest, NumPy
and Python versions, MTL coefficients and checksum, grid, mask checksum, QA
policy, selected method cards and parameters. `hash_inputs=True` adds complete
SHA256 checksums of imagery; otherwise imagery size/mtime are only identifiers,
not proof of content identity. Default numerical results are unchanged.

Wang scene-bound scanning now applies the caller's whole-scene mask as well as
QA and thermal validity. Reuse those bounds and a consistent mask for all tiles.
GeoTIFF export rejects arrays whose shape differs from the specified output
window, preventing silent origin/extent mismatch.

Calibration auxiliaries were also checked against the official USGS
[Collection 2 QA bit tables](https://www.usgs.gov/landsat-missions/landsat-collection-2-quality-assessment-bands)
and [Level-2 product scaling](https://www.usgs.gov/landsat-missions/landsat-collection-2-level-2-science-products).
`surface_reflectance` scales an existing SR product; it does not perform its
atmospheric correction or replace product QA/range screening. QA_RADSAT B2/B4/B5
and terrain-occlusion bits form the documented conservative scene mask; they
are not thermal saturation bits.

## Unified family interface

`emissivity(..., method=...)` selects Avdan, Rongali or Sobrino. Chavez DOS/COST
uses `optical_correction(..., method=...)`, which returns an array or diagnostics
with reusable parameters. Both appear in the 17-selector catalog. Their source
conditions and coefficient choices are unchanged. `split_window` accepts
calibrated optical bands or a prepared band-specific emissivity pair, with
conflicting/unused input routes rejected. The empty reserved family was removed.
See the [per-method notebooks](../exemple/README.md) for all
parameters, units and options.
