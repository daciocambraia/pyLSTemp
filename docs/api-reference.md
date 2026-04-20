# API Reference

## Public functions

### `ndvi(landsat_band_5, landsat_band_4, mask=None)`

Computes NDVI from the NIR and red bands.

### `brightness_band_10(band_10, sensor, rad_gain=None, rad_bias=None, mask=None)`

Computes brightness temperature for Landsat thermal band 10 using `sensor="landsat_8"` or `sensor="landsat_9"`.
Default values:
- `landsat_8`: `rad_gain=0.0003342`, `rad_bias=0.1`
- `landsat_9`: `rad_gain=0.00038`, `rad_bias=0.1`
You can override these values in the function call.

### `brightness_band_11(band_11, sensor, rad_gain=None, rad_bias=None, mask=None)`

Computes brightness temperature for Landsat thermal band 11 using `sensor="landsat_8"` or `sensor="landsat_9"`.
Default values:
- `landsat_8`: `rad_gain=0.0003342`, `rad_bias=0.1`
- `landsat_9`: `rad_gain=0.000349`, `rad_bias=0.1`
You can override these values in the function call.

### `emissivity_band_10(ndvi_image, red_band=None, emissivity_method="avdan-2016")`

Computes emissivity for the thermal band 10 workflow.
The default `avdan-2016` method follows Avdan and Jovanovska's NDVI rules: water (`NDVI < 0`), soil (`0 <= NDVI < 0.2`), mixed pixels (`0.2 <= NDVI <= 0.5`) using fractional vegetation cover and `C=0.005`, and vegetation (`NDVI > 0.5`).

### `emissivity_band_11(ndvi_image, red_band=None, emissivity_method="avdan-2016")`

Computes emissivity for the thermal band 11 workflow.
`avdan-2016` returns the same emissivity for both thermal workflows because the source method is a single-channel Band 10 workflow. For split-window methods that need band-specific emissivity, prefer `gopinadh-2018` or `xiaolei-2014`.

### `single_window(brightness_temperature_10, red_band, nir_band, lst_method="mono-window-2016", emissivity_method="avdan-2016", unit="kelvin")`

Computes land surface temperature using a single-channel method. `brightness_temperature_10` must be computed beforehand with `brightness_band_10(...)`.
`mono-window-2016` is a Band 10 single-channel workflow; do not pass Band 11 brightness temperature to this method.
The default `mono-window-2016` implementation uses `lambda=10.895e-6 m`, the midpoint of the Landsat 8/9 TIRS Band 10 range (`10.6-11.19 um`) used in the Avdan and Jovanovska workflow.

### `split_window(brightness_temperature_10, brightness_temperature_11, red_band, nir_band, lst_method, emissivity_method="gopinadh-2018", unit="kelvin", water_vapor=None)`

Computes land surface temperature using a split-window method. `brightness_temperature_10` and `brightness_temperature_11` must be computed beforehand with `brightness_band_10(...)` and `brightness_band_11(...)`.
The default split-window emissivity method is `gopinadh-2018`, because it provides band-specific emissivity for bands 10 and 11.
`avdan-2016` is blocked in `split_window(...)` because it is a single-channel emissivity method. Use `gopinadh-2018` or `xiaolei-2014` instead.

For `lst_method="du-2015"`, `water_vapor` represents atmospheric column water vapor in `g/cm2`.
When `water_vapor=None`, the implementation uses Du et al.'s all-CWV coefficient set for `[0.0, 6.3] g/cm2`.
When `water_vapor` is provided, the method selects the matching Du et al. CWV sub-range:
- `[0.0, 2.5]`
- `[2.0, 3.5]`
- `[3.0, 4.5]`
- `[4.0, 5.5]`
- `[5.0, 6.3]`

For `lst_method="jimenez-munoz-2014"`, `water_vapor` is required in `g/cm2`.
This method does not use a default CWV value because the result depends directly on scene atmospheric water vapor.

### `list_algorithms()`

Returns a catalog of discovered families, algorithm metadata, and original-library credit.

## Current algorithm families

### `emissivity`

- `avdan-2016`
- `gopinadh-2018`
- `xiaolei-2014`

### `single_channel`

- `mono-window-2016`

### `split_window`

- `jimenez-munoz-2014`
- `du-2015`
- `kerr-1992`
- `price-1984`
- `sobrino-1993`

### `thermal`

- `brightness`

Sensor constants are stored under `pylstemp/sensors/`.

### `vegetation`

- `ndvi`

### `radiative_transfer`

- reserved for future methods

## Internal organization

- shared public orchestration: `pylstemp/api.py`
- algorithm family discovery: `pylstemp/algorithms/__init__.py`
- algorithm module discovery inside each family: `pylstemp/registry.py`
- family implementations: `pylstemp/algorithms/*`
