# Usage Guide

This guide shows the main workflows supported by the package.

## Importing the public API

```python
from pylstemp import (
    ndvi,
    brightness_temperature,
    emissivity,
    single_window,
    split_window,
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

brightness_10, brightness_11 = brightness_temperature(band_10, band_11)
```

## 3. Compute emissivity

```python
from pylstemp import emissivity, ndvi

ndvi_image = ndvi(nir_band, red_band)
emissivity_10, emissivity_11 = emissivity(
    ndvi_image,
    landsat_band_4=red_band,
    emissivity_method="avdan",
)
```

## 4. Compute single-window LST

```python
from pylstemp import single_window

lst_single = single_window(
    landsat_band_10=band_10,
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
    landsat_band_10=band_10,
    landsat_band_11=band_11,
    landsat_band_4=red_band,
    landsat_band_5=nir_band,
    lst_method="jiminez-munoz",
    emissivity_method="avdan",
    unit="celsius",
)
```

## Notes on invalid pixels

- zero values are treated as invalid in the thermal workflow mask
- `NaN` values are propagated through the calculations
- if you pass a mask manually to `ndvi` or `brightness_temperature`, it must be boolean
