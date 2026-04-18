"""Thermal calibration constants for supported Landsat sensors."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class LandsatThermalConstants:
    """Thermal constants needed to convert Landsat radiance to brightness temperature."""

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
    """Return thermal constants for a supported Landsat sensor."""

    normalized_sensor = sensor.strip().lower()
    if normalized_sensor not in LANDSAT_THERMAL_CONSTANTS:
        raise ValueError(
            f"Unsupported sensor '{sensor}'. Available sensors: {sorted(LANDSAT_THERMAL_CONSTANTS)}"
        )
    return LANDSAT_THERMAL_CONSTANTS[normalized_sensor]
