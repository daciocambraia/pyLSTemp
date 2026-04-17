"""Numerical helpers used by multiple conversion workflows."""

from __future__ import annotations

import numpy as np

from .validation import ensure_boolean_mask, to_float_array


def generate_mask(image) -> np.ndarray:
    """Return True where a pixel is invalid for downstream computations."""
    array = to_float_array("image", image)
    return np.isnan(array) | (array == 0)


def apply_mask(image, mask: np.ndarray | None) -> np.ndarray:
    """Return a masked float array without mutating the original input."""
    output = np.asarray(image, dtype=float).copy()
    if mask is not None:
        validated_mask = ensure_boolean_mask(mask, shape=output.shape)
        output[validated_mask] = np.nan
    return output


def compute_ndvi(nir, red, eps: float = 1e-15, mask: np.ndarray | None = None) -> np.ndarray:
    """Compute NDVI while keeping invalid or user-masked pixels as NaN."""
    nir_array = to_float_array("nir", nir)
    red_array = to_float_array("red", red)
    with np.errstate(divide="ignore", invalid="ignore"):
        ndvi = (nir_array - red_array) / (nir_array + red_array + eps)
    ndvi[np.abs(ndvi) > 1] = np.nan
    return apply_mask(ndvi, mask)


def compute_brightness_temperature(
    image,
    mult_factor: float,
    add_factor: float,
    k1: float,
    k2: float,
    mask: np.ndarray | None = None,
) -> np.ndarray:
    """Convert raw thermal bands to brightness temperature."""
    image_array = to_float_array("image", image)
    toa_radiance = (mult_factor * image_array) + add_factor
    with np.errstate(divide="ignore", invalid="ignore"):
        brightness_temp = k2 / np.log((k1 / toa_radiance) + 1)
    return apply_mask(brightness_temp, mask)


def fractional_vegetation_cover(ndvi) -> np.ndarray:
    """Compute fractional vegetation cover and clip the result to the expected range."""
    ndvi_array = to_float_array("ndvi", ndvi)
    if ndvi_array.ndim != 2:
        raise ValueError("NDVI image should be 2-dimensional.")
    fvc = ((ndvi_array - 0.2) / (0.5 - 0.2)) ** 2
    return np.clip(fvc, 0, 1)


def cavity_effect(
    emissivity_veg: float,
    emissivity_soil: float,
    fractional_vegetation_cover_image,
    geometrical_factor: float = 0.55,
) -> np.ndarray:
    """Compute the cavity effect term used by emissivity methods."""
    fvc = to_float_array("fractional_vegetation_cover_image", fractional_vegetation_cover_image)
    return (1 - emissivity_soil) * emissivity_veg * geometrical_factor * (1 - fvc)


def rescale_band(image, mult: float = 2e-05, add: float = -0.1) -> np.ndarray:
    """Rescale optical Landsat bands using the default coefficients from the original code."""
    image_array = to_float_array("image", image)
    return (mult * image_array) + add
