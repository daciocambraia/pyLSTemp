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


def _emissivity_pair(ndvi_image, red_band=None, emissivity_method: str = "avdan"):
    """Compute emissivity pair from an NDVI image."""
    ndvi_array = to_float_array("ndvi_image", ndvi_image)
    validated_red_band = None if red_band is None else to_float_array("red_band", red_band)
    ensure_same_shape(ndvi_image=ndvi_array, red_band=validated_red_band)

    algorithm = emissivity_registry.create(emissivity_method)
    return algorithm(ndvi=ndvi_array, red_band=validated_red_band)


def emissivity_band_10(ndvi_image, red_band=None, emissivity_method: str = "avdan"):
    """Compute emissivity for the thermal band 10 workflow."""

    emissivity_10, _ = _emissivity_pair(
        ndvi_image,
        red_band=red_band,
        emissivity_method=emissivity_method,
    )
    return emissivity_10


def emissivity_band_11(ndvi_image, red_band=None, emissivity_method: str = "avdan"):
    """Compute emissivity for the thermal band 11 workflow."""

    _, emissivity_11 = _emissivity_pair(
        ndvi_image,
        red_band=red_band,
        emissivity_method=emissivity_method,
    )
    return emissivity_11


def single_window(
    brightness_temperature_10,
    red_band,
    nir_band,
    lst_method: str = "mono-window",
    emissivity_method: str = "avdan",
    unit: str = "kelvin",
) -> np.ndarray:
    """Compute land surface temperature using a single-channel method."""
    normalized_unit = normalize_temperature_unit(unit)

    brightness_10 = to_float_array("brightness_temperature_10", brightness_temperature_10)
    red = to_float_array("red_band", red_band)
    nir = to_float_array("nir_band", nir_band)
    ensure_same_shape(
        brightness_temperature_10=brightness_10,
        red_band=red,
        nir_band=nir,
    )

    mask = build_mask_from(brightness_10)
    ndvi_image = ndvi(nir, red, mask=mask)
    emissivity_10 = emissivity_band_10(ndvi_image, red_band=red, emissivity_method=emissivity_method)

    result = single_channel_registry.create(lst_method)(
        emissivity_10=emissivity_10,
        brightness_temperature_10=brightness_10,
        mask=mask,
    )
    return result if normalized_unit == "kelvin" else result - CELSIUS_SCALER


def split_window(
    brightness_temperature_10,
    brightness_temperature_11,
    red_band,
    nir_band,
    lst_method: str,
    emissivity_method: str,
    unit: str = "kelvin",
) -> np.ndarray:
    """Compute land surface temperature using a split-window method."""
    normalized_unit = normalize_temperature_unit(unit)

    brightness_10 = to_float_array("brightness_temperature_10", brightness_temperature_10)
    brightness_11 = to_float_array("brightness_temperature_11", brightness_temperature_11)
    red = to_float_array("red_band", red_band)
    nir = to_float_array("nir_band", nir_band)
    ensure_same_shape(
        brightness_temperature_10=brightness_10,
        brightness_temperature_11=brightness_11,
        red_band=red,
        nir_band=nir,
    )

    mask = build_mask_from(brightness_10)
    ndvi_image = ndvi(nir, red, mask=mask)
    emissivity_10 = emissivity_band_10(ndvi_image, red_band=red, emissivity_method=emissivity_method)
    emissivity_11 = emissivity_band_11(ndvi_image, red_band=red, emissivity_method=emissivity_method)

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
