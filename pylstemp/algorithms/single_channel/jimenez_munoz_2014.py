"""Jimenez-Munoz et al. (2014), Eqs. 1, 2, 4 and 6, Landsat-8 Band 10."""
from __future__ import annotations
import numpy as np
from ...metadata import AlgorithmSpec
from ...validation import to_float_array, ensure_same_shape
from .base import BaseTemperatureAlgorithm


class SingleChannelJimenezMunoz2014LST(BaseTemperatureAlgorithm):
    """Retrieve LST [K] with explicit TOA radiance and PWV [g/cm2].

    Polynomial atmospheric functions use the published Band-10 matrix.
    Operational PWV range is 0..3 g/cm2: the paper reports degraded
    performance above 3. Invalid/out-of-range raster pixels become NaN;
    invalid scalars are rejected. Landsat-9 coefficient transfer is experimental.
    """
    b_gamma = 1324.0  # K, Eq. 2, TIRS-1 (Landsat Band 10).
    coefficients = ((0.04019, 0.02916, 1.01523),
                    (-0.38333, -1.50294, 0.20324),
                    (0.00918, 1.36072, -0.27514))  # Eq. 6, NOT SW Table I.

    def __call__(self, **kwargs):
        """Require brightness_temperature_10, emissivity_10, radiance_band_10, water_vapor."""
        if kwargs.get("radiance_band_10") is None or kwargs.get("water_vapor") is None:
            raise ValueError("'jimenez-munoz-sc-2014' requires radiance_band_10 "
                             "[W m-2 sr-1 um-1] and water_vapor [g/cm2]. "
                             "Use toa_radiance(..., metadata=..., band=10) and water_vapor(...).")
        tb = to_float_array("brightness_temperature_10", kwargs.get("brightness_temperature_10"))
        eps = to_float_array("emissivity_10", kwargs.get("emissivity_10"))
        radiance = to_float_array("radiance_band_10", kwargs["radiance_band_10"])
        invalid = self._validate_inputs(mask=kwargs.get("mask"),
            brightness_temperature_10=tb, emissivity_10=eps, radiance_band_10=radiance)
        invalid |= radiance <= 0
        w = to_float_array("water_vapor", kwargs["water_vapor"])
        if w.ndim == 0:
            if not np.isfinite(w) or not 0 <= w <= 3:
                raise ValueError("jimenez-munoz-sc-2014: scalar water_vapor must be finite "
                                 "and within [0,3] g/cm2; above 3 the polynomial SC approach "
                                 "loses accuracy. Use split_window or atmospheric parameters.")
        else:
            ensure_same_shape(water_vapor=w, brightness_temperature_10=tb)
        invalid |= ~np.isfinite(w) | (w < 0) | (w > 3)
        with np.errstate(all="ignore"):
            psi1, psi2, psi3 = (a*w*w + b*w + c for a,b,c in self.coefficients)
            gamma = tb*tb / (self.b_gamma*radiance)
            delta = tb - tb*tb/self.b_gamma
            result = gamma*((psi1*radiance + psi2)/eps + psi3) + delta
        return self._finalize(result, mask=invalid)


ALGORITHM_SPEC = AlgorithmSpec(
    key="jimenez-munoz-sc-2014", factory=SingleChannelJimenezMunoz2014LST,
    name="Jimenez-Munoz 2014 single-channel LST", reference="Jimenez-Munoz et al. (2014)",
    citation="Jimenez-Munoz, J.-C., Sobrino, J. A., Skokovic, D., Mattar, C., and Cristobal, J. "
             "Land surface temperature retrieval methods from Landsat-8 thermal infrared sensor data. "
             "IEEE Geoscience and Remote Sensing Letters 11(10), 1840-1843, 2014. "
             "https://doi.org/10.1109/LGRS.2014.2312032",
)
