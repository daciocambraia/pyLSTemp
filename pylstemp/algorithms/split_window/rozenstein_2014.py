"""Rozenstein et al. (2014), Eqs. 3--10 and Tables 1--2."""
from __future__ import annotations
import numpy as np
from ...metadata import AlgorithmSpec
from ...validation import to_float_array, ensure_same_shape
from .base import SplitWindowParentLST


class SplitWindowRozenstein2014LST(SplitWindowParentLST):
    """Landsat-8 SW with an explicitly selected standard atmospheric profile.

    PWV is in g/cm2, limited to [0.5, 3]. Temperature coefficients are chosen
    BEFORE computation. The result outside the selected Celsius fit interval
    is NaN. Landsat-9 transfer and profiles over tropical regions are unvalidated.
    """
    thermal_coefficients = {
        "0-60": (-64.4661, .4398, -68.8678, .4755),
        "0-30": (-59.1391, .4213, -63.3921, .4565),
        "0-40": (-60.9196, .4276, -65.2240, .4629),
        "10-40": (-62.8065, .4338, -67.1728, .4694),
        "10-50": (-64.6081, .4399, -69.0215, .4756),
    }
    profiles = {
        "us-standard-1976": (1.0286, -.1146, 1.0083, -.1568),
        "midlatitude-summer": (1.0335, -.1134, 1.0078, -.1546),
    }

    def _compute_lst(self, **kwargs):
        profile = kwargs.get("atmospheric_profile")
        interval = kwargs.get("temperature_range", "0-60")
        if profile not in self.profiles:
            raise ValueError("rozenstein-2014 requires atmospheric_profile='us-standard-1976' or 'midlatitude-summer'; no automatic regional profile is assumed.")
        if interval not in self.thermal_coefficients:
            raise ValueError("temperature_range must be one of " + str(tuple(self.thermal_coefficients)))
        names = ("brightness_temperature_10", "brightness_temperature_11", "emissivity_10", "emissivity_11")
        images = {name: to_float_array(name, kwargs.get(name)) for name in names}
        mask = self._validate_inputs(mask=kwargs.get("mask"), **images)
        w = to_float_array("water_vapor", kwargs.get("water_vapor"))
        if w.ndim == 0:
            if not np.isfinite(w) or not .5 <= w <= 3:
                raise ValueError("rozenstein-2014 requires finite scalar PWV in [0.5,3] g/cm2.")
        else:
            ensure_same_shape(water_vapor=w, **images)
        mask |= ~np.isfinite(w) | (w < .5) | (w > 3)
        t10, t11, e10, e11 = (np.where(mask, np.nan, images[name]) for name in names)
        w = np.where(np.isfinite(w) & (w >= .5) & (w <= 3), w, np.nan)
        i10, s10, i11, s11 = self.profiles[profile]
        tau10, tau11 = i10+s10*w, i11+s11*w
        mask |= (tau10 <= 0) | (tau10 > 1) | (tau11 <= 0) | (tau11 > 1)
        c10, c11 = e10*tau10, e11*tau11
        d10 = (1-tau10)*(1+(1-e10)*tau10)
        d11 = (1-tau11)*(1+(1-e11)*tau11)
        denominator = d11*c10-d10*c11
        scale = np.maximum(np.abs(d11*c10), np.abs(d10*c11))
        singular = np.abs(denominator) <= 64*np.finfo(float).eps*np.maximum(scale, np.finfo(float).tiny)
        mask |= singular
        a10,b10,a11,b11 = self.thermal_coefficients[interval]
        with np.errstate(divide="ignore", invalid="ignore", over="ignore"):
            a = d10/denominator
            e1 = d11*(1-c10-d10)/denominator
            e2 = d10*(1-c11-d11)/denominator
            result = e1*a10 + e2*a11 + (1+a+e1*b10)*t10 - (a+e2*b11)*t11
        lower, upper = (float(v)+273.15 for v in interval.split("-"))
        mask |= (result < lower) | (result > upper)
        return result, mask


ALGORITHM_SPEC = AlgorithmSpec(
    key="rozenstein-2014", factory=SplitWindowRozenstein2014LST,
    name="Rozenstein 2014 split-window LST", reference="Rozenstein et al. (2014)",
    citation="Rozenstein, O., Qin, Z., Derimian, Y., Karnieli, A. (2014). Derivation of Land Surface Temperature for Landsat-8 TIRS Using a Split Window Algorithm. Sensors 14, 5768-5780. https://doi.org/10.3390/s140405768",
)
