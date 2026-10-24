"""Image-based optical correction following Chavez (1996), DOS/COST."""
from dataclasses import dataclass
import numpy as np
from .validation import to_float_array, ensure_boolean_mask


@dataclass(frozen=True)
class ChavezParameters:
    """Reusable full-scene haze parameters; fit once, then apply to tiles."""
    method: str
    dark_reflectance: float
    assumed_dark_surface: float
    sun_elevation: float
    percentile: float
    valid_samples: int


def _fit_chavez(toa_reflectance, *, sun_elevation, method="cost", percentile=.01,
               assumed_dark_surface=.01, mask=None):
    """Fit haze in solar-angle-corrected TOA reflectance units, not DN.

    percentile=.01 means the 0.01st percentile (not 1%). This selection rule
    is an explicit computational choice; Chavez does not prescribe this
    universal percentile. Fit on the complete valid scene. COST uses the
    solar cosine approximation; its original TM assessment is not OLI validation.
    """
    values = to_float_array("toa_reflectance",toa_reflectance)
    if method not in {"dos", "cost"}:
        raise ValueError("method must be dos or cost.")
    if not np.isfinite(sun_elevation) or not 0 < sun_elevation <= 90:
        raise ValueError("sun_elevation must be scalar degrees in (0,90].")
    if not np.isfinite(percentile) or not 0 <= percentile <= 100:
        raise ValueError("percentile must be in [0,100].")
    if not np.isfinite(assumed_dark_surface) or not 0 <= assumed_dark_surface <= 1:
        raise ValueError("assumed_dark_surface must be in [0,1].")
    valid = np.isfinite(values) & (values >= 0) & (values <= 1)
    if mask is not None:
        valid &= ~ensure_boolean_mask(mask, shape=values.shape)
    samples = values[valid]
    if samples.size < 2:
        raise ValueError("At least two valid samples are needed to fit haze.")
    dark = float(np.percentile(samples,percentile))
    # Nonpositive haze is evidence against an additive haze correction.
    if dark < assumed_dark_surface:
        raise ValueError("Dark percentile is below assumed dark-surface reflectance; review the scene/selection instead of clipping haze.")
    return ChavezParameters(method,dark,float(assumed_dark_surface),float(sun_elevation),
                            float(percentile),int(samples.size))


def _chavez_reflectance(toa_reflectance, *, parameters, mask=None):
    """Apply scene-fitted DOS/COST; return an approximate corrected scenario.

    Using rho_TOA = pi*L*d^2/(ESUN*cos(theta_z)), subtracting the DOS haze
    rho_dark-0.01 gives rho_DOS. COST additionally divides by cos(theta_z),
    with nadir transmittance=1 and downwelling=0 (Chavez pp.1027--1029).
    Values outside [0,1] become NaN; no physical-range clipping is applied.
    The model assumes ONE scene solar angle, matching the fit parameters.
    """
    if not isinstance(parameters,ChavezParameters):
        raise ValueError("Use parameters returned by optical_correction(return_diagnostics=True).")
    p=parameters
    if (p.method not in {"dos","cost"} or not np.isfinite(p.sun_elevation)
        or not 0 < p.sun_elevation <= 90 or not np.isfinite(p.dark_reflectance)
        or not 0 <= p.assumed_dark_surface <= p.dark_reflectance <= 1):
        raise ValueError("Invalid Chavez parameters.")
    values=to_float_array("toa_reflectance",toa_reflectance)
    invalid=~np.isfinite(values) | (values < 0) | (values > 1)
    if mask is not None:
        invalid |= ensure_boolean_mask(mask,shape=values.shape)
    result=values-(p.dark_reflectance-p.assumed_dark_surface)
    if p.method == "cost":
        result=result/np.sin(np.deg2rad(p.sun_elevation))
    return np.where(invalid | (result < 0) | (result > 1),np.nan,result)


from .messages import contextual_errors


@contextual_errors
def optical_correction(toa_reflectance, *, method="chavez-cost", sun_elevation=None,
                       mask=None, parameters=None, percentile=None,
                       assumed_dark_surface=None, return_diagnostics=False):
    """Correct TOA reflectance using a selected optical method.

    method: chavez-dos or chavez-cost. Fit on the full valid scene with one
    sun_elevation [degrees, (0,90]]; defaults: percentile .01, dark surface .01.
    return_diagnostics=True returns reflectance and reusable parameters.
    For tiles supply parameters and omit fitting options; their method must
    match. Invalid corrected reflectance outside [0,1] becomes NaN, not clipped.
    Chavez is a TM-derived approximation, not validated OLI/LaSRC equivalence.
    """
    if not isinstance(method,str) or method.strip().lower() not in {"chavez-dos","chavez-cost"}:
        raise ValueError("method must be chavez-dos or chavez-cost.")
    if not isinstance(return_diagnostics,(bool,np.bool_)):
        raise ValueError("return_diagnostics must be boolean.")
    key=method.strip().lower().removeprefix("chavez-")
    if parameters is None:
        if sun_elevation is None:
            raise ValueError("Provide sun_elevation when fitting optical correction.")
        parameters=_fit_chavez(toa_reflectance,sun_elevation=sun_elevation,
            method=key,percentile=.01 if percentile is None else percentile,
            assumed_dark_surface=.01 if assumed_dark_surface is None else assumed_dark_surface,
            mask=mask)
    else:
        if any(value is not None for value in (sun_elevation,percentile,assumed_dark_surface)):
            raise ValueError("Reusable parameters cannot be combined with fitting options.")
        if not isinstance(parameters,ChavezParameters) or parameters.method!=key:
            raise ValueError("Reusable parameters must match the selected Chavez method.")
    corrected=_chavez_reflectance(toa_reflectance,parameters=parameters,mask=mask)
    if return_diagnostics:
        return dict(reflectance=corrected,parameters=parameters,method="chavez-"+key,
                    units="dimensionless",invalid_mask=~np.isfinite(corrected))
    return corrected
