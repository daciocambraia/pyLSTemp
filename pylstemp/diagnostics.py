"""JSON-safe processing identity shared by public diagnostic results."""
import numpy as np
from ._version import __version__


def _describe(value):
    if isinstance(value, np.ndarray):
        if value.ndim == 0:
            return _describe(value.item())
        return {"kind": "aligned-array", "shape": list(value.shape), "dtype": str(value.dtype)}
    if isinstance(value, np.generic):
        return _describe(value.item())
    if isinstance(value, dict):
        return {str(k): _describe(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [_describe(v) for v in value]
    if isinstance(value, float) and not np.isfinite(value):
        return None
    return value


def annotate(result, *, family, method, units, quality_mode="screened", **parameters):
    """Add identity and selected/raw/screened aliases without changing arrays."""
    result.update(family=family, method=method, units=units, quality_mode=quality_mode)
    result["metadata"] = dict(schema_version=1, library="pylstemp", version=__version__,
        family=family, method=method, units=units, quality_mode=quality_mode,
        parameters=_describe(parameters))
    value_key = next((k for k in ("lst", "water_vapor", "emissivity", "reflectance", "result") if k in result), None)
    if value_key is not None:
        result["result"] = result[value_key]
        result["invalid_mask"] = ~np.isfinite(result[value_key])
    for key in ("lst", "water_vapor"):
        if "raw_" + key in result:
            result["raw_result"] = result["raw_" + key]
        if "screened_" + key in result:
            result["screened_result"] = result["screened_" + key]
    result["metadata"]["result_semantics"] = (
        "raw_with_flags" if quality_mode == "diagnostic" else "screened")
    return result
