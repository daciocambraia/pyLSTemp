"""Brightness temperature calculations for Landsat 8 and Landsat 9 thermal bands."""

from __future__ import annotations

import numpy as np

from ...metadata import AlgorithmSpec
from ...sensors import get_landsat_thermal_constants
from ...utils import compute_brightness_temperature
from ...validation import ensure_boolean_mask, ensure_same_shape, to_float_array


class BrightnessTemperatureLandsat:
    """
    Convert Landsat thermal bands to brightness temperature.

    This class contains the band-specific conversion logic used by the
    public ``brightness`` dispatcher.

    Notes
    -----
    - Supported sensors are ``"landsat_8"`` and ``"landsat_9"``.
    - Default radiance gain and bias values are loaded from sensor metadata.
    - User-provided ``rad_gain`` and ``rad_bias`` override the defaults.
    - Radiance gain/bias are different from the sensor constants ``K1`` and
      ``K2``.
    """

    def compute_band_10(
        self,
        thermal_band,
        sensor: str,
        rad_gain: float | None = None,
        rad_bias: float | None = None,
        mask=None,
    ) -> np.ndarray:
        """
        Compute brightness temperature for thermal Band 10.

        Parameters
        ----------
        thermal_band : array-like
            Thermal Band 10 image.
        sensor : str
            Landsat sensor name. Supported values are ``"landsat_8"`` and
            ``"landsat_9"``.
        rad_gain : float, optional
            Radiance multiplicative factor, equivalent to
            ``RADIANCE_MULT_BAND_10``. If omitted, the sensor default is used.
        rad_bias : float, optional
            Radiance additive factor, equivalent to ``RADIANCE_ADD_BAND_10``.
            If omitted, the sensor default is used.
        mask : array-like of bool, optional
            Boolean mask where True values indicate invalid pixels.

        Returns
        -------
        ndarray
            Brightness temperature image in Kelvin.
        """
        constants = get_landsat_thermal_constants(sensor)
        thermal_image = to_float_array("thermal_band", thermal_band)

        validated_mask = None
        if mask is not None:
            validated_mask = ensure_boolean_mask(mask, shape=thermal_image.shape)

        effective_rad_gain = constants.radiance_mult_band_10 if rad_gain is None else float(rad_gain)
        effective_rad_bias = constants.radiance_add_band_10 if rad_bias is None else float(rad_bias)

        return compute_brightness_temperature(
            thermal_image,
            effective_rad_gain,
            effective_rad_bias,
            constants.k1_constant_10,
            constants.k2_constant_10,
            mask=validated_mask,
        )

    def compute_band_11(
        self,
        thermal_band,
        sensor: str,
        rad_gain: float | None = None,
        rad_bias: float | None = None,
        mask=None,
    ) -> np.ndarray:
        """
        Compute brightness temperature for thermal Band 11.

        Parameters
        ----------
        thermal_band : array-like
            Thermal Band 11 image.
        sensor : str
            Landsat sensor name. Supported values are ``"landsat_8"`` and
            ``"landsat_9"``.
        rad_gain : float, optional
            Radiance multiplicative factor, equivalent to
            ``RADIANCE_MULT_BAND_11``. If omitted, the sensor default is used.
        rad_bias : float, optional
            Radiance additive factor, equivalent to ``RADIANCE_ADD_BAND_11``.
            If omitted, the sensor default is used.
        mask : array-like of bool, optional
            Boolean mask where True values indicate invalid pixels.

        Returns
        -------
        ndarray
            Brightness temperature image in Kelvin.
        """
        constants = get_landsat_thermal_constants(sensor)
        thermal_image = to_float_array("thermal_band", thermal_band)

        validated_mask = None
        if mask is not None:
            validated_mask = ensure_boolean_mask(mask, shape=thermal_image.shape)

        effective_rad_gain = constants.radiance_mult_band_11 if rad_gain is None else float(rad_gain)
        effective_rad_bias = constants.radiance_add_band_11 if rad_bias is None else float(rad_bias)

        return compute_brightness_temperature(
            thermal_image,
            effective_rad_gain,
            effective_rad_bias,
            constants.k1_constant_11,
            constants.k2_constant_11,
            mask=validated_mask,
        )

