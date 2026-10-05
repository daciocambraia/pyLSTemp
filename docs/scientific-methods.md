# Scientific methods and migration - v1.11.0

## What has been verified

Independent numerical regression tests check formulas, units, masks and calibration.
Operational scene tests check execution and data consistency. Neither is a substitute
for validation against independent surface-temperature and atmospheric observations.
Near-surface air temperature is not a ground-truth substitute for skin temperature.

## Input contracts

- Thermal workflows use brightness temperature in kelvin, not DN or Level-2 ST_B10.
- NDVI/EVI use physical optical reflectance. Preserve the product type and calibration.
- Level-1 TOA reflectance: (MTL gain * DN + MTL offset) / sin(solar elevation).
- Per-pixel SZA, when present, is stored in hundredths of degrees. Elevation = 90 - SZA/100.
- Level-1 BT: K2 / log(1 + K1 / (radiance gain * DN + radiance offset)).
- All four thermal coefficients come from the scene MTL in the scene reader.
- C2 Level-2 SR_B* scaling is 0.0000275 * DN - 0.2. This scaling does not atmospherically correct Level-1.
- Xiaolei requires red surface reflectance in [0,1]. Atmospheric correction cannot be inferred from array values.
- QA excludes fill, dilated cloud, high-confidence cirrus/cloud/shadow/snow, selected optical saturation and terrain occlusion.
- Wang operates over land; exclude QA water. Cloud masking is an initial quality screen, not complete atmospheric correction.

Sources: [USGS Level-1 calibration](https://www.usgs.gov/landsat-missions/using-usgs-landsat-level-1-data-product),
[USGS C2 QA](https://www.usgs.gov/landsat-missions/landsat-collection-2-quality-assessment-bands),
[USGS Level-2 scale factors](https://www.usgs.gov/faqs/how-do-i-use-a-scale-factor-landsat-level-2-science-products).

## Explicit source decisions

### Avdan and Jovanovska (2016)

Use Table 2 soil emissivity 0.966, rather than the contradictory prose value 0.996.
Retain the published NDVI classes, water 0.991, vegetation 0.973, squared vegetation
fraction for mixed pixels and C=0.005 in that mixed class. This gives mixed endpoints
0.971 and 0.978, without values above 1. Class boundaries still have discontinuities:
these are explicit consequences of the adopted piecewise parameterization, not smoothed
away as an undocumented change. Negative NDVI alone is an empirical water proxy,
not a universal land-cover classifier. Do not use these constants as universal emissivities.
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
demonstrations. Xiaolei is not applied to these TOA inputs. Its array formula is tested
independently with physical surface reflectance.
No RMSE, bias against ground truth or scientific accuracy certification is claimed.

## Migration from v1.10

Numerical results change after unit/coefficient/reflectance corrections.
Xiaolei no longer rescales raw DN: supply surface reflectance and preserve provenance.
Temperature above 56.7 C is no longer discarded. Nonfinite/nonpositive absolute
temperature and invalid emissivity are NaN. Workflow masks are explicit keyword arguments.
Legacy spectral_indices remains available for compatibility; spectral_index is preferred.

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
nonfinite optical input produce NaN for NDVI/EVI. The tolerance is 1e-15 for
NDVI; the existing EVI absolute-value mask remains. Removing the bias can
change a piecewise emissivity class at an exact NDVI boundary.

The catalog now contains one NDVI. Legacy imports remain aliases to that
implementation. `reflectance(..., kind="surface")` accepts matching Collection 2
Level-2 SR data, while Level-1 can be converted to TOA. Scaling is not atmospheric
correction; the two local Level-1 scenes do not provide real SR for Xiaolei.
See [correction report](CORRECOES_INDICES_REFLECTANCIA_v1.11.md).
