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

### `vegetation`

- `ndvi`

### `radiative_transfer`

- reserved for future methods

## Internal organization

- shared public orchestration: `pylstemp/api.py`
- algorithm family discovery: `pylstemp/algorithms/__init__.py`
- algorithm module discovery inside each family: `pylstemp/registry.py`
- family implementations: `pylstemp/algorithms/*`
