"""Stable public API for the package."""

from __future__ import annotations

import numpy as np

from .algorithms import FAMILY_REGISTRIES
from .algorithms.emissivity import emissivity_registry
from .algorithms.single_channel import single_channel_registry
from .algorithms.split_window import split_window_registry
from .algorithms.thermal import (
    brightness_band_10,
    brightness_band_11,
)
from .algorithms.spectral_index import ndvi as _ndvi
from .algorithms.spectral_index import spectral_index_registry
from .algorithms.water_vapor import water_vapor_registry
from .exceptions import InputShapesNotEqual
from .references import ORIGINAL_LIBRARY_CREDIT
from .validation import (
    build_mask_from,
    ensure_same_shape,
    normalize_temperature_unit,
    to_float_array,
)

CELSIUS_SCALER = 273.15
SINGLE_CHANNEL_EMISSIVITY_METHODS = {"avdan-2016"}


def _normalize_thermal_band(band) -> str:
    """
    Normalize supported thermal band identifiers.

    Parameters
    ----------
    band : str or int
        Thermal band identifier or alias.

    Returns
    -------
    str
        Canonical band key, either ``"band_10"`` or ``"band_11"``.

    Raises
    ------
    ValueError
        If the band identifier is not supported.
    """

    aliases = {
        10: "band_10",
        "10": "band_10",
        "band_10": "band_10",
        "b10": "band_10",
        11: "band_11",
        "11": "band_11",
        "band_11": "band_11",
        "b11": "band_11",
    }
    try:
        return aliases[band]
    except KeyError as exc:
        raise ValueError("band must be 'band_10' or 'band_11'.") from exc


def spectral_index(index: str, **kwargs):
    """
    Compute a spectral index selected by name.

    This dispatcher routes the request to one of the registered spectral
    index algorithms, such as NDVI or EVI.

    Parameters
    ----------
    index : str
        Name of the spectral index to compute. Currently supported values
        include `"ndvi"` and `"evi"`.
    **kwargs
        Input bands and optional parameters required by the selected index.
        For `index="ndvi"`, provide `nir` and `red`. For `index="evi"`,
        provide `nir`, `red`, and `blue`.

    Returns
    -------
    numpy.ndarray
        Array containing the computed spectral index values.

    Notes
    -----
    - Input arrays must have the same shape and spatial alignment.
    - Use reflectance-like optical bands for physically meaningful results.
    - A boolean `mask` can be passed to mark invalid pixels as `NaN`.

    Examples
    --------
    >>> from pylstemp import spectral_index
    >>> ndvi = spectral_index(index="ndvi", nir=nir, red=red)
    >>> evi = spectral_index(index="evi", nir=nir, red=red, blue=blue)
    """

    return spectral_index_registry.create(index)(**kwargs)


def brightness(
    thermal_band,
    band: str,
    sensor: str,
    rad_gain: float | None = None,
    rad_bias: float | None = None,
    mask=None,
) -> np.ndarray:
    """
    Compute brightness temperature for a selected Landsat thermal band.

    This function converts a thermal band image to top-of-atmosphere
    brightness temperature using the selected Landsat sensor constants
    and radiance rescaling coefficients.

    Parameters
    ----------
    thermal_band : array-like
        Thermal band image to convert. Use the band 10 array when
        `band="band_10"` and the band 11 array when `band="band_11"`.
    band : str
        Thermal band identifier. Supported values are `"band_10"` and
        `"band_11"`. Short aliases such as `"10"`, `"11"`, `"b10"` and
        `"b11"` are also accepted.
    sensor : str
        Landsat sensor name. Supported values are `"landsat_8"` and
        `"landsat_9"`.
    rad_gain : float, optional
        Radiance multiplicative rescaling factor. This corresponds to
        `RADIANCE_MULT_BAND_X` in the scene metadata. If omitted, the
        default value registered for the selected sensor and band is used.
    rad_bias : float, optional
        Radiance additive rescaling factor. This corresponds to
        `RADIANCE_ADD_BAND_X` in the scene metadata. If omitted, the
        default value registered for the selected sensor and band is used.
    mask : array-like of bool, optional
        Boolean mask where True values indicate invalid pixels
        (e.g., nodata, clouds, shadows, or saturated pixels).

    Returns
    -------
    numpy.ndarray
        Array containing brightness temperature values in Kelvin.

    Notes
    -----
    - Input arrays should be radiometrically consistent with the selected
      Landsat sensor and band.
    - `rad_gain` and `rad_bias` are different from the thermal constants
      `K1` and `K2`; `K1` and `K2` are selected internally from the sensor
      metadata.
    - It is recommended to apply quality masks before using the result in
      land surface temperature workflows.

    Examples
    --------
    >>> from pylstemp import brightness
    >>> brightness_10 = brightness(
    ...     thermal_band=band_10,
    ...     band="band_10",
    ...     sensor="landsat_8",
    ... )
    >>> brightness_11 = brightness(
    ...     thermal_band=band_11,
    ...     band="band_11",
    ...     sensor="landsat_8",
    ...     rad_gain=0.0003342,
    ...     rad_bias=0.1,
    ... )
    """

    normalized_band = _normalize_thermal_band(band)
    if normalized_band == "band_10":
        return brightness_band_10(
            thermal_band,
            sensor=sensor,
            rad_gain=rad_gain,
            rad_bias=rad_bias,
            mask=mask,
        )
    return brightness_band_11(
        thermal_band,
        sensor=sensor,
        rad_gain=rad_gain,
        rad_bias=rad_bias,
        mask=mask,
    )


