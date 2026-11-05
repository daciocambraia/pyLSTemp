"""TOA radiance to brightness temperature, with explicit DN compatibility."""
import numpy as np
from ..messages import contextual_errors
from ..utils import compute_brightness_temperature, radiance_brightness_temperature
from ..sensors import get_landsat_thermal_constants
from .metadata import _level1, _number, normalize_thermal_band
from .toa_radiance import toa_radiance


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


    Quality inputs
    --------------
    Before this calculation, call quality_mask(qa_pixel_path,
    qa_radsat_path, reference_path=...) and pass the aligned boolean result
    combined with input nodata as mask=. True means invalid. QA files are
    not read by this numerical function; mask=None applies no QA screening.
    LandsatScene.calibrated() prepares and returns its QA mask automatically.
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
            sensor_constants = get_landsat_thermal_constants(sensor)
            if sensor_constants.sensor != spacecraft.lower():
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
def brightness_from_mtl(dn, *, metadata, band, mask=None):
    """Convert Level-1 thermal DN to kelvin using MTL gain, bias, K1 and K2."""
    if isinstance(band, (bool, np.bool_)) or not isinstance(band, (int, np.integer)) or band not in (10, 11):
        raise ValueError("Thermal band must be 10 or 11.")
    return brightness(dn, band, metadata=metadata, input_quantity="dn", mask=mask)
