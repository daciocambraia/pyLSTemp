"""Landsat 8/9 Collection 2 calibration using scene metadata.

TOA reflectance is not atmospherically corrected surface reflectance.
Reference: USGS Using the Landsat Level-1 Data Product and C2 QA tables.
"""
from pathlib import Path
import re
import numpy as np

from .utils import apply_mask, compute_brightness_temperature
from .validation import to_float_array, ensure_boolean_mask, ensure_same_shape


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
    if not str(metadata.get("PROCESSING_LEVEL", "")).startswith("L1"):
        raise ValueError("Raw DN calibration requires Level-1 metadata.")


def toa_reflectance(dn, *, metadata, band, mask=None, sun_elevation=None):
    """Convert Level-1 optical DN to TOA reflectance (dimensionless).

    sun_elevation may be a scalar or an aligned per-pixel angle in degrees.
    By default the MTL scene-centre angle is used. Values are not clipped to
    [0, 1]: outliers remain available for quality assessment.
    """
    _level1(metadata)
    if band not in range(1, 10):
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


def brightness_from_mtl(dn, *, metadata, band, mask=None):
    """Convert Level-1 thermal DN to kelvin using MTL gain, bias, K1 and K2."""
    _level1(metadata)
    if band not in (10, 11):
        raise ValueError("Thermal band must be 10 or 11.")
    return compute_brightness_temperature(
        dn, _number(metadata, f"RADIANCE_MULT_BAND_{band}"),
        _number(metadata, f"RADIANCE_ADD_BAND_{band}"),
        _number(metadata, f"K1_CONSTANT_BAND_{band}"),
        _number(metadata, f"K2_CONSTANT_BAND_{band}"), mask=mask,
    )


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
