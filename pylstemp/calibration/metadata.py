"""Read and validate matching Landsat scene calibration metadata."""
from pathlib import Path
from collections.abc import Mapping
import re
import numpy as np
from ..messages import contextual_errors


@contextual_errors
def read_mtl(path):
    """Read scalar MTL fields without assuming the scene's calibration values."""
    result = {}
    for line in Path(path).read_text(encoding="utf-8-sig").splitlines():
        match = re.match(r"\s*([A-Z0-9_]+)\s*=\s*(.*?)\s*$", line)
        if not match:
            continue
        key, value = match.groups()
        if key in {"GROUP", "END_GROUP", "END"}:
            continue
        if value.startswith('"') and value.endswith('"'):
            result[key] = value[1:-1]
        else:
            try:
                result[key] = float(value)
            except ValueError:
                result[key] = value
    if result.get("SPACECRAFT_ID") not in {"LANDSAT_8", "LANDSAT_9"}:
        raise ValueError("Only LANDSAT_8 and LANDSAT_9 metadata are supported.")
    return result



def _number(metadata, key):
    try:
        value = float(metadata[key])
    except (KeyError, TypeError, ValueError) as exc:
        raise ValueError(f"Missing or invalid MTL field: {key}") from exc
    if not np.isfinite(value):
        raise ValueError(f"Nonfinite MTL field: {key}")
    return value



def _level1(metadata):
    if not isinstance(metadata, Mapping):
        raise ValueError("metadata must be a mapping parsed from the matching Landsat MTL file.")
    if not str(metadata.get("PROCESSING_LEVEL", "")).startswith("L1"):
        raise ValueError("Raw DN calibration requires Level-1 metadata (L1TP/L1GT/L1GS). Do not treat Level-2 SR/ST values as Level-1 DN.")



def normalize_thermal_band(band):
    """Normalize the public thermal-band aliases to band_10/band_11."""
    if isinstance(band, str):
        band = band.strip().lower()
    aliases = {10: "band_10", 11: "band_11", "10": "band_10", "11": "band_11",
               "b10": "band_10", "b11": "band_11", "band_10": "band_10", "band_11": "band_11"}
    try:
        return aliases[band]
    except (KeyError, TypeError) as exc:
        raise ValueError(f"band must be 10 or 11 ('band_10', 'band_11', 'b10', 'b11'); received {band!r}.") from exc
