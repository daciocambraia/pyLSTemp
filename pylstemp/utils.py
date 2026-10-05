"""Numerical helpers used by multiple conversion workflows."""

from __future__ import annotations

import numpy as np

from .validation import ensure_boolean_mask, ensure_same_shape, to_float_array


def generate_mask(image) -> np.ndarray:
    """
    Generate a default invalid-pixel mask.

    Parameters
    ----------
    image : array-like
        Input image.

    Returns
    -------
    ndarray of bool
        Mask where True indicates NaN or zero-valued pixels.
    """
    array = to_float_array("image", image)
    return ~np.isfinite(array) | (array == 0)


def apply_mask(image, mask: np.ndarray | None) -> np.ndarray:
    """
    Apply a boolean mask to an image.

    Parameters
    ----------
    image : array-like
        Input image.
    mask : array-like of bool or None
        Boolean mask where True values indicate invalid pixels.

    Returns
    -------
    ndarray
        Float copy of the input with masked pixels set to NaN.
    """
    output = np.asarray(image, dtype=float).copy()
    if mask is not None:
        validated_mask = ensure_boolean_mask(mask, shape=output.shape)
        output[validated_mask] = np.nan
    return output


def compute_ndvi(nir, red, eps: float = 1e-15, mask: np.ndarray | None = None) -> np.ndarray:
    """
    Compute the Normalized Difference Vegetation Index.

    Parameters
    ----------
    nir : array-like
        Near-infrared band.
    red : array-like
        Red band.
    eps : float, default=1e-15
        Nonnegative absolute denominator tolerance. Values <= eps are invalid;
        eps is not added to valid denominators.
    mask : array-like of bool, optional
        Boolean mask where True values indicate invalid pixels.

    Returns
    -------
    ndarray
        NDVI image with invalid values set to NaN.
    """
    nir_array = to_float_array("nir", nir)
    red_array = to_float_array("red", red)
    ensure_same_shape(nir=nir_array, red=red_array)
    if not np.isscalar(eps) or not np.isfinite(eps) or eps < 0:
        raise ValueError("compute_ndvi: eps must be a finite nonnegative denominator tolerance.")
    with np.errstate(all="ignore"):
        denominator = nir_array + red_array
        valid = np.isfinite(nir_array) & np.isfinite(red_array)
        valid &= np.isfinite(denominator) & (np.abs(denominator) > eps)
        output = np.full(nir_array.shape, np.nan, dtype=float)
        np.divide(nir_array - red_array, denominator, out=output, where=valid)
    output = np.where(np.isfinite(output) & (np.abs(output) <= 1), output, np.nan)
    return apply_mask(output, mask)


def compute_brightness_temperature(
    image,
    mult_factor: float,
    add_factor: float,
    k1: float,
    k2: float,
    mask: np.ndarray | None = None,
) -> np.ndarray:
    """
    Convert raw thermal DN values to brightness temperature.

    Parameters
    ----------
    image : array-like
        Thermal band image.
    mult_factor : float
        Radiance multiplicative factor, equivalent to
        ``RADIANCE_MULT_BAND_X``.
    add_factor : float
        Radiance additive factor, equivalent to ``RADIANCE_ADD_BAND_X``.
    k1 : float
        Thermal calibration constant K1.
    k2 : float
        Thermal calibration constant K2.
    mask : array-like of bool, optional
        Boolean mask where True values indicate invalid pixels.

    Returns
    -------
    ndarray
        Brightness temperature in Kelvin.
    """
    image_array = to_float_array("image", image)
    coefficients = np.asarray([mult_factor, add_factor, k1, k2], dtype=float)
    if not np.all(np.isfinite(coefficients)) or mult_factor <= 0 or k1 <= 0 or k2 <= 0:
        raise ValueError("Radiance gain, K1 and K2 must be positive and all coefficients finite.")
    invalid = ~np.isfinite(image_array) | (image_array <= 0)
    if mask is not None:
        invalid |= ensure_boolean_mask(mask, shape=image_array.shape)
    with np.errstate(over="ignore", invalid="ignore"):
        radiance = mult_factor * image_array + add_factor
    return radiance_brightness_temperature(radiance, k1, k2, mask=invalid)


def radiance_brightness_temperature(radiance, k1, k2, mask=None):
    """Invert Planck: TOA radiance [W m-2 sr-1 um-1] -> TOA BT [K]."""
    image = to_float_array("radiance", radiance)
    if not np.all(np.isfinite([k1, k2])) or k1 <= 0 or k2 <= 0:
        raise ValueError("K1 and K2 must be finite and positive.")
    invalid = ~np.isfinite(image) | (image <= 0)
    if mask is not None:
        invalid |= ensure_boolean_mask(mask, shape=image.shape)
    with np.errstate(all="ignore"):
        temperature = k2 / np.log1p(k1 / image)
    return apply_mask(temperature, invalid | ~np.isfinite(temperature))


def fractional_vegetation_cover(ndvi) -> np.ndarray:
    """
    Compute fractional vegetation cover from NDVI.

    Parameters
    ----------
    ndvi : array-like
        NDVI image.

    Returns
    -------
    ndarray
        Fractional vegetation cover clipped to the range 0 to 1.

    Raises
    ------
    ValueError
        If ``ndvi`` is not a 2-dimensional image.
    """
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
    """
    Compute the cavity-effect correction for emissivity methods.

    Parameters
    ----------
    emissivity_veg : float
        Vegetation emissivity coefficient.
    emissivity_soil : float
        Soil emissivity coefficient.
    fractional_vegetation_cover_image : array-like
        Fractional vegetation cover image.
    geometrical_factor : float, default=0.55
        Geometrical factor used by the correction.

    Returns
    -------
    ndarray
        Cavity-effect correction term.
    """
    fvc = to_float_array("fractional_vegetation_cover_image", fractional_vegetation_cover_image)
    return (1 - emissivity_soil) * emissivity_veg * geometrical_factor * (1 - fvc)


def rescale_band(image, mult: float = 2e-05, add: float = -0.1) -> np.ndarray:
    """
    Rescale an optical band using linear coefficients.

    Parameters
    ----------
    image : array-like
        Input optical band.
    mult : float, default=2e-05
        Multiplicative scale factor.
    add : float, default=-0.1
        Additive scale factor.

    Returns
    -------
    ndarray
        Rescaled band.

    Notes
    -----
    - Defaults follow the original implementation used by the package.
    """
    image_array = to_float_array("image", image)
    return (mult * image_array) + add
