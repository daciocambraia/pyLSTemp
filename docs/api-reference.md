# API Reference

## Public functions

### `ndvi(landsat_band_5, landsat_band_4, mask=None)`

Computes NDVI from the NIR and red bands.

### `brightness_temperature_band_10(thermal_band, sensor, rad_gain, rad_bias, mask=None)`

Computes brightness temperature for Landsat thermal band 10 using `sensor="landsat_8"` or `sensor="landsat_9"`.

### `brightness_temperature_band_11(thermal_band, sensor, rad_gain, rad_bias, mask=None)`

Computes brightness temperature for Landsat thermal band 11 using `sensor="landsat_8"` or `sensor="landsat_9"`.

### `brightness_temperature(landsat_band_10, sensor, rad_gain_band_10, rad_bias_band_10, landsat_band_11=None, rad_gain_band_11=None, rad_bias_band_11=None, mask=None)`

Computes brightness temperature for Landsat thermal bands using `sensor="landsat_8"` or `sensor="landsat_9"`.
`rad_gain_band_x` and `rad_bias_band_x` are informed manually in the function call and are different from `K1` and `K2`.

### `emissivity(ndvi_image, landsat_band_4=None, emissivity_method="avdan")`

Computes emissivity for band 10 and band 11 from an NDVI image.

### `single_window(brightness_temperature_10, red_band, nir_band, lst_method="mono-window", emissivity_method="avdan", unit="kelvin")`

Computes land surface temperature using a single-channel method. `brightness_temperature_10` must be computed beforehand with `brightness_temperature(...)`.

### `split_window(brightness_temperature_10, brightness_temperature_11, red_band, nir_band, lst_method, emissivity_method, unit="kelvin")`

Computes land surface temperature using a split-window method. `brightness_temperature_10` and `brightness_temperature_11` must be computed beforehand with `brightness_temperature(...)`.

### `list_algorithms()`

Returns a catalog of discovered families, algorithm metadata, and original-library credit.

## Current algorithm families

### `emissivity`

- `avdan`
- `gopinadh`
- `xiaolei`

### `single_channel`

- `mono-window`

### `split_window`

- `jiminez-munoz`
- `kerr`
- `mc-millin`
- `price`
- `sobrino-1993`

### `thermal`

- `landsat-brightness`

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
