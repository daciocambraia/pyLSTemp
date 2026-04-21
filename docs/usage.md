# Usage Guide

This guide shows the main workflows exposed by the public API.

## Import the public functions

```python
from pylstemp import (
    ndvi,
    brightness_band_10,
    brightness_band_11,
    emissivity_band_10,
    emissivity_band_11,
    single_window,
    split_window,
    list_algorithms,
)
```

## 1. Compute NDVI

```python
import numpy as np
from pylstemp import ndvi

band_4_red = np.array([[0.2, 0.3], [0.4, 0.5]])
band_5_nir = np.array([[0.6, 0.7], [0.8, 0.9]])

ndvi_image = ndvi(band_5_nir, band_4_red)
```

## 2. Compute brightness temperature

```python
import numpy as np
from pylstemp import brightness_band_10, brightness_band_11

band_10 = np.full((3, 3), 1000.0)
band_11 = np.full((3, 3), 900.0)
sensor = "landsat_8"

brightness_10 = brightness_band_10(
    band_10,
    sensor=sensor,
)

brightness_11 = brightness_band_11(
    band_11,
    sensor=sensor,
)
```

To override the default sensor metadata values, pass `rad_gain=` and `rad_bias=` explicitly.

## 3. Compute emissivity

```python
from pylstemp import emissivity_band_10, emissivity_band_11

emissivity_10 = emissivity_band_10(
    ndvi_image,
    band_4_red=band_4_red,
    emissivity_method="avdan-2016",
)

emissivity_11 = emissivity_band_11(
    ndvi_image,
    band_4_red=band_4_red,
    emissivity_method="avdan-2016",
)
```

`avdan-2016` follows the NDVI conditional emissivity rules from Avdan and Jovanovska: water, soil, mixed pixels using fractional vegetation cover plus `C=0.005`, and vegetation. Because this source method is single-channel, it returns the same emissivity for band 10 and band 11 workflows. For split-window methods, consider `gopinadh-2018` or `xiaolei-2014` when you want band-specific emissivity.

## 4. Compute single-channel LST

```python
from pylstemp import single_window

lst_single = single_window(
    brightness_band_10=brightness_10,
    band_4_red=band_4_red,
    band_5_nir=band_5_nir,
    lst_method="mono-window-2016",
    emissivity_method="avdan-2016",
    unit="kelvin",
)
```

The default `mono-window-2016` method uses `lambda=10.895e-6 m`, the midpoint of the Landsat 8/9 TIRS Band 10 range (`10.6-11.19 um`). This avoids using the Band 11 lower wavelength (`11.5 um`) in a Band 10 single-channel workflow.
Use only `brightness_band_10` with `mono-window-2016`; do not use Band 11 brightness temperature in this workflow.

## 5. Compute split-window LST

```python
from pylstemp import split_window

lst_split = split_window(
    brightness_band_10=brightness_10,
    brightness_band_11=brightness_11,
    band_4_red=band_4_red,
    band_5_nir=band_5_nir,
    lst_method="du-2015",
    emissivity_method="gopinadh-2018",
    unit="celsius",
)
```

`split_window(...)` blocks `emissivity_method="avdan-2016"` because Avdan is a single-channel emissivity method. Use `gopinadh-2018` or `xiaolei-2014` for split-window workflows.

Only `lst_method="du-2015"` uses `water_vapor`. It is optional; if omitted, the method uses the general Du et al. coefficient range `[0.0, 6.3] g/cm2`.

```python
lst_du = split_window(
    brightness_band_10=brightness_10,
    brightness_band_11=brightness_11,
    band_4_red=band_4_red,
    band_5_nir=band_5_nir,
    lst_method="du-2015",
    emissivity_method="gopinadh-2018",
    water_vapor=3.8,
)
```

Use `water_vapor` in `g/cm2` when you have an atmospheric column water vapor estimate and want the method to select the corresponding Du et al. coefficient sub-range.

## 6. Inspect available families and methods

```python
from pylstemp import list_algorithms

catalog = list_algorithms()
print(catalog.keys())
print(catalog["split_window"].keys())
```

## Notes on invalid pixels

- zero values are treated as invalid in the thermal workflow mask
- `NaN` values are propagated through the calculations
- manual masks passed to `ndvi()`, `brightness_band_10()` or `brightness_band_11()` must be boolean
- `sensor` must be `landsat_8` or `landsat_9`
- `rad_gain` and `rad_bias` default to the sensor metadata values and can be overridden manually in the brightness temperature function call
- these radiance values are different from the sensor constants `K1` and `K2`
