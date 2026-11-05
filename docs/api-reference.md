# API Reference

The package exposes one function per retrieval/correction family. Sobrino is
selected through `emissivity(method=...)`; Chavez through `optical_correction`.
Prepared emissivity is accepted by `single_window` and `split_window`, using
keyword-only inputs. It is recommended when emissivity has already been
calculated; optical-input routes remain available as alternatives.
NDVI is internal; there is no spectral-index API or empty reserved family.

The [method notebooks](../exemple/README.md) document the applicable parameters,
unit, default and method-specific option, with executable examples.
[Method cards](method-cards.md) retain the equations and scientific decisions.

## Public functions

### `read_mtl`

```text
read_mtl(path)
```

Read the matching Landsat8/9 MTL. Level1 calibration uses its actual band coefficients.

### `toa_radiance`

```text
toa_radiance(dn, *, metadata, band, mask=None)
```

Level1 DN -> TOA radiance [W m-2 sr-1 um-1], bands1..11, matching MTL gain/bias; no solar correction.

### `toa_reflectance`

```text
toa_reflectance(dn, *, metadata, band, mask=None, sun_elevation=None)
```

Level1 optical DN -> TOA reflectance [dimensionless], bands1..9. Solar elevation in (0,90] degrees, scalar or aligned raster. This is not surface reflectance.

### `brightness`

```text
brightness(thermal_band, band, sensor=None, rad_gain=None, rad_bias=None, mask=None, *, metadata=None, input_quantity='radiance')
```

TOA radiance [W m-2 sr-1 um-1] -> BT [K]. Explicit input_quantity="dn" enables Level1 calibration first. Matching MTL is preferred; sensor constants are a fallback, without implying validity of LST coefficient transfer.

### `emissivity`

```text
emissivity(ndvi_image=None, band=None, band_4_red=None, emissivity_method=None, *, method=None, red=None, nir=None, mask=None)
```

Select method="avdan-2016" (default) or "rongali-2018". Supply red/nir for internal NDVI or ndvi_image instead. Output is dimensionless. The default thermal band is band10. The legacy emissivity_method keyword remains an alternative to method, never combined with it.

### `single_window`

```text
single_window(brightness_band_10, band_4_red=None, band_5_nir=None, lst_method='mono-window-2016', emissivity_method=None, unit='kelvin', *, emissivity_10=None, mask=None, radiance_band_10=None, water_vapor=None, return_diagnostics=False, optical_quantity=None)
```

BT10 [K] + prepared emissivity_10 [dimensionless, (0,1]] is the recommended route for reuse. Omit band_4_red, band_5_nir and emissivity_method in that route. Alternatively, supply calibrated red/nir and select emissivity_method (avdan-2016 or rongali-2018); None defaults to Avdan in the optical route only. Conflicting or incomplete routes are rejected. mono-window-2016 (default) uses emissivity correction only. jimenez-munoz-2014-sc also requires matching radiance_band_10 and PWV [0,3] g/cm2. unit selects kelvin/celsius. return_diagnostics=True returns lst, ndvi (None with prepared emissivity), emissivity_10, invalid_mask, units and optical_contract. PWV is supplied explicitly, not estimated internally.

### `split_window`

```text
split_window(brightness_band_10, brightness_band_11, band_4_red=None, band_5_nir=None, lst_method=None, emissivity_method=None, unit='kelvin', water_vapor=None, *, emissivity_10=None, emissivity_11=None, ndvi_image=None, mask=None, return_diagnostics=False, optical_quantity=None, quality_mode='screened', pwv_quality_flags=None)
```

Choose lst_method explicitly. Supply calibrated band_4_red/band_5_nir OR a prepared aligned emissivity_10/emissivity_11 pair; partial pairs and conflicting routes are rejected. Prepared inputs omit emissivity_method; optical inputs default to rongali-2018. Kerr additionally requires optical bands for internal NDVI or ndvi_image, including with prepared emissivity. Other prepared routes reject unused optical/NDVI inputs. return_diagnostics=True returns lst, emissivity_10/11, ndvi (None if unavailable/unused), invalid_mask, units and optical_contract. Units are converted only at output.

### `water_vapor`

