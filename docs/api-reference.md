# API Reference

## Public functions

### Internal NDVI

NDVI is calculated by one shared internal helper wherever required. There
is no public spectral-index dispatcher or separately registered NDVI method.
Supply aligned `red` and `nir` optical bands to emissivity/PWV functions.
Use the same radiometric convention for both bands. Masks use True=invalid.
Prepared NDVI remains an alternative input for numerical reuse; do not mix
it with `red`/`nir`. Undefined ratios and nonfinite inputs become NaN;
1e-15 is a denominator tolerance, not an additive bias.

### `toa_radiance(dn, *, metadata, band, mask=None)`

Convert Level-1 DN to TOA spectral radiance in **W m-2 sr-1 um-1**.
Bands 1..11 use their own `RADIANCE_MULT_BAND_x` and `RADIANCE_ADD_BAND_x`
from the matching MTL. Formula: `L = M_L * DN + A_L`. No solar rescaling.
Nonfinite values, DN <= 0 and mask=True become NaN; values are not clipped.
Public import: `from pylstemp import toa_radiance, read_mtl`.

### `toa_reflectance(dn, *, metadata, band, mask=None, sun_elevation=None)`

Convert Level-1 optical DN (bands 1..9) to **dimensionless TOA reflectance**:
`rho = (M_rho * DN + A_rho) / sin(solar elevation)`.
Elevation is in degrees; use a scalar or an aligned per-pixel array. The MTL
scene-centre value is the fallback. Negative/above-one output is preserved.
This does not perform atmospheric correction or produce surface reflectance.

### `brightness(thermal_band, band, sensor=None, rad_gain=None, rad_bias=None, mask=None, *, metadata=None, input_quantity="radiance")`

Canonical implementation: `pylstemp.calibration.brightness`, also exported at
`pylstemp.brightness` and `pylstemp.api.brightness`. Default input: **TOA radiance
in W m-2 sr-1 um-1**. Output: **TOA brightness temperature in K**.
Use band 10/11 or the documented aliases. Matching Level-1 MTL supplies K1/K2;
`sensor="landsat_8"`/`"landsat_9"` provides fallback constants if MTL is omitted.
USGS equation: `BT = K2 / log(1 + K1 / L)`. BT is not surface temperature.

Explicit `input_quantity="dn"` keeps the historical DN shortcut. Matching MTL
provides all coefficients. Without MTL, sensor gain/bias defaults are available
and `rad_gain`/`rad_bias` overrides are supported. Those arguments are rejected
for already calibrated radiance or with authoritative MTL. A sensor conflicting
with the MTL is also rejected. Nonpositive radiance and nonfinite inputs become NaN.
The legacy thermal-family band helpers still accept DN for compatibility.

### `emissivity(ndvi_image=None, band=10, band_4_red=None, emissivity_method="avdan-2016", *, red=None, nir=None, mask=None)`

Computes emissivity from `red` and `nir`, with internal NDVI. A prepared
`ndvi_image` remains accepted instead of optical bands.
Use `band="band_10"` or `band="band_11"`.
The default `avdan-2016` method follows Avdan and Jovanovska's NDVI rules: water (`NDVI < 0`), soil (`0 <= NDVI < 0.2`), mixed pixels (`0.2 <= NDVI <= 0.5`) using fractional vegetation cover and `C=0.005`, and vegetation (`NDVI > 0.5`).
`avdan-2016` returns the same emissivity for both thermal workflows because the source method is a single-channel Band 10 workflow. For split-window methods that need band-specific emissivity, prefer `gopinadh-2018`.

### `single_window(brightness_band_10, band_4_red, band_5_nir, lst_method="mono-window-2016", emissivity_method="avdan-2016", unit="kelvin", *, mask=None, radiance_band_10=None, water_vapor=None)`

Computes land surface temperature using a single-channel method. `brightness_band_10` must be computed beforehand with `brightness(..., band="band_10")`.
`mono-window-2016` is a Band 10 single-channel workflow; do not pass Band 11 brightness temperature to this method.
The default `mono-window-2016` implementation uses `lambda=10.895e-6 m`, the midpoint of the Landsat 8/9 TIRS Band 10 range (`10.6-11.19 um`) used in the Avdan and Jovanovska workflow.

`jimenez-munoz-sc-2014` implements the Band-10 single-channel formulation,
separate from the split-window key `jimenez-munoz-2014`. Supply matching
`radiance_band_10` in W m-2 sr-1 um-1 and `water_vapor` in g/cm2.
The operational polynomial PWV range is [0,3]: invalid scalars are rejected;
nonfinite, negative or >3 raster pixels become NaN. This is a scientific
screen motivated by the paper, not a claim that accuracy is guaranteed in range.
No atmospheric function or radiance is silently reconstructed from default sensor constants.
Both Avdan and Gopinadh emissivity methods are accepted. Avdan LST does not
accept the new atmospheric keywords because it does not use them.