def _emissivity_pair(ndvi_image, band_4_red=None, emissivity_method: str = "avdan-2016"):
    """
    Compute Band 10 and Band 11 emissivity from NDVI.

    Parameters
    ----------
    ndvi_image : array-like
        NDVI image used by the emissivity method.
    band_4_red : array-like, optional
        Red band image required by selected methods.
    emissivity_method : str, default="avdan-2016"
        Registered emissivity method key.

    Returns
    -------
    tuple of ndarray
        Emissivity arrays for Band 10 and Band 11.
    """
    ndvi_array = to_float_array("ndvi_image", ndvi_image)
    validated_red_band = None if band_4_red is None else to_float_array("band_4_red", band_4_red)
    ensure_same_shape(ndvi_image=ndvi_array, band_4_red=validated_red_band)

    algorithm = emissivity_registry.create(emissivity_method)
    return algorithm(ndvi=ndvi_array, red_band=validated_red_band)


def emissivity_band_10(ndvi_image, band_4_red=None, emissivity_method: str = "avdan-2016"):
    """
    Compute emissivity for the Band 10 thermal workflow.

    Parameters
    ----------
    ndvi_image : array-like
        NDVI image used by the emissivity method.
    band_4_red : array-like, optional
        Red band image required by selected methods.
    emissivity_method : str, default="avdan-2016"
        Registered emissivity method key.

    Returns
    -------
    ndarray
        Band 10 emissivity image.
    """

    emissivity_10, _ = _emissivity_pair(
        ndvi_image,
        band_4_red=band_4_red,
        emissivity_method=emissivity_method,
    )
    return emissivity_10


def emissivity_band_11(ndvi_image, band_4_red=None, emissivity_method: str = "avdan-2016"):
    """
    Compute emissivity for the Band 11 thermal workflow.

    Parameters
    ----------
    ndvi_image : array-like
        NDVI image used by the emissivity method.
    band_4_red : array-like, optional
        Red band image required by selected methods.
    emissivity_method : str, default="avdan-2016"
        Registered emissivity method key.

    Returns
    -------
    ndarray
        Band 11 emissivity image.
    """

    _, emissivity_11 = _emissivity_pair(
        ndvi_image,
        band_4_red=band_4_red,
        emissivity_method=emissivity_method,
    )
    return emissivity_11


def emissivity(ndvi_image, band: str, band_4_red=None, emissivity_method: str = "avdan-2016"):
    """
    Compute land surface emissivity for a selected thermal band workflow.

    This function computes emissivity from a precomputed NDVI image using
    one of the registered emissivity methods.

    Parameters
    ----------
    ndvi_image : array-like
        NDVI image used by the emissivity method.
    band : str
        Thermal workflow band. Supported values are `"band_10"` and
        `"band_11"`. Short aliases such as `"10"`, `"11"`, `"b10"` and
        `"b11"` are also accepted.
    band_4_red : array-like, optional
        Red band image. Required by methods that estimate soil emissivity
        from the red band, such as `"xiaolei-2014"`.
    emissivity_method : str, default="avdan-2016"
        Name of the emissivity method to use.

    Returns
    -------
    numpy.ndarray
        Emissivity array for the selected thermal band workflow.

    Notes
    -----
    - `avdan-2016` is intended for the single-channel workflow and returns
      the same emissivity for band 10 and band 11.
    - For split-window workflows, prefer band-specific methods such as
      `"gopinadh-2018"` or `"xiaolei-2014"`.
    - Input arrays must have the same shape and spatial alignment.

    Examples
    --------
    >>> from pylstemp import emissivity
    >>> emissivity_10 = emissivity(
    ...     ndvi_image,
    ...     band="band_10",
    ...     band_4_red=red,
    ...     emissivity_method="avdan-2016",
    ... )
    """

    normalized_band = _normalize_thermal_band(band)
    if normalized_band == "band_10":
        return emissivity_band_10(
            ndvi_image,
            band_4_red=band_4_red,
            emissivity_method=emissivity_method,
        )
    return emissivity_band_11(
        ndvi_image,
        band_4_red=band_4_red,
        emissivity_method=emissivity_method,
    )