```text
water_vapor(brightness_band_10, brightness_band_11, ndvi_image=None, method: 'str' = 'wang-2015', window_size: 'int | None' = None, group_count: 'int' = 3, *, red=None, nir=None, mask=None, ndvi_range=None, chunk_rows=8, min_samples=10, quality_threshold=0.95, ndvi_filter=True, return_diagnostics=False) -> 'np.ndarray | dict[str, np.ndarray]'
```

BT10/BT11 [K] with red/nir or prepared NDVI; aligned2D arrays. Wang uses window21, global NDVI groups and fixed r2>=.97; reuse full-scene ndvi_range between tiles. Ren uses window11 standalone and local NDVI screening; on usual30m delivery a declared window33 approximates1km support. Ren-only controls: min_samples10, quality_threshold.95, ndvi_filter=True and return_diagnostics. Its output domain is [.06,6.3] g/cm2; diagnostics include water_vapor, raw_water_vapor, ratio, chi_squared, sample_count, invalid_mask. ndvi_filter=False permits thermal-only mode.

### `optical_correction`

```text
optical_correction(toa_reflectance, *, method='chavez-cost', sun_elevation=None, mask=None, parameters=None, percentile=None, assumed_dark_surface=None, return_diagnostics=False)
```

Select chavez-dos or chavez-cost. Input is solar-angle-corrected TOA reflectance [0,1], not DN/radiance. Fit with a single scene sun_elevation [degrees], percentile=.01 and assumed_dark_surface=.01 defaults. return_diagnostics=True returns reflectance, parameters, method, units, invalid_mask. To reuse the fit on tiles, pass parameters, choose the same method, and omit fitting options. Corrected out-of-range values become NaN, not clipped. TM-to-OLI transfer is experimental; this is not automatic LaSRC correction.

### `list_algorithms`

```text
list_algorithms(*, include_inactive=False) -> 'dict[str, dict[str, dict[str, str]]]'
```

The catalog contains 14 available method selectors. All have workflow_status="active". The compatibility argument include_inactive does not add methods; removed methods cannot be called explicitly.

## Split-window method requirements

| Method | PWV and source conditions |
|---|---|
| du-2015 | Optional PWV [0,6.3] g/cm2; None uses all-CWV row. Inclusive overlapping intervals [0,2.5], [2,3.5], [3,4.5], [4,5.5], [5,6.3] average LST estimates. |
| jimenez-munoz-2014-sw | Required finite nonnegative scalar/raster PWV; source evaluated0..6, larger values extrapolate. |
| price-1984, sobrino-1993 | No PWV; explicit AVHRR adaptations, not Landsat-validated coefficients. |
| kerr-1992 | No PWV; source thresholds .11/.72 refer to atmospherically corrected NDVI. AVHRR-to-TIRS transfer remains an adaptation. |

Invalid/nonfinite scalars are rejected where domains are enforced; invalid raster pixels become NaN. No implicit filling or PWV fallback. Boolean masks and arrays must be aligned, without broadcasting.

## Calibration auxiliaries (`pylstemp.calibration`)

### `quality_mask`

```text
quality_mask(qa_pixel, qa_radsat=None, *, exclude_water=False)
```

Collection2 QA_PIXEL plus optional QA_RADSAT; True means rejected. exclude_water adds bit7 to the mask. Saturation B2/B4/B5 and terrain occlusion are optical/geometry screening, not thermal saturation bits.

### `surface_reflectance`

```text
surface_reflectance(dn, *, scale=2.75e-05, offset=-0.2, mask=None)
```

Scale an existing Collection2 Level2 SR_B* product: DN*.0000275-.2. This does not atmospherically correct Level1, replace QA screening or establish sensor-compatible NDVI thresholds.

### `brightness_from_mtl`

```text
brightness_from_mtl(dn, *, metadata, band, mask=None)
```

Level1 thermal DN -> BT[K], using the same MTL path as brightness(input_quantity="dn").

## Scene and workflows

`LandsatScene(folder, backend="auto")` requires aligned Level1 B4/B5/B10/B11, **QA_PIXEL and QA_RADSAT (both mandatory)** and exactly one matching MTL. B2/SZA are optional. Backends: auto/rasterio/pillow. Use as a context manager or call close().

