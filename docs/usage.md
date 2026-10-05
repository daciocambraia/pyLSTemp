# Usage Guide

This guide shows the main workflows exposed by the public API.

## Import the public functions

```python
from pylstemp import (
    spectral_index,
    brightness,
    emissivity,
    water_vapor,
    single_window,
    split_window,
    list_algorithms,
    toa_radiance,
    toa_reflectance,
    read_mtl,
)
```

## 1. Compute NDVI

```python
import numpy as np
from pylstemp import spectral_index

# Synthetic MTL and DN for an executable example. For real scenes use:
# metadata = read_mtl("path/to/SCENE_MTL.txt")
metadata = dict(PROCESSING_LEVEL="L1TP", SPACECRAFT_ID="LANDSAT_8",
    SUN_ELEVATION=30, RADIANCE_MULT_BAND_4=.007425383,
    RADIANCE_ADD_BAND_4=-37.126915, RADIANCE_MULT_BAND_5=.005048835,
    RADIANCE_ADD_BAND_5=-25.244175, REFLECTANCE_MULT_BAND_4=.00002,
    REFLECTANCE_ADD_BAND_4=-.1,
    RADIANCE_MULT_BAND_10=.0003342, RADIANCE_ADD_BAND_10=.1,
    RADIANCE_MULT_BAND_11=.0003342, RADIANCE_ADD_BAND_11=.1,
    K1_CONSTANT_BAND_10=774.8853, K2_CONSTANT_BAND_10=1321.0789,
    K1_CONSTANT_BAND_11=480.8883, K2_CONSTANT_BAND_11=1201.1442)
red_dn = np.array([[20000., 22000.], [24000., 26000.]])
nir_dn = np.array([[30000., 33000.], [36000., 39000.]])
red = toa_radiance(red_dn, metadata=metadata, band=4)
nir = toa_radiance(nir_dn, metadata=metadata, band=5)
ndvi_image = spectral_index(index="ndvi", nir=nir, red=red)
# Optional dimensionless TOA reflectance, outside the default radiance workflow:
red_toa_reflectance = toa_reflectance(red_dn, metadata=metadata, band=4)
```

## 2. Compute brightness temperature

```python
import numpy as np
from pylstemp import brightness

band_10_dn = np.full((2, 2), 20000.0)
band_11_dn = np.full((2, 2), 20000.0)
radiance_10 = toa_radiance(band_10_dn, metadata=metadata, band=10)
radiance_11 = toa_radiance(band_11_dn, metadata=metadata, band=11)
brightness_10 = brightness(radiance_10, band=10, metadata=metadata)
brightness_11 = brightness(radiance_11, band=11, metadata=metadata)
```

