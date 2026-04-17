# API Reference

## Public functions

### `ndvi(landsat_band_5, landsat_band_4, mask=None)`

Computes NDVI from the NIR and red bands.

### `brightness_temperature(landsat_band_10, landsat_band_11=None, mask=None)`

Computes brightness temperature for Landsat thermal bands.

### `emissivity(ndvi_image, landsat_band_4=None, emissivity_method="avdan")`

Computes emissivity for band 10 and band 11 from an NDVI image.

### `single_window(landsat_band_10, landsat_band_4, landsat_band_5, lst_method="mono-window", emissivity_method="avdan", unit="kelvin")`

Computes land surface temperature using a single-channel method.

### `split_window(landsat_band_10, landsat_band_11, landsat_band_4, landsat_band_5, lst_method, emissivity_method, unit="kelvin")`

Computes land surface temperature using a split-window method.

### `list_algorithms()`

Returns metadata about the registered algorithms and the original library credit.

## Public domains

### Vegetation

- `src/pylstemp/vegetation/ndvi.py`

### Thermal

- `src/pylstemp/thermal/brightness.py`

### Emissivity

- `src/pylstemp/emissivity/`

### Temperature

- `src/pylstemp/temperature/`
