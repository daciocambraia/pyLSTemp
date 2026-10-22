"""Landsat 8/9 Collection 2 calibration using scene metadata.

TOA reflectance is not atmospherically corrected surface reflectance.
Reference: USGS Using the Landsat Level-1 Data Product and C2 QA tables.
"""
from pathlib import Path
import re
import numpy as np
from collections.abc import Mapping
from .messages import contextual_errors

from .utils import apply_mask, compute_brightness_temperature, radiance_brightness_temperature
from .sensors import get_landsat_thermal_constants
from .validation import to_float_array, ensure_boolean_mask, ensure_same_shape


@contextual_errors
def read_mtl(path):
    """Read scalar MTL fields without assuming the scene's calibration values."""
    result = {}
    for line in Path(path).read_text(encoding="utf-8-sig").splitlines():
        match = re.match(r"\s*([A-Z0-9_]+)\s*=\s*(.*?)\s*$", line)
        if not match:
            continue
        key, value = match.groups()
        if key in {"GROUP", "END_GROUP", "END"}:
            continue
        if value.startswith('"') and value.endswith('"'):
            result[key] = value[1:-1]
        else:
            try:
                result[key] = float(value)
            except ValueError:
                result[key] = value
    if result.get("SPACECRAFT_ID") not in {"LANDSAT_8", "LANDSAT_9"}:
        raise ValueError("Only LANDSAT_8 and LANDSAT_9 metadata are supported.")
    return result


def _number(metadata, key):
    try:
        value = float(metadata[key])
    except (KeyError, TypeError, ValueError) as exc:
        raise ValueError(f"Missing or invalid MTL field: {key}") from exc
    if not np.isfinite(value):
        raise ValueError(f"Nonfinite MTL field: {key}")
    return value


def _level1(metadata):
    if not isinstance(metadata, Mapping):
        raise ValueError("metadata must be a mapping parsed from the matching Landsat MTL file.")
    if not str(metadata.get("PROCESSING_LEVEL", "")).startswith("L1"):
        raise ValueError("Raw DN calibration requires Level-1 metadata (L1TP/L1GT/L1GS). Do not treat Level-2 SR/ST values as Level-1 DN.")


def normalize_thermal_band(band):
    """Normalize the public thermal-band aliases to band_10/band_11."""
    if isinstance(band, str):
        band = band.strip().lower()
    aliases = {10: "band_10", 11: "band_11", "10": "band_10", "11": "band_11",
               "b10": "band_10", "b11": "band_11", "band_10": "band_10", "band_11": "band_11"}
    try:
        return aliases[band]
    except (KeyError, TypeError) as exc:
        raise ValueError(f"band must be 10 or 11 ('band_10', 'band_11', 'b10', 'b11'); received {band!r}.") from exc


@contextual_errors
def toa_radiance(dn, *, metadata, band, mask=None):
    """Level-1 DN -> TOA spectral radiance [W m-2 sr-1 um-1], bands 1..11.

    Uses the matching MTL: L = RADIANCE_MULT_BAND_x * DN + RADIANCE_ADD_BAND_x.
    DN <= 0, nonfinite values and mask=True become NaN. No solar correction,
    atmospheric correction, emissivity correction or clipping is performed.
    """
    _level1(metadata)
    if isinstance(band, (bool, np.bool_)) or not isinstance(band, (int, np.integer)) or band not in range(1, 12):
        raise ValueError("Radiance band must be an integer from 1 to 11.")
    image = to_float_array("dn", dn)
    gain = _number(metadata, f"RADIANCE_MULT_BAND_{band}")
    bias = _number(metadata, f"RADIANCE_ADD_BAND_{band}")
    if gain <= 0:
        raise ValueError("Radiance gain must be positive.")
    invalid = ~np.isfinite(image) | (image <= 0)
    if mask is not None:
        invalid |= ensure_boolean_mask(mask, shape=image.shape)
    with np.errstate(over="ignore", invalid="ignore"):
        value = gain * image + bias
    return apply_mask(value, invalid | ~np.isfinite(value))


@contextual_errors
def brightness(thermal_band, band, sensor=None, rad_gain=None, rad_bias=None, mask=None,
               *, metadata=None, input_quantity="radiance"):
    """TOA brightness temperature [K], using the USGS Planck inversion.

    Default input_quantity='radiance' requires TOA spectral radiance in
    W m-2 sr-1 um-1. Supply matching Level-1 metadata for band-specific K1/K2;
    sensor='landsat_8'/'landsat_9' is a fallback when metadata is unavailable.
    Radiance is never scaled again: rad_gain/rad_bias are rejected in this mode.

    input_quantity='dn' explicitly enables the historical thermal DN shortcut.
    Matching MTL is preferred. Without MTL, sensor defaults can be overridden
    by rad_gain/rad_bias. Conflicting sensor/MTL or overrides with MTL are rejected.
    True mask entries, nonpositive radiance and nonfinite inputs become NaN.
    This is TOA BT, not emissivity/atmosphere-corrected surface temperature.
    """
    key = normalize_thermal_band(band)
    number = int(key[-2:])
    if not isinstance(input_quantity, str) or input_quantity.strip().lower() not in {"radiance", "dn"}:
        raise ValueError("input_quantity must be 'radiance' [W m-2 sr-1 um-1] or 'dn' [Level-1].")
    quantity = input_quantity.strip().lower()
    if quantity == "radiance" and (rad_gain is not None or rad_bias is not None):
        raise ValueError("Radiance is already calibrated; omit rad_gain/rad_bias or use input_quantity='dn'.")
    if metadata is not None:
        _level1(metadata)
        spacecraft = metadata.get("SPACECRAFT_ID")
        if spacecraft not in {"LANDSAT_8", "LANDSAT_9"}:
            raise ValueError("MTL SPACECRAFT_ID must be LANDSAT_8 or LANDSAT_9.")
        if sensor is not None:
            get_landsat_thermal_constants(sensor)
            if sensor != spacecraft.lower():
                raise ValueError("sensor and MTL SPACECRAFT_ID must describe the same scene.")
        if rad_gain is not None or rad_bias is not None:
            raise ValueError("With metadata, use the matching MTL coefficients; omit rad_gain/rad_bias.")
        k1 = _number(metadata, f"K1_CONSTANT_BAND_{number}")
        k2 = _number(metadata, f"K2_CONSTANT_BAND_{number}")
        radiance = toa_radiance(thermal_band, metadata=metadata, band=number, mask=mask) if quantity == "dn" else thermal_band
        return radiance_brightness_temperature(radiance, k1, k2, mask=mask)
    constants = get_landsat_thermal_constants(sensor)
    k1 = getattr(constants, f"k1_constant_{number}")
    k2 = getattr(constants, f"k2_constant_{number}")
    if quantity == "radiance":
        return radiance_brightness_temperature(thermal_band, k1, k2, mask=mask)
    gain = getattr(constants, f"radiance_mult_band_{number}") if rad_gain is None else float(rad_gain)
    bias = getattr(constants, f"radiance_add_band_{number}") if rad_bias is None else float(rad_bias)
    return compute_brightness_temperature(thermal_band, gain, bias, k1, k2, mask=mask)


