"""Stable public API for the package."""

from __future__ import annotations

import numpy as np

from .algorithms import FAMILY_REGISTRIES
from .algorithms.emissivity import emissivity_registry
from .algorithms.single_channel import single_channel_registry
from .algorithms.split_window import split_window_registry
from .algorithms.thermal import brightness_temperature
from .algorithms.vegetation import ndvi
from .exceptions import InputShapesNotEqual
from .references import ORIGINAL_LIBRARY_CREDIT
from .validation import (
    build_mask_from,
    ensure_same_shape,
    normalize_temperature_unit,
    to_float_array,
)

CELSIUS_SCALER = 273.15


def emissivity(ndvi_image, landsat_band_4=None, emissivity_method: str = "avdan"):
    """Compute band-specific emissivity from an NDVI image."""
    ndvi_array = to_float_array("ndvi_image", ndvi_image)
    red_band = None if landsat_band_4 is None else to_float_array("landsat_band_4", landsat_band_4)
    ensure_same_shape(ndvi_image=ndvi_array, landsat_band_4=red_band)

    algorithm = emissivity_registry.create(emissivity_method)
    return algorithm(ndvi=ndvi_array, red_band=red_band)


def single_window(
    landsat_band_10,
    landsat_band_4,
    landsat_band_5,
    lst_method: str = "mono-window",
    emissivity_method: str = "avdan",
    unit: str = "kelvin",
) -> np.ndarray:
    """Compute land surface temperature using a single-channel method."""
    normalized_unit = normalize_temperature_unit(unit)

    band_10 = to_float_array("landsat_band_10", landsat_band_10)
    band_4 = to_float_array("landsat_band_4", landsat_band_4)
    band_5 = to_float_array("landsat_band_5", landsat_band_5)
    ensure_same_shape(landsat_band_10=band_10, landsat_band_4=band_4, landsat_band_5=band_5)

    mask = build_mask_from(band_10)
    ndvi_image = ndvi(band_5, band_4, mask=mask)
    brightness_10, _ = brightness_temperature(band_10, mask=mask)
    emissivity_10, _ = emissivity(ndvi_image, landsat_band_4=band_4, emissivity_method=emissivity_method)

    result = single_channel_registry.create(lst_method)(
        emissivity_10=emissivity_10,
        brightness_temperature_10=brightness_10,
        mask=mask,
    )
    return result if normalized_unit == "kelvin" else result - CELSIUS_SCALER


def split_window(
    landsat_band_10,
    landsat_band_11,
    landsat_band_4,
    landsat_band_5,
    lst_method: str,
    emissivity_method: str,
    unit: str = "kelvin",
) -> np.ndarray:
    """Compute land surface temperature using a split-window method."""
    normalized_unit = normalize_temperature_unit(unit)

    band_10 = to_float_array("landsat_band_10", landsat_band_10)
    band_11 = to_float_array("landsat_band_11", landsat_band_11)
    band_4 = to_float_array("landsat_band_4", landsat_band_4)
    band_5 = to_float_array("landsat_band_5", landsat_band_5)
    ensure_same_shape(
        landsat_band_10=band_10,
        landsat_band_11=band_11,
        landsat_band_4=band_4,
        landsat_band_5=band_5,
    )

    mask = build_mask_from(band_10)
    ndvi_image = ndvi(band_5, band_4, mask=mask)
    brightness_10, brightness_11 = brightness_temperature(band_10, band_11, mask=mask)
    emissivity_10, emissivity_11 = emissivity(
        ndvi_image,
        landsat_band_4=band_4,
        emissivity_method=emissivity_method,
    )

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
    )
    return result if normalized_unit == "kelvin" else result - CELSIUS_SCALER


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
