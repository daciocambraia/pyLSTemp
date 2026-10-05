# API Reference

## Public functions

### `spectral_index(index, **kwargs)`

Computes a spectral index selected by name. NDVI accepts calibrated radiance or
reflectance; record the input quantity because band-specific conversions can
change the ratio. The standard scene workflow uses TOA radiance. Raw DN is not generally
equivalent to calibrated radiance/reflectance. Undefined ratios and any nonfinite input
become NaN. NDVI uses the exact ratio for valid denominators; `eps=1e-15` is a
denominator tolerance, not an additive bias.
Only `spectral_index` is listed in the catalog; legacy `spectral_indices` imports
share the canonical NDVI implementation.
Currently supported:

- `index="ndvi"` with `nir`, `red`, and optional `mask`

Example:

```python
ndvi_image = spectral_index(
    index="ndvi",
    nir=nir,
    red=red,
)

```

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

### `emissivity(ndvi_image, band, band_4_red=None, emissivity_method="avdan-2016")`

Computes emissivity for the selected thermal band workflow.
Use `band="band_10"` or `band="band_11"`.
The default `avdan-2016` method follows Avdan and Jovanovska's NDVI rules: water (`NDVI < 0`), soil (`0 <= NDVI < 0.2`), mixed pixels (`0.2 <= NDVI <= 0.5`) using fractional vegetation cover and `C=0.005`, and vegetation (`NDVI > 0.5`).
`avdan-2016` returns the same emissivity for both thermal workflows because the source method is a single-channel Band 10 workflow. For split-window methods that need band-specific emissivity, prefer `gopinadh-2018`.

### `single_window(brightness_band_10, band_4_red, band_5_nir, lst_method="mono-window-2016", emissivity_method="avdan-2016", unit="kelvin")`

Computes land surface temperature using a single-channel method. `brightness_band_10` must be computed beforehand with `brightness(..., band="band_10")`.
`mono-window-2016` is a Band 10 single-channel workflow; do not pass Band 11 brightness temperature to this method.
The default `mono-window-2016` implementation uses `lambda=10.895e-6 m`, the midpoint of the Landsat 8/9 TIRS Band 10 range (`10.6-11.19 um`) used in the Avdan and Jovanovska workflow.

### `split_window(brightness_band_10, brightness_band_11, band_4_red, band_5_nir, lst_method, emissivity_method="gopinadh-2018", unit="kelvin", water_vapor=None)`

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
For `du-2015`, use a single scene-level value. When `water_vapor=None`, the implementation uses Du et al.'s all-CWV coefficient set for `[0.0, 6.3] g/cm2`.
When `water_vapor` is provided for `du-2015`, the method selects the matching Du et al. CWV sub-range. If the value falls in an overlap between adjacent ranges, it computes both estimates and returns their mean, following Du et al.'s continuity strategy:
- `[0.0, 2.5]`
- `[2.0, 3.5]`
- `[3.0, 4.5]`
- `[4.0, 5.5]`
- `[5.0, 6.3]`

`jimenez-munoz-2014` requires `water_vapor` and accepts either a single scene-level value or a raster with the same shape as the brightness temperature arrays. Use `water_vapor(method="wang-2015", ...)` for pixel-by-pixel water vapor or provide an external estimate.
Price, Kerr and Sobrino do not use `water_vapor`; supplying it emits a
`RuntimeWarning` explaining that it is ignored. Du rejects raster PWV with an
actionable `ValueError` and requires a finite scalar in `[0,6.3] g/cm2`.

### `water_vapor(brightness_band_10, brightness_band_11, ndvi_image, method="wang-2015", window_size=21, group_count=3)`

Estimates precipitable water vapor (`PWV`) in `g/cm2` using the selected method.
Currently supported:

- `method="wang-2015"`: NDVI-based split-window covariance-variance ratio method from Wang et al. (2015)

This method uses Landsat 8 TIRS brightness temperatures for bands 10 and 11 plus NDVI. It returns a water vapor array with the same shape as the input images. The default Wang 2015 configuration uses a 21 by 21 moving template, the nearest centered-window equivalent to the article's 20 by 20 template, and 3 scene-level NDVI groups.

```python
water = water_vapor(
    brightness_band_10=brightness_10,
    brightness_band_11=brightness_11,
    ndvi_image=ndvi_image,
    method="wang-2015",
)
```

The resulting water vapor raster can be used directly in `split_window(..., lst_method="jimenez-munoz-2014", water_vapor=water)`. For `du-2015`, provide a single scene-level value such as the mean of a water vapor raster if you want to select a specific CWV coefficient sub-range.

### `list_algorithms()`

Returns a catalog of discovered families, algorithm metadata, and original-library credit.
Each method includes `input_requirements` and `water_vapor_support`.
There are 12 algorithm entries, including exactly one NDVI.

### `reflectance(dn, *, metadata, band, kind="toa", mask=None, sun_elevation=None)`

Public import: `from pylstemp import reflectance`. Parse matching MTL with
`from pylstemp.calibration import read_mtl`.

- `kind="toa"`: Level-1 optical DN, integer band 1..9, MTL gain/offset and solar
  elevation correction. Optional elevation is in degrees, scalar or aligned raster.
- `kind="surface"`: existing Landsat 8/9 Collection 2 Level-2 SR_B1..SR_B7 DN
  with L2SP/L2SR metadata; applies `DN * 0.0000275 - 0.2`.
  Level-1 metadata and a second solar correction are rejected.

Nonpositive DN, nonfinite values and boolean masks become NaN. Physical
reflectance outside [0,1] is preserved for explicit quality decisions.
This function does not perform atmospheric correction of Level-1/TOA data.
SR scaling remains an optional calibration utility. Available emissivity methods
use NDVI and do not require an additional SR product.

~~~python
from pylstemp import reflectance, read_mtl
from pylstemp.calibration import read_mtl
red_toa = reflectance(red_dn, metadata=read_mtl("L1_MTL.txt"), band=4)
red_sr = reflectance(sr_b4_dn, metadata=read_mtl("L2_MTL.txt"), band=4, kind="surface")
~~~

## Validation messages

Public workflow errors identify function, method/band/sensor, input problem and
next action. Existing exception classes remain catchable; original causes are
chained. Shape errors include field names and actual shapes; boolean masks use
`True` for invalid pixels. Temperature outputs accept kelvin/celsius; inputs
remain Kelvin. Calibration errors explicitly distinguish Level-1 from Level-2.
See [verified examples and scene results](CORRECOES_INDICES_REFLECTANCIA_v1.11.md).

## Current algorithm families

### `emissivity`

- `avdan-2016`
- `gopinadh-2018`

### `single_channel`

- `mono-window-2016`

### `split_window`

- `jimenez-munoz-2014`
- `du-2015`
- `kerr-1992`
- `price-1984`
- `sobrino-1993`

### `water_vapor`

- `wang-2015`

### `thermal`

- `brightness`

Sensor constants are stored under `pylstemp/sensors/`.

### `spectral_index`

- `ndvi`

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