### `split_window(brightness_band_10, brightness_band_11, band_4_red, band_5_nir, lst_method, emissivity_method="gopinadh-2018", unit="kelvin", water_vapor=None, *, mask=None, atmospheric_profile=None, temperature_range="0-60")`

Computes land surface temperature using a split-window method. `brightness_band_10` and `brightness_band_11` must be computed beforehand with `brightness(..., band="band_10")` and `brightness(..., band="band_11")`.
Example: use `lst_method="du-2015"` for the practical Du et al. split-window workflow.

```python
lst = split_window(
    brightness_band_10=brightness_10,
    brightness_band_11=brightness_11,
    band_4_red=red,
    band_5_nir=nir,
    lst_method="du-2015",
)
```

The default split-window emissivity method is `gopinadh-2018`, because it provides band-specific emissivity for bands 10 and 11 using Rongali et al.'s linear fractional vegetation cover with `NDVIsoil=0.15` and `NDVIvegetation=0.48`. The fractional vegetation cover is clipped to `0..1`; the final emissivity is still computed from the article's linear mixture.
`avdan-2016` is blocked in `split_window(...)` because it is a single-channel emissivity method. Use `gopinadh-2018` instead.

For `lst_method="du-2015"` or `lst_method="jimenez-munoz-2014"`, `water_vapor` represents atmospheric column water vapor in `g/cm2`.
For `du-2015`, use a scalar or an aligned raster of exactly the same shape. When `water_vapor=None`, the implementation uses Du et al.'s all-CWV coefficient set for `[0.0, 6.3] g/cm2`.
When `water_vapor` is provided for `du-2015`, the method selects the matching Du et al. CWV sub-range. If the value falls in an overlap between adjacent ranges, it computes both estimates and returns their mean, following Du et al.'s continuity strategy:

- `[0.0, 2.5]`
- `[2.0, 3.5]`
- `[3.0, 4.5]`
- `[4.0, 5.5]`
- `[5.0, 6.3]`

`jimenez-munoz-2014` requires `water_vapor` and accepts either a single scene-level value or a raster with the same shape as the brightness temperature arrays. Use `water_vapor(method="wang-2015", ...)` for pixel-by-pixel water vapor or provide an external estimate.
Price, Kerr and Sobrino do not use `water_vapor`; supplying it emits a
`RuntimeWarning` explaining that it is ignored. Du rejects nonfinite/out-of-domain scalars. Raster pixels outside `[0,6.3]`
or nonfinite become NaN; raster shapes must match, without broadcasting.

### `water_vapor(brightness_band_10, brightness_band_11, ndvi_image=None, method="wang-2015", window_size=None, group_count=3, *, red=None, nir=None, mask=None, ndvi_range=None, chunk_rows=8, min_samples=10, quality_threshold=0.95, ndvi_filter=True, return_diagnostics=False)`

Returns aligned PWV [g/cm2] from TOA brightness temperatures in kelvin.
`window_size=None` selects the method-specific default:

- `wang-2015` (default): window 21, three scene-level NDVI groups; requires
  red/nir (or prepared NDVI). Supply full-scene `ndvi_range` when processing spatial tiles.
- `ren-2015`: window 11, local NDVI +/-1.5 sigma screen, forward covariance/
  variance regression and domain [0.06,6.3]. On a 30-m delivery grid choose
  `window_size=33` for about 1 km support; the scene workflow selects 33.

Masks are boolean, True=invalid. Inputs must be aligned 2-D arrays. Windows
are centered, odd and at least three pixels wide. Ren-specific options are
`min_samples`, `quality_threshold`, `ndvi_filter` and `return_diagnostics`;
changed Ren controls are rejected for Wang. Ren rejects `ndvi_range` and
nondefault `group_count`, since it has no global NDVI groups.
Ren `ndvi_filter=False` explicitly permits thermal-only operation without
NDVI. Its sample minimum and quality threshold are operational choices,
not universal TIRS prescriptions from the article.