`scene.read(token, window=None)` reads DN/QA. `scene.calibrated(window=None, exclude_water=False, optical_quantity="radiance")` returns optical bands, thermal BT[K] and invalid mask; reflectance selects TOA reflectance, not SR. `scene.write_geotiff(path, array, window=None, units="")` requires exact scene/window shape and writes aligned float32/NaN GeoTIFFs. Windows contain four integer bounds with exclusive ends.

```text
scene_ndvi_range(scene, *, optical_quantity='radiance', block_rows=256, mask=None)
```

```text
du_from_scene(scene, *, window=None, pwv_mode='general', pwv_method='wang-2015', emissivity_method='rongali-2018', optical_quantity='radiance', unit='kelvin', window_size=None, group_count=3, chunk_rows=8, ndvi_range=None, mask=None, pwv_options=None, diagnostics=False, hash_inputs=False)
```

Wang global scanning applies QA and the same whole-scene caller mask. Reuse the resulting bounds across tiles; Ren is local. Du modes are general, raster or mean; mean requires accepted PWV over the output window. The workflow reads the required halo automatically. Ren pwv_options may set min_samples/quality_threshold/ndvi_filter.

Diagnostics retain calibrated optical_red/optical_nir, bt10/bt11, internal ndvi and emissivity_10/11 in result.intermediates. result.export(scene, folder) writes these alongside normal products when requested. Provenance records versions, source/card digest, MTL checksum and coefficients, grid, masks, parameters and source conditions. hash_inputs=True adds full imagery SHA256; default size/mtime identify files without proving content identity.

For array diagnostics, optical_quantity declares radiance, reflectance/toa_reflectance, surface_reflectance or None (undeclared), without converting them. Ground accuracy and sensor-transfer validity are separate from numerical regression.


### Jimenez-Munoz method names

Use `jimenez-munoz-2014-sw` for split-window and `jimenez-munoz-2014-sc`
for single-channel: both place the SC/SW suffix after the year.
The previous selectors `jimenez-munoz-2014` (SW) and `jimenez-munoz-sc-2014`
(SC) remain accepted as compatibility aliases. Other method names, equations,
coefficients and units are unchanged.


### Evidence and applicability

Each catalog entry includes `numerical_evidence`, `empirical_accuracy` and
`evidence`. `evidence["landsat_8"]` and `evidence["landsat_9"]` distinguish source
coefficients, experimental transfers, caller-supplied band parameters and
MTL-based calibration. They do not establish scene accuracy. The same metadata
is shipped in the source cards; sensor identity cannot be inferred from arrays.

Price/Kerr/Sobrino1993 emit RuntimeWarning for the AVHRR-to-TIRS transfer.
Jimenez-Munoz SW emits RuntimeWarning for unmasked valid PWV >6 g/cm2, preserving
the extrapolated numerical result. See scientific-methods.md for source limits.


## Raw estimates and quality flags

See [diagnostic-quality.md](diagnostic-quality.md) for `quality_mode="diagnostic"`, returned arrays, propagation of PWV flags, and the explicit Du general-coefficient fallback.


## Quality inputs: scene reader versus array functions

LandsatScene automatically locates the two QA rasters using the product ID. Missing required QA files raise ValueError during scene opening; mismatched grids are rejected. calibrated() constructs the QA mask and passes it to calibration. Functions receiving prepared arrays do not read these files: use an aligned boolean mask when applying QA screening. All current examples read BOTH QA rasters with read_quality_mask() and combine the result with nodata before calling the method. The QA mask does not reproject inputs. Water exclusion is an additional explicit policy, disabled by default in calibrated().

## Explicit QA file inputs (public API)

```python
from pylstemp import read_quality_mask
mask = read_quality_mask(qa_pixel_path, qa_radsat_path,
                         reference_path=reference_path, exclude_water=False)
```

Both QA paths and reference_path are required. GeoTIFFs must match shape, CRS and transform. Returns bool, True = invalid, including QA nodata. Pass this mask combined with data nodata as mask= to calibration, optical_correction (before fitting), emissivity, water_vapor (before windows), single_window and split_window. No automatic reprojection, unit conversion or scene-identity inference. All 16 notebooks perform this step explicitly. `scene.quality_mask(window=None, exclude_water=False)` exposes the existing scene QA step independently; calibrated() calls it automatically. See [complete QA workflow](quality-inputs.md).
