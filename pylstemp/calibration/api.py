"""Method-selected interface for the three main calibration conversions."""
from ..exceptions import InvalidMethodRequested
from ..messages import contextual_errors
from ..validation import ensure_bool
from ..diagnostics import annotate
from .toa_radiance import toa_radiance
from .toa_reflectance import toa_reflectance
from .brightness import brightness

_METHODS = {
    "toa-radiance": toa_radiance,
    "toa-reflectance": toa_reflectance,
    "brightness": brightness,
}


@contextual_errors
def calibrate(data, *, method, return_diagnostics=False, **kwargs):
    """Convert Landsat data with an explicitly selected calibration method.

    Parameters
    ----------
    data : array-like
        Level-1 DN for toa-radiance/toa-reflectance; TOA spectral radiance
        [W m-2 sr-1 um-1] for brightness by default.
    method : {"toa-radiance", "toa-reflectance", "brightness"}
        Required output conversion. No conversion is selected implicitly.
    **kwargs
        Arguments of the selected direct function, including band, metadata
        and mask. toa-reflectance also accepts sun_elevation. brightness
        accepts sensor and input_quantity="dn" for explicit DN conversion.
        Unsupported arguments raise TypeError.

    Returns
    -------
    numpy.ndarray
        TOA radiance [W m-2 sr-1 um-1], dimensionless TOA reflectance, or
        TOA brightness temperature [K]. mask=True pixels become NaN.

    Notes
    -----
    Prepare QA using quality_mask() and pass it as mask=. Calibration
    does not perform atmospheric/emissivity correction or estimate LST.
    Existing Level-2 SR scaling remains a separate surface_reflectance helper.
    """
    method = method.strip().lower() if isinstance(method, str) else method
    if not isinstance(method, str) or method not in _METHODS:
        raise InvalidMethodRequested(
            f"Unknown calibration method {method!r}. Available: {', '.join(_METHODS)}."
        )
    return_diagnostics = ensure_bool("return_diagnostics", return_diagnostics)
    result = _METHODS[method](data, **kwargs)
    if return_diagnostics:
        units = {"toa-radiance": "W m-2 sr-1 um-1", "toa-reflectance": "dimensionless", "brightness": "kelvin"}[method]
        return annotate(dict(result=result), family="calibration", method=method, units=units,
            band=kwargs.get("band"), input_quantity=kwargs.get("input_quantity", "radiance" if method=="brightness" else "dn"),
            sensor=kwargs.get("sensor"), metadata_source="matching-MTL" if kwargs.get("metadata") is not None else "sensor-fallback")
    return result