def single_window(
    brightness_band_10,
    band_4_red,
    band_5_nir,
    lst_method: str = "mono-window-2016",
    emissivity_method: str = "avdan-2016",
    unit: str = "kelvin",
) -> np.ndarray:
    """
    Compute land surface temperature using a single-channel method.

    This workflow expects brightness temperature for thermal band 10 to be
    computed beforehand with `brightness(..., band="band_10")`.

    Parameters
    ----------
    brightness_band_10 : array-like
        Brightness temperature image for thermal band 10, in Kelvin.
    band_4_red : array-like
        Red band image used to compute NDVI internally.
    band_5_nir : array-like
        Near-infrared band image used to compute NDVI internally.
    lst_method : str, default="mono-window-2016"
        Single-channel LST method to use.
    emissivity_method : str, default="avdan-2016"
        Emissivity method used before LST computation.
    unit : {"kelvin", "celsius", "celcius"}, default="kelvin"
        Output temperature unit. The misspelling `"celcius"` is accepted
        for backward compatibility and normalized to `"celsius"`.

    Returns
    -------
    numpy.ndarray
        Land surface temperature image in the requested unit.

    Notes
    -----
    - Input arrays must have the same shape and spatial alignment.
    - Zero and `NaN` values in the brightness image are masked internally.
    - The default mono-window method is a band 10 workflow.

    Examples
    --------
    >>> from pylstemp import single_window
    >>> lst = single_window(
    ...     brightness_band_10=brightness_10,
    ...     band_4_red=red,
    ...     band_5_nir=nir,
    ...     lst_method="mono-window-2016",
    ...     unit="celsius",
    ... )
    """
    normalized_unit = normalize_temperature_unit(unit)

    brightness_10 = to_float_array("brightness_band_10", brightness_band_10)
    red = to_float_array("band_4_red", band_4_red)
    nir = to_float_array("band_5_nir", band_5_nir)
    ensure_same_shape(
        brightness_band_10=brightness_10,
        band_4_red=red,
        band_5_nir=nir,
    )

    mask = build_mask_from(brightness_10)
    ndvi_image = _ndvi(nir=nir, red=red, mask=mask)
    emissivity_10 = emissivity_band_10(ndvi_image, band_4_red=red, emissivity_method=emissivity_method)

    result = single_channel_registry.create(lst_method)(
        emissivity_10=emissivity_10,
        brightness_temperature_10=brightness_10,
        mask=mask,
    )
    return result if normalized_unit == "kelvin" else result - CELSIUS_SCALER


def split_window(
    brightness_band_10,
    brightness_band_11,
    band_4_red,
    band_5_nir,
    lst_method: str,
    emissivity_method: str = "gopinadh-2018",
    unit: str = "kelvin",
    water_vapor: float | np.ndarray | None = None,
) -> np.ndarray:
    """
    Compute land surface temperature using a split-window method.

    This workflow expects brightness temperature for thermal bands 10 and 11
    to be computed beforehand with `brightness(...)`.

    Parameters
    ----------
    brightness_band_10 : array-like
        Brightness temperature image for thermal band 10, in Kelvin.
    brightness_band_11 : array-like
        Brightness temperature image for thermal band 11, in Kelvin.
    band_4_red : array-like
        Red band image used to compute NDVI internally.
    band_5_nir : array-like
        Near-infrared band image used to compute NDVI internally.
    lst_method : str
        Split-window LST method to use, such as `"du-2015"`,
        `"jimenez-munoz-2014"`, `"sobrino-1993"`, `"kerr-1992"`, or
        `"price-1984"`.
    emissivity_method : str, default="gopinadh-2018"
        Emissivity method used before LST computation.
    unit : {"kelvin", "celsius", "celcius"}, default="kelvin"
        Output temperature unit. The misspelling `"celcius"` is accepted
        for backward compatibility and normalized to `"celsius"`.
    water_vapor : float or array-like, optional
        Atmospheric column water vapor in g/cm2. Required by
        `"jimenez-munoz-2014"` and optional for `"du-2015"`.

    Returns
    -------
    numpy.ndarray
        Land surface temperature image in the requested unit.

    Notes
    -----
    - Input arrays must have the same shape and spatial alignment.
    - `avdan-2016` is blocked for split-window workflows because it is a
      single-channel emissivity method.
    - `water_vapor` can be a single scene-level value or a raster, depending
      on the selected method.

    Examples
    --------
    >>> from pylstemp import split_window
    >>> lst = split_window(
    ...     brightness_band_10=brightness_10,
    ...     brightness_band_11=brightness_11,
    ...     band_4_red=red,
    ...     band_5_nir=nir,
    ...     lst_method="du-2015",
    ...     emissivity_method="gopinadh-2018",
    ...     unit="celsius",
    ... )
    """
    normalized_unit = normalize_temperature_unit(unit)
    if emissivity_method in SINGLE_CHANNEL_EMISSIVITY_METHODS:
        raise ValueError(
            f"'{emissivity_method}' is a single-channel emissivity method and should not be used "
            "with split_window(). Use a band-specific emissivity method such as "
            "'gopinadh-2018' or 'xiaolei-2014'."
        )

    brightness_10 = to_float_array("brightness_band_10", brightness_band_10)
    brightness_11 = to_float_array("brightness_band_11", brightness_band_11)
    red = to_float_array("band_4_red", band_4_red)
    nir = to_float_array("band_5_nir", band_5_nir)
    ensure_same_shape(
        brightness_band_10=brightness_10,
        brightness_band_11=brightness_11,
        band_4_red=red,
        band_5_nir=nir,
    )

    mask = build_mask_from(brightness_10)
    ndvi_image = _ndvi(nir=nir, red=red, mask=mask)
    emissivity_10 = emissivity_band_10(ndvi_image, band_4_red=red, emissivity_method=emissivity_method)
    emissivity_11 = emissivity_band_11(ndvi_image, band_4_red=red, emissivity_method=emissivity_method)

    if brightness_11 is None or emissivity_11 is None:
        raise InputShapesNotEqual(
            "Split-window computation requires both band 11 brightness temperature "
            "and band 11 emissivity."
        )

    result = split_window_registry.create(lst_method)(
        emissivity_10=emissivity_10,
        emissivity_11=emissivity_11,
        brightness_temperature_10=brightness_10,
        brightness_temperature_11=brightness_11,
        ndvi=ndvi_image,
        mask=mask,
        water_vapor=water_vapor,
    )
    return result if normalized_unit == "kelvin" else result - CELSIUS_SCALER


