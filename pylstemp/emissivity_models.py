"""Source-specific Sobrino emissivity functions, without invented TIRS constants."""
import numpy as np
from .utils import _resolve_ndvi
from .validation import to_float_array, ensure_same_shape, ensure_boolean_mask


def _inputs(ndvi, mask, ndvi_soil, ndvi_vegetation):
    n = to_float_array("ndvi", ndvi)
    if not (-1 <= ndvi_soil < ndvi_vegetation <= 1):
        raise ValueError("NDVI endmembers must be ordered inside [-1,1].")
    invalid = ~np.isfinite(n) | (np.abs(n) > 1)
    if mask is not None:
        invalid |= ensure_boolean_mask(mask, shape=n.shape)
    fvc = np.clip((n-ndvi_soil)/(ndvi_vegetation-ndvi_soil), 0, 1)**2
    return n, fvc, invalid


def _sobrino_2004_tm6(ndvi=None, *, red=None, nir=None, mask=None):
    """TM5 band-6 Eq.13 for mixed pixels, and 0.99 for full vegetation.

    Bare soil (NDVI<0.2), water, snow and undefined inputs are NOT inferred
    from Eq.13: they are NaN. Constants are not calibrated for Landsat 8/9.
    Pass red/nir for internal NDVI, with a suitable land mask; NDVI alone
    cannot identify water or snow. A prepared ndvi remains an alternative.
    Source Section 4 constructs NDVI from TOA/surface reflectivities,
    preferring surface reflectivities; radiance inputs are not established
    equivalents. The numerical arrays cannot prove their radiometric units.
    """
    ndvi = _resolve_ndvi(ndvi, red=red, nir=nir, mask=mask)
    n, fvc, invalid = _inputs(ndvi, mask, .2, .5)
    invalid |= n < .2
    result = np.where(n > .5, .99, .004*fvc+.986)
    return np.where(invalid, np.nan, result)


def _sobrino_2008(ndvi=None, *, red=None, nir=None, soil_emissivity, vegetation_emissivity,
                 variant="simplified", red_surface=None, soil_red_coefficients=None,
                 cavity_factor=.55, vegetation_cavity=.005,
                 ndvi_soil=.2, ndvi_vegetation=.5, mask=None):
    """NDVI thresholds: simplified Eq.9, or full Eqs.5--8 with cavity.

    Pass red/nir for internal NDVI, or an explicitly prepared ndvi.
    Declare their radiometric convention and justify the chosen thresholds;
    the simplified relation does not establish radiance/reflectance equivalence.
    Endmembers must be provided per spectral band, with their provenance.
    Full mode requires calibrated SURFACE red reflectance and (a,b) for the
    soil relationship a+b*rho_red. No TM/AVHRR constants are assigned to TIRS.
    cavity_factor=.55 is the geometrical assumption used in Sobrino 2004;
    vegetation_cavity=.005 follows the typical value discussed in 2008.
    Water/snow/urban classification is the caller's masking responsibility.
    """
    ndvi = _resolve_ndvi(ndvi, red=red, nir=nir, mask=mask)
    n, fvc, invalid = _inputs(ndvi, mask, ndvi_soil, ndvi_vegetation)
    es, ev = (to_float_array(k,v) for k,v in
              (("soil_emissivity",soil_emissivity),("vegetation_emissivity",vegetation_emissivity)))
    for name,value in (("soil_emissivity",es),("vegetation_emissivity",ev)):
        if value.ndim == 0:
            if not np.isfinite(value) or not 0 < value <= 1:
                raise ValueError(name+" must be finite in (0,1].")
        else:
            ensure_same_shape(ndvi=n, **{name:value})
        invalid |= ~np.isfinite(value) | (value <= 0) | (value > 1)
    mixed = ev*fvc+es*(1-fvc)
    if variant == "simplified":
        if red_surface is not None or soil_red_coefficients is not None:
            raise ValueError("Simplified Sobrino does not use red reflectance; use variant='full'.")
        result = mixed
    elif variant == "full":
        red = to_float_array("red_surface",red_surface)
        ensure_same_shape(ndvi=n, red_surface=red)
        coefficients = np.asarray(soil_red_coefficients,dtype=float)
        if coefficients.shape != (2,) or not np.isfinite(coefficients).all():
            raise ValueError("Full Sobrino requires finite soil_red_coefficients=(a,b).")
        if not np.isfinite(cavity_factor) or not 0 <= cavity_factor <= 1:
            raise ValueError("cavity_factor must be in [0,1].")
        if not np.isfinite(vegetation_cavity) or not 0 <= vegetation_cavity < 1:
            raise ValueError("vegetation_cavity must be in [0,1).")
        invalid |= ~np.isfinite(red) | (red < 0) | (red > 1)
        result = np.where(n < ndvi_soil, coefficients[0]+coefficients[1]*red,
                    np.where(n > ndvi_vegetation, ev+vegetation_cavity,
                             mixed+(1-es)*ev*cavity_factor*(1-fvc)))
    else:
        raise ValueError("variant must be simplified or full.")
    return np.where(invalid | ~np.isfinite(result) | (result <= 0) | (result > 1), np.nan, result)
