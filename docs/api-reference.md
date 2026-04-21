# API Reference

## Public functions

### `spectral_indices(indice, **kwargs)`

Computes a spectral index selected by name.
Currently supported:

- `indice="ndvi"` with `band_5_nir`, `band_4_red`, and optional `mask`

Example:

```python
ndvi_image = spectral_indices(
    indice="ndvi",
    band_5_nir=band_5_nir,
    band_4_red=band_4_red,
)
```

### `brightness_band_10(band_10, sensor, rad_gain=None, rad_bias=None, mask=None)`

Computes brightness temperature for Landsat thermal band 10 using `sensor="landsat_8"` or `sensor="landsat_9"`.
`rad_gain` corresponds to `RADIANCE_MULT_BAND_10` and `rad_bias` corresponds to `RADIANCE_ADD_BAND_10`.
Default values:
- `landsat_8`: `rad_gain=0.0003342`, `rad_bias=0.1`
- `landsat_9`: `rad_gain=0.00038`, `rad_bias=0.1`
You can override these values in the function call.

### `brightness_band_11(band_11, sensor, rad_gain=None, rad_bias=None, mask=None)`

Computes brightness temperature for Landsat thermal band 11 using `sensor="landsat_8"` or `sensor="landsat_9"`.
`rad_gain` corresponds to `RADIANCE_MULT_BAND_11` and `rad_bias` corresponds to `RADIANCE_ADD_BAND_11`.
Default values:
- `landsat_8`: `rad_gain=0.0003342`, `rad_bias=0.1`
- `landsat_9`: `rad_gain=0.000349`, `rad_bias=0.1`
You can override these values in the function call.

### `emissivity_band_10(ndvi_image, band_4_red=None, emissivity_method="avdan-2016")`

Computes emissivity for the thermal band 10 workflow.
The default `avdan-2016` method follows Avdan and Jovanovska's NDVI rules: water (`NDVI < 0`), soil (`0 <= NDVI < 0.2`), mixed pixels (`0.2 <= NDVI <= 0.5`) using fractional vegetation cover and `C=0.005`, and vegetation (`NDVI > 0.5`).

### `emissivity_band_11(ndvi_image, band_4_red=None, emissivity_method="avdan-2016")`

Computes emissivity for the thermal band 11 workflow.
`avdan-2016` returns the same emissivity for both thermal workflows because the source method is a single-channel Band 10 workflow. For split-window methods that need band-specific emissivity, prefer `gopinadh-2018` or `xiaolei-2014`.

### `single_window(brightness_band_10, band_4_red, band_5_nir, lst_method="mono-window-2016", emissivity_method="avdan-2016", unit="kelvin")`

Computes land surface temperature using a single-channel method. `brightness_band_10` must be computed beforehand with `brightness_band_10(...)`.
`mono-window-2016` is a Band 10 single-channel workflow; do not pass Band 11 brightness temperature to this method.
The default `mono-window-2016` implementation uses `lambda=10.895e-6 m`, the midpoint of the Landsat 8/9 TIRS Band 10 range (`10.6-11.19 um`) used in the Avdan and Jovanovska workflow.

### `split_window(brightness_band_10, brightness_band_11, band_4_red, band_5_nir, lst_method, emissivity_method="gopinadh-2018", unit="kelvin", water_vapor=None)`

Computes land surface temperature using a split-window method. `brightness_band_10` and `brightness_band_11` must be computed beforehand with `brightness_band_10(...)` and `brightness_band_11(...)`.
Example: use `lst_method="du-2015"` for the practical Du et al. split-window workflow.

```python
lst = split_window(
    brightness_band_10=brightness_10,
    brightness_band_11=brightness_11,
    band_4_red=band_4_red,
    band_5_nir=band_5_nir,
    lst_method="du-2015",
)
```

The default split-window emissivity method is `gopinadh-2018`, because it provides band-specific emissivity for bands 10 and 11.
`avdan-2016` is blocked in `split_window(...)` because it is a single-channel emissivity method. Use `gopinadh-2018` or `xiaolei-2014` instead.

For `lst_method="du-2015"` or `lst_method="jimenez-munoz-2014"`, `water_vapor` represents atmospheric column water vapor in `g/cm2`.
For `du-2015`, use a single scene-level value. When `water_vapor=None`, the implementation uses Du et al.'s all-CWV coefficient set for `[0.0, 6.3] g/cm2`.
When `water_vapor` is provided for `du-2015`, the method selects the matching Du et al. CWV sub-range:
- `[0.0, 2.5]`
- `[2.0, 3.5]`
- `[3.0, 4.5]`
- `[4.0, 5.5]`
- `[5.0, 6.3]`

`jimenez-munoz-2014` requires `water_vapor` and accepts either a single scene-level value or a raster with the same shape as the brightness temperature arrays. Use `water_vapor_wang_2015(...)` for pixel-by-pixel water vapor or provide an external estimate.
Current non-Du/Jimenez split-window methods do not use `water_vapor`.

### `water_vapor_wang_2015(brightness_band_10, brightness_band_11, ndvi_image, window_size=5, group_count=5)`

Estimates precipitable water vapor (`PWV`) in `g/cm2` using the NDVI-based split-window covariance-variance ratio method from Wang et al. (2015).
This method uses Landsat 8 TIRS brightness temperatures for bands 10 and 11 plus NDVI. It returns a water vapor array with the same shape as the input images.

```python
water_vapor = water_vapor_wang_2015(
    brightness_band_10=brightness_10,
    brightness_band_11=brightness_11,
    ndvi_image=ndvi_image,
)
```

The resulting `water_vapor` raster can be used directly in `split_window(..., lst_method="jimenez-munoz-2014", water_vapor=water_vapor)`. For `du-2015`, provide a single scene-level value such as the mean of a water vapor raster if you want to select a specific CWV coefficient sub-range.

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

### `water_vapor`

- `wang-2015`

### `thermal`

- `brightness`

Sensor constants are stored under `pylstemp/sensors/`.

### `spectral_indices`

- `ndvi`

### `radiative_transfer`

- reserved for future methods

## Internal organization

- shared public orchestration: `pylstemp/api.py`
- algorithm family discovery: `pylstemp/algorithms/__init__.py`
- algorithm module discovery inside each family: `pylstemp/registry.py`
- family implementations: `pylstemp/algorithms/*`