def brightness_band_10(
    band_10,
    sensor: str,
    rad_gain: float | None = None,
    rad_bias: float | None = None,
    mask=None,
):
    """
    Compute brightness temperature for Landsat thermal band 10.

    Parameters
    ----------
    band_10 : array-like
        Landsat thermal band 10 image.
    sensor : str
        Landsat sensor name. Supported values are `"landsat_8"` and
        `"landsat_9"`.
    rad_gain : float, optional
        Radiance multiplicative rescaling factor
        (`RADIANCE_MULT_BAND_10`). If omitted, the sensor default is used.
    rad_bias : float, optional
        Radiance additive rescaling factor (`RADIANCE_ADD_BAND_10`). If
        omitted, the sensor default is used.
    mask : array-like of bool, optional
        Boolean mask where True values indicate invalid pixels.

    Returns
    -------
    numpy.ndarray
        Brightness temperature image in Kelvin.

    Notes
    -----
    - Default Landsat 8 values are `rad_gain=0.0003342` and `rad_bias=0.1`.
    - Default Landsat 9 values are `rad_gain=0.00038` and `rad_bias=0.1`.
    - Prefer the public `brightness(..., band="band_10")` dispatcher in
      user-facing workflows.

    Examples
    --------
    >>> from pylstemp import brightness
    >>> brightness_10 = brightness(band_10, band="band_10", sensor="landsat_8")
    """

    return BrightnessTemperatureLandsat().compute_band_10(
        band_10,
        sensor=sensor,
        rad_gain=rad_gain,
        rad_bias=rad_bias,
        mask=mask,
    )


def brightness_band_11(
    band_11,
    sensor: str,
    rad_gain: float | None = None,
    rad_bias: float | None = None,
    mask=None,
):
    """
    Compute brightness temperature for Landsat thermal band 11.

    Parameters
    ----------
    band_11 : array-like
        Landsat thermal band 11 image.
    sensor : str
        Landsat sensor name. Supported values are `"landsat_8"` and
        `"landsat_9"`.
    rad_gain : float, optional
        Radiance multiplicative rescaling factor
        (`RADIANCE_MULT_BAND_11`). If omitted, the sensor default is used.
    rad_bias : float, optional
        Radiance additive rescaling factor (`RADIANCE_ADD_BAND_11`). If
        omitted, the sensor default is used.
    mask : array-like of bool, optional
        Boolean mask where True values indicate invalid pixels.

    Returns
    -------
    numpy.ndarray
        Brightness temperature image in Kelvin.

    Notes
    -----
    - Default Landsat 8 values are `rad_gain=0.0003342` and `rad_bias=0.1`.
    - Default Landsat 9 values are `rad_gain=0.000349` and `rad_bias=0.1`.
    - Prefer the public `brightness(..., band="band_11")` dispatcher in
      user-facing workflows.

    Examples
    --------
    >>> from pylstemp import brightness
    >>> brightness_11 = brightness(band_11, band="band_11", sensor="landsat_8")
    """

    return BrightnessTemperatureLandsat().compute_band_11(
        band_11,
        sensor=sensor,
        rad_gain=rad_gain,
        rad_bias=rad_bias,
        mask=mask,
    )


ALGORITHM_SPEC = AlgorithmSpec(
    key="brightness",
    factory=BrightnessTemperatureLandsat,
    name="Brightness temperature",
    reference="Landsat 8 and Landsat 9 thermal calibration constants",
    citation=(
        "Brightness temperature conversion using sensor-specific Landsat K1 and K2 constants "
        "with explicit per-band radiance gain and bias inputs."
    ),
    aliases=(),
)
