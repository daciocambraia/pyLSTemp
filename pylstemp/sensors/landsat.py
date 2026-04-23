"""Thermal calibration constants for supported Landsat sensors."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class LandsatThermalConstants:
    """
    Thermal constants for Landsat brightness-temperature conversion.

    Attributes
    ----------
    sensor : str
        Sensor key.
    radiance_mult_band_10 : float
        Default ``RADIANCE_MULT_BAND_10`` value.
    radiance_mult_band_11 : float
        Default ``RADIANCE_MULT_BAND_11`` value.
    radiance_add_band_10 : float
        Default ``RADIANCE_ADD_BAND_10`` value.
    radiance_add_band_11 : float
        Default ``RADIANCE_ADD_BAND_11`` value.
    k1_constant_10 : float
        Band 10 thermal calibration constant K1.
    k1_constant_11 : float
        Band 11 thermal calibration constant K1.
    k2_constant_10 : float
        Band 10 thermal calibration constant K2.
    k2_constant_11 : float
        Band 11 thermal calibration constant K2.
    """

    sensor: str
    radiance_mult_band_10: float
    radiance_mult_band_11: float
    radiance_add_band_10: float
    radiance_add_band_11: float
    k1_constant_10: float
    k1_constant_11: float
    k2_constant_10: float
    k2_constant_11: float


LANDSAT_THERMAL_CONSTANTS: dict[str, LandsatThermalConstants] = {
    "landsat_8": LandsatThermalConstants(
        sensor="landsat_8",
        radiance_mult_band_10=0.0003342,
        radiance_mult_band_11=0.0003342,
        radiance_add_band_10=0.1,
        radiance_add_band_11=0.1,
        k1_constant_10=774.8853,
        k1_constant_11=480.8883,
        k2_constant_10=1321.0789,
        k2_constant_11=1201.1442,
    ),
    "landsat_9": LandsatThermalConstants(
        sensor="landsat_9",
        radiance_mult_band_10=0.00038,
        radiance_mult_band_11=0.000349,
        radiance_add_band_10=0.1,
        radiance_add_band_11=0.1,
        k1_constant_10=799.0284,
        k1_constant_11=475.6581,
        k2_constant_10=1329.2405,
        k2_constant_11=1198.3494,
    ),
}


def get_landsat_thermal_constants(sensor: str) -> LandsatThermalConstants:
    """
    Return thermal constants for a supported Landsat sensor.

    Parameters
    ----------
    sensor : str
        Sensor key, such as ``"landsat_8"`` or ``"landsat_9"``.

    Returns
    -------
    LandsatThermalConstants
        Sensor-specific radiance and thermal calibration constants.

    Raises
    ------
    ValueError
        If the sensor is not supported.
    """

    normalized_sensor = sensor.strip().lower()
    if normalized_sensor not in LANDSAT_THERMAL_CONSTANTS:
        raise ValueError(
            f"Unsupported sensor '{sensor}'. Available sensors: {sorted(LANDSAT_THERMAL_CONSTANTS)}"
        )
    return LANDSAT_THERMAL_CONSTANTS[normalized_sensor]