def water_vapor(
    brightness_band_10,
    brightness_band_11,
    ndvi_image,
    method: str = "wang-2015",
    window_size: int = 5,
    group_count: int = 5,
) -> np.ndarray:
    """
    Estimate precipitable water vapor using the selected method.

    Currently, this dispatcher supports the Wang et al. (2015) NDVI-based
    method for estimating precipitable water vapor from Landsat TIRS
    brightness temperature bands.

    Parameters
    ----------
    brightness_band_10 : array-like
        Brightness temperature image for thermal band 10.
    brightness_band_11 : array-like
        Brightness temperature image for thermal band 11.
    ndvi_image : array-like
        NDVI image spatially aligned with the brightness temperature arrays.
    method : str, default="wang-2015"
        Water vapor retrieval method.
    window_size : int, default=5
        Moving-window size in pixels. Must be an odd integer greater than or
        equal to 3. For example, `5` means a 5 by 5 local window.
    group_count : int, default=5
        Number of NDVI-based local groups used by the Wang et al. method.

    Returns
    -------
    numpy.ndarray
        Estimated precipitable water vapor image in g/cm2.

    Notes
    -----
    - Input arrays must have the same shape and spatial alignment.
    - Larger windows may produce smoother estimates; smaller windows are more
      locally sensitive.
    - The resulting raster can be passed to `split_window(...,
      lst_method="jimenez-munoz-2014", water_vapor=...)`.

    Examples
    --------
    >>> from pylstemp import water_vapor
    >>> water = water_vapor(
    ...     brightness_band_10=brightness_10,
    ...     brightness_band_11=brightness_11,
    ...     ndvi_image=ndvi,
    ...     method="wang-2015",
    ... )
    """

    return water_vapor_registry.create(method)(
        brightness_band_10=brightness_band_10,
        brightness_band_11=brightness_band_11,
        ndvi_image=ndvi_image,
        window_size=window_size,
        group_count=group_count,
    )


def list_algorithms() -> dict[str, dict[str, dict[str, str]]]:
    """
    Return metadata for all registered algorithm families and methods.

    Returns
    -------
    dict
        Catalog containing each algorithm family, method key, display name,
        reference, citation, and original-library credit.

    Examples
    --------
    >>> from pylstemp import list_algorithms
    >>> catalog = list_algorithms()
    >>> catalog["spectral_index"].keys()
    dict_keys(['evi', 'ndvi'])
    """
    catalog = {"credit": {"original_library": ORIGINAL_LIBRARY_CREDIT}}

    for family_name, registry in FAMILY_REGISTRIES.items():
        catalog[family_name] = {
            key: {
                "name": metadata.name,
                "reference": metadata.reference,
                "citation": metadata.citation,
            }
            for key, metadata in registry.describe().items()
        }

    return catalog