@contextual_errors
def toa_reflectance(dn, *, metadata, band, mask=None, sun_elevation=None):
    """Convert Level-1 optical DN to TOA reflectance (dimensionless).

    sun_elevation may be a scalar or an aligned per-pixel angle in degrees.
    By default the MTL scene-centre angle is used. Values are not clipped to
    [0, 1]: outliers remain available for quality assessment.
    """
    _level1(metadata)
    if isinstance(band, (bool, np.bool_)) or not isinstance(band, (int, np.integer)) or band not in range(1, 10):
        raise ValueError("Optical band must be an integer from 1 to 9.")
    image = to_float_array("dn", dn)
    gain = _number(metadata, f"REFLECTANCE_MULT_BAND_{band}")
    bias = _number(metadata, f"REFLECTANCE_ADD_BAND_{band}")
    if gain <= 0:
        raise ValueError("Reflectance gain must be positive.")
    elevation = np.asarray(_number(metadata, "SUN_ELEVATION") if sun_elevation is None else sun_elevation, dtype=float)
    if elevation.ndim:
        ensure_same_shape(dn=image, sun_elevation=elevation)
    invalid_angle = ~np.isfinite(elevation) | (elevation <= 0) | (elevation > 90)
    if elevation.ndim == 0 and invalid_angle:
        raise ValueError("SUN_ELEVATION must be within (0, 90] degrees.")
    invalid = ~np.isfinite(image) | (image <= 0) | invalid_angle
    if mask is not None:
        invalid |= ensure_boolean_mask(mask, shape=image.shape)
    with np.errstate(divide="ignore", invalid="ignore"):
        reflectance = (gain * image + bias) / np.sin(np.deg2rad(elevation))
    return apply_mask(reflectance, invalid | ~np.isfinite(reflectance))


@contextual_errors
def brightness_from_mtl(dn, *, metadata, band, mask=None):
    """Convert Level-1 thermal DN to kelvin using MTL gain, bias, K1 and K2."""
    if isinstance(band, (bool, np.bool_)) or not isinstance(band, (int, np.integer)) or band not in (10, 11):
        raise ValueError("Thermal band must be 10 or 11.")
    return brightness(dn, band, metadata=metadata, input_quantity="dn", mask=mask)


@contextual_errors
def surface_reflectance(dn, *, scale=0.0000275, offset=-0.2, mask=None):
    """Scale C2 Level-2 SR_B* DN to surface reflectance; no sun correction.

    This does not perform atmospheric correction on Level-1 DN.
    """
    image = to_float_array("dn", dn)
    if not np.isfinite(scale) or scale <= 0 or not np.isfinite(offset):
        raise ValueError("SR scaling must be finite, with positive scale.")
    invalid = ~np.isfinite(image) | (image <= 0)
    if mask is not None:
        invalid |= ensure_boolean_mask(mask, shape=image.shape)
    return apply_mask(image * scale + offset, invalid)


@contextual_errors
def quality_mask(qa_pixel, qa_radsat=None, *, exclude_water=False):
    """C2 Landsat 8/9 mask: fill, dilated cloud, cirrus, cloud, shadow, snow.

    QA_RADSAT excludes saturation in B2/B4/B5 and terrain occlusion.
    Thermal saturation is not encoded in these QA_RADSAT optical bits.
    Water is preserved unless exclude_water=True (use True for Wang over land).
    """
    qa = np.asarray(qa_pixel)
    if not np.issubdtype(qa.dtype, np.integer) or np.any(qa < 0) or np.any(qa > 65535):
        raise ValueError("QA_PIXEL must contain unsigned 16-bit integer values.")
    bits = 0b111111 | ((1 << 7) if exclude_water else 0)
    invalid = (qa.astype(np.uint16) & bits) != 0
    if qa_radsat is not None:
        sat = np.asarray(qa_radsat)
        ensure_same_shape(qa_pixel=qa, qa_radsat=sat)
        if not np.issubdtype(sat.dtype, np.integer) or np.any(sat < 0) or np.any(sat > 65535):
            raise ValueError("QA_RADSAT must contain unsigned 16-bit integer values.")
        invalid |= (sat.astype(np.uint16) & ((1 << 1) | (1 << 3) | (1 << 4) | (1 << 11))) != 0
    return invalid