Normally the return value is a PWV array; for Ren, `return_diagnostics=True`
returns aligned arrays keyed by `water_vapor`, `raw_water_vapor`, `ratio`,
`chi_squared`, `sample_count` and `invalid_mask`. Rejected PWV is NaN.
See [source equations and support](image-only-methods.md#ren-2015-mswcvr).

```python
water = water_vapor(brightness_10, brightness_11, red=red, nir=nir,
                    method="ren-2015", window_size=33)
```

Provide accepted PWV to Du or Jimenez, respecting each LST method's own
domain. For calibration, halo, exports and provenance, see
[the scene workflow](du-pwv-workflow.md).

### `list_algorithms()`

Returns a catalog of discovered families, algorithm metadata, and original-library credit.
Each method includes `input_requirements` and `water_vapor_support`.
There are 13 registered algorithms. NDVI is an internal helper, outside the catalog.

### Migration: explicit TOA reflectance

Use `toa_reflectance(dn, metadata=mtl, band=4)` for Level-1 optical calibration.
The former `reflectance(..., kind="toa")` dispatcher has been removed. Its
Level-2 selection branch was unused by every retained retrieval model.
The internal `calibration.surface_reflectance` scaling helper remains separate;
it requires existing Level-2 SR data and does not atmospherically correct Level-1.

## Validation messages

Public workflow errors identify function, method/band/sensor, input problem and
next action. Existing exception classes remain catchable; original causes are
chained. Shape errors include field names and actual shapes; boolean masks use
`True` for invalid pixels. Temperature outputs accept kelvin/celsius; inputs
remain Kelvin. Calibration errors explicitly distinguish Level-1 from Level-2.
See [verified examples and scene results](validation.md).

## Current algorithm families

### `emissivity`

- `avdan-2016`
- `gopinadh-2018`

### `single_channel`

- `mono-window-2016`
- `jimenez-munoz-sc-2014`

### `split_window`

- `jimenez-munoz-2014`
- `du-2015`
- `kerr-1992`
- `price-1984`
- `sobrino-1993`
- `rozenstein-2014`

### `water_vapor`

- `wang-2015`
- `ren-2015`

### `thermal`

- `brightness`

Sensor constants are stored under `pylstemp/sensors/`.

### `radiative_transfer`

- reserved for future methods

## Internal organization

- shared public orchestration: `pylstemp/api.py`
- DN/radiance/reflectance/TOA BT calibration: `pylstemp/calibration.py`
- algorithm family discovery: `pylstemp/algorithms/__init__.py`
- algorithm module discovery inside each family: `pylstemp/registry.py`
- family implementations: `pylstemp/algorithms/*`

### `LandsatScene.calibrated(window=None, *, exclude_water=False, optical_quantity="radiance")`

Returns optical B4/B5 (and B2 when present), thermal BT10/BT11 [K], and the
boolean invalid-pixel mask. Optical defaults to TOA radiance [W m-2 sr-1 um-1].
Select `optical_quantity="reflectance"` for TOA reflectance with solar correction.
B4/B5/B10/B11, matching MTL, QA_PIXEL and QA_RADSAT are required. B2 is optional.
Both modes share QA and supplied SZA validity masks for controlled comparisons.
All returned arrays are aligned. Scene inputs are never modified.


## Source-checked additional methods

`split_window(..., lst_method="rozenstein-2014", water_vapor=pwv,
atmospheric_profile="midlatitude-summer", temperature_range="0-60")`
requires a selected published profile and PWV in [0.5,3] g/cm2. See
[domains, equations and adaptations](image-only-methods.md).

`split_window_from_emissivity(bt10, bt11, e10, e11, *, lst_method,
water_vapor=None, mask=None, unit="kelvin", ndvi_image=None, red=None, nir=None,
atmospheric_profile=None, temperature_range="0-60")` accepts prepared,
aligned band emissivities. Kerr requires red/nir for internal NDVI, or a prepared `ndvi_image`.

`sobrino_2004_tm6(ndvi=None, *, red=None, nir=None, mask=None)` is specific to TM5 band 6, with
unresolved bare-soil classes returned as NaN.

`sobrino_2008(ndvi=None, *, red=None, nir=None, soil_emissivity, vegetation_emissivity,
variant="simplified", red_surface=None, soil_red_coefficients=None,
cavity_factor=0.55, vegetation_cavity=0.005, ndvi_soil=0.2,
ndvi_vegetation=0.5, mask=None)` requires band-specific endmembers. Full mode
also needs `red_surface` and `soil_red_coefficients=(a,b)`; do not pass TOA
radiance or TOA reflectance as surface reflectance.

`fit_chavez(toa_reflectance, *, sun_elevation, method="cost",
percentile=0.01, assumed_dark_surface=0.01, mask=None)` returns reusable
parameters. `chavez_reflectance(toa_reflectance, *, parameters, mask=None)`
applies them, preserving the same angle and haze fit across tiles.
These functions are imported from the package root. They do not estimate
thermal atmospheric parameters and do not constitute operational SR.