`brightness` lives in `pylstemp.calibration` and remains exported at the package root.
Its default input is TOA radiance in W m-2 sr-1 um-1; the output is TOA BT in K.
It matches the [USGS Level-1 equation](https://www.usgs.gov/landsat-missions/using-usgs-landsat-level-1-data-product).
It does not correct emissivity or atmospheric effects. Prefer the matching MTL.
For the former DN shortcut set `input_quantity="dn"` explicitly. Without MTL,
`sensor=` selects fallback constants and `rad_gain`/`rad_bias` can override defaults.
Those overrides are rejected for radiance input to prevent double calibration.

## 3. Compute emissivity

```python
from pylstemp import emissivity

emissivity_10 = emissivity(
    ndvi_image,
    band="band_10",
    band_4_red=red,
    emissivity_method="avdan-2016",
)

emissivity_11 = emissivity(
    ndvi_image,
    band="band_11",
    band_4_red=red,
    emissivity_method="avdan-2016",
)
```

`avdan-2016` follows the NDVI conditional emissivity rules from Avdan and Jovanovska: water, soil, mixed pixels using fractional vegetation cover plus `C=0.005`, and vegetation. Because this source method is single-channel, it returns the same emissivity for band 10 and band 11 workflows. For split-window methods, consider `gopinadh-2018` when you want band-specific emissivity.

## 4. Compute single-channel LST

```python
from pylstemp import single_window

lst_single = single_window(
    brightness_band_10=brightness_10,
    band_4_red=red,
    band_5_nir=nir,
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
    band_4_red=red,
    band_5_nir=nir,
    lst_method="du-2015",
    emissivity_method="gopinadh-2018",
    unit="celsius",
)
```

`split_window(...)` blocks `emissivity_method="avdan-2016"` because Avdan is a single-channel emissivity method. Use `gopinadh-2018` for split-window workflows. `gopinadh-2018` uses Rongali et al.'s linear fractional vegetation cover with `NDVIsoil=0.15` and `NDVIvegetation=0.48`; the FVC is clipped to `0..1` before the linear emissivity mixture.

`lst_method="du-2015"` can use a single scene-level `water_vapor` value, but it is optional; if omitted, the method uses the general Du et al. coefficient range `[0.0, 6.3] g/cm2`.
When the supplied value falls inside one of Du et al.'s overlapping CWV ranges, the method computes both adjacent estimates and returns their mean.
`lst_method="jimenez-munoz-2014"` requires `water_vapor` and accepts either a single value or a raster with the same shape as the brightness temperature arrays.

```python
lst_du = split_window(
    brightness_band_10=brightness_10,
    brightness_band_11=brightness_11,
    band_4_red=red,
    band_5_nir=nir,
    lst_method="du-2015",
    emissivity_method="gopinadh-2018",
    water_vapor=3.8,
)
```

Use `water_vapor` in `g/cm2` when you have an atmospheric column water vapor estimate and want the method to select the corresponding Du et al. coefficient sub-range.

## 6. Estimate water vapor from Landsat 8 imagery

```python
from pylstemp import water_vapor

water = water_vapor(
    brightness_band_10=brightness_10,
    brightness_band_11=brightness_11,
    ndvi_image=ndvi_image,
    method="wang-2015",
    window_size=21,
    group_count=3,
)
```

`wang-2015` estimates precipitable water vapor from Landsat 8 TIRS bands 10 and 11 using NDVI-based local grouping. The result is a raster and can be passed directly to `jimenez-munoz-2014` for pixel-by-pixel correction.

```python
lst_jimenez = split_window(
    brightness_band_10=brightness_10,
    brightness_band_11=brightness_11,
    band_4_red=red,
    band_5_nir=nir,
    lst_method="jimenez-munoz-2014",
    emissivity_method="gopinadh-2018",
    water_vapor=water,
)
```

## 7. Inspect available families and methods

```python
from pylstemp import list_algorithms

catalog = list_algorithms()
print(catalog.keys())
print(catalog["split_window"].keys())
print(catalog["water_vapor"].keys())
```

## Notes on invalid pixels

- zero values are treated as invalid in the thermal workflow mask
- `NaN` values are propagated through the calculations
- manual masks passed to `spectral_index(index="ndvi", ...)` or `brightness(...)` must be boolean
- `sensor` must be `landsat_8` or `landsat_9`
- DN gain/bias overrides apply only to `input_quantity="dn"` without MTL; metadata is authoritative when supplied
- gain/bias calibrate DN to radiance; `K1` and `K2` convert radiance to BT

## Scientific contracts and real scenes

NDVI accepts calibrated radiance or reflectance; preserve the input quantity
and check that emissivity/land-cover thresholds match its intended use.
The supplied scene examples use Level-1 TOA radiance. EVI was removed because
it is not used by the retained retrieval methods. Xiaolei is not available; emissivity methods are
avdan-2016 and gopinadh-2018.
Use pylstemp.calibration.read_mtl, toa_radiance, toa_reflectance and brightness for Level-1 calibration.
LandsatScene.calibrated() defaults to optical_quantity="radiance". Select "reflectance" explicitly
for TOA reflectance with per-pixel SZA (or MTL solar elevation). QA applies in both modes.
B4/B5/B10/B11, MTL and QA are required; B2 is optional.
Both LST workflows and water_vapor accept keyword-only mask=.
Wang supports ndvi_range=(scene_min,scene_max) and chunk_rows=. External tiles require halo pixels.
Nonfinite/negative PWV pixels are masked, scalar negative PWV is rejected.
See [scientific-methods.md](scientific-methods.md) for source decisions and limits.
