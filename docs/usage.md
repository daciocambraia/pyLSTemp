# Usage Guide

This guide shows the main workflows exposed by the public API.

## Import the public functions

```python
from pylstemp import (
    ndvi,
    brightness_temperature_band_10,
    brightness_temperature_band_11,
    emissivity,
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

red_band = np.array([[0.2, 0.3], [0.4, 0.5]])
nir_band = np.array([[0.6, 0.7], [0.8, 0.9]])

ndvi_image = ndvi(nir_band, red_band)
```

## 2. Compute brightness temperature

```python
import numpy as np
from pylstemp import brightness_temperature_band_10, brightness_temperature_band_11

band_10 = np.full((3, 3), 1000.0)
band_11 = np.full((3, 3), 900.0)
sensor = "landsat_8"

brightness_10 = brightness_temperature_band_10(
    band_10,
    sensor=sensor,
)

brightness_11 = brightness_temperature_band_11(
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
    red_band=red_band,
    emissivity_method="avdan",
)

emissivity_11 = emissivity_band_11(
    ndvi_image,
    red_band=red_band,
    emissivity_method="avdan",
)
```

## 4. Compute single-channel LST

```python
from pylstemp import single_window

lst_single = single_window(
    brightness_temperature_10=brightness_10,
    red_band=red_band,
    nir_band=nir_band,
    lst_method="mono-window",
    emissivity_method="avdan",
    unit="kelvin",
)
```

## 5. Compute split-window LST

```python
from pylstemp import split_window

lst_split = split_window(
    brightness_temperature_10=brightness_10,
    brightness_temperature_11=brightness_11,
    red_band=red_band,
    nir_band=nir_band,
    lst_method="jiminez-munoz",
    emissivity_method="avdan",
    unit="celsius",
)
```

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
- manual masks passed to `ndvi()` or `brightness_temperature()` must be boolean
- `sensor` must be `landsat_8` or `landsat_9`
- `rad_gain` and `rad_bias` default to the sensor metadata values and can be overridden manually in the brightness temperature function call
- these radiance values are different from the sensor constants `K1` and `K2`
