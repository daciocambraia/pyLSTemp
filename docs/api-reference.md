# API Reference

## Public functions

### `ndvi(landsat_band_5, landsat_band_4, mask=None)`

Computes NDVI from the NIR and red bands.

### `brightness_temperature_band_10(band_10, sensor, rad_gain=None, rad_bias=None, mask=None)`

Computes brightness temperature for Landsat thermal band 10 using `sensor="landsat_8"` or `sensor="landsat_9"`.
Default values:
- `landsat_8`: `rad_gain=0.0003342`, `rad_bias=0.1`
- `landsat_9`: `rad_gain=0.00038`, `rad_bias=0.1`
You can override these values in the function call.

### `brightness_temperature_band_11(band_11, sensor, rad_gain=None, rad_bias=None, mask=None)`

Computes brightness temperature for Landsat thermal band 11 using `sensor="landsat_8"` or `sensor="landsat_9"`.
Default values:
- `landsat_8`: `rad_gain=0.0003342`, `rad_bias=0.1`
- `landsat_9`: `rad_gain=0.000349`, `rad_bias=0.1`
You can override these values in the function call.

### `emissivity_band_10(ndvi_image, red_band=None, emissivity_method="avdan")`

Computes emissivity for the thermal band 10 workflow.

### `emissivity_band_11(ndvi_image, red_band=None, emissivity_method="avdan")`

Computes emissivity for the thermal band 11 workflow.

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
