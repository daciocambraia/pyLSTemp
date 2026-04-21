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
from .algorithms.spectral_indices import ndvi as _ndvi
from .algorithms.spectral_indices import spectral_indices_registry
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


def spectral_indices(indice: str, **kwargs):
    """Compute a spectral index selected by name."""

    return spectral_indices_registry.create(indice)(**kwargs)


def _emissivity_pair(ndvi_image, band_4_red=None, emissivity_method: str = "avdan-2016"):
    """Compute emissivity pair from an NDVI image."""
    ndvi_array = to_float_array("ndvi_image", ndvi_image)
    validated_red_band = None if band_4_red is None else to_float_array("band_4_red", band_4_red)
    ensure_same_shape(ndvi_image=ndvi_array, band_4_red=validated_red_band)

    algorithm = emissivity_registry.create(emissivity_method)
    return algorithm(ndvi=ndvi_array, red_band=validated_red_band)


def emissivity_band_10(ndvi_image, band_4_red=None, emissivity_method: str = "avdan-2016"):
    """Compute emissivity for the thermal band 10 workflow."""

    emissivity_10, _ = _emissivity_pair(
        ndvi_image,
        band_4_red=band_4_red,
        emissivity_method=emissivity_method,
    )
    return emissivity_10


def emissivity_band_11(ndvi_image, band_4_red=None, emissivity_method: str = "avdan-2016"):
    """Compute emissivity for the thermal band 11 workflow."""

    _, emissivity_11 = _emissivity_pair(
        ndvi_image,
        band_4_red=band_4_red,
        emissivity_method=emissivity_method,
    )
    return emissivity_11


def single_window(
    brightness_band_10,
    band_4_red,
    band_5_nir,
    lst_method: str = "mono-window-2016",
    emissivity_method: str = "avdan-2016",
    unit: str = "kelvin",
) -> np.ndarray:
    """Compute land surface temperature using a single-channel method."""
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
    ndvi_image = _ndvi(nir, red, mask=mask)
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
    """Compute land surface temperature using a split-window method."""
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
    ndvi_image = _ndvi(nir, red, mask=mask)
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


def water_vapor_wang_2015(
    brightness_band_10,
    brightness_band_11,
    ndvi_image,
    window_size: int = 5,
    group_count: int = 5,
) -> np.ndarray:
    """Estimate precipitable water vapor with Wang et al. (2015)."""

    return water_vapor_registry.create("wang-2015")(
        brightness_band_10=brightness_band_10,
        brightness_band_11=brightness_band_11,
        ndvi_image=ndvi_image,
        window_size=window_size,
        group_count=group_count,
    )


def list_algorithms() -> dict[str, dict[str, dict[str, str]]]:
    """Return canonical algorithm metadata for UI, docs or future extensions."""
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
