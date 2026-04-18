# Usage Guide

This guide shows the main workflows exposed by the public API.

## Import the public functions

```python
from pylstemp import (
    ndvi,
    brightness_temperature,
    emissivity,
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
from pylstemp import brightness_temperature

band_10 = np.full((3, 3), 1000.0)
band_11 = np.full((3, 3), 900.0)
sensor = "landsat_8"
rad_gain_band_10 = 0.0003342
rad_bias_band_10 = 0.1
rad_gain_band_11 = 0.0003342
rad_bias_band_11 = 0.1

brightness_10, brightness_11 = brightness_temperature(
    band_10,
    sensor=sensor,
    rad_gain_band_10=rad_gain_band_10,
    rad_bias_band_10=rad_bias_band_10,
    landsat_band_11=band_11,
    rad_gain_band_11=rad_gain_band_11,
    rad_bias_band_11=rad_bias_band_11,
)
```

## 3. Compute emissivity

```python
from pylstemp import emissivity

emissivity_10, emissivity_11 = emissivity(
    ndvi_image,
    landsat_band_4=red_band,
    emissivity_method="avdan",
)
```

## 4. Compute single-channel LST

```python
from pylstemp import single_window

lst_single = single_window(
    brightness_temperature_10=brightness_10,
    landsat_band_4=red_band,
    landsat_band_5=nir_band,
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
    landsat_band_4=red_band,
    landsat_band_5=nir_band,
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
- `rad_gain_band_x` and `rad_bias_band_x` must be informed manually in the function call
- these radiance values are different from the sensor constants `K1` and `K2`
