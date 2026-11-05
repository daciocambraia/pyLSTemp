"""Per-pixel diagnostic flags; these are not calibrated probabilities of accuracy."""
from enum import IntFlag
import numpy as np

class QualityFlag(IntFlag):
    INPUT_MASKED = 1
    UNDEFINED = 2
    LOW_QUALITY = 4
    INSUFFICIENT_SAMPLES = 8
    PWV_OUT_OF_DOMAIN = 16
    NONPHYSICAL = 32
    ILL_CONDITIONED = 64
    SPATIAL_MEAN_PWV = 128
    LEGACY_SENSOR_TRANSFER = 256
    DU_GENERAL_FALLBACK = 512

DESCRIPTIONS = {
    'INPUT_MASKED': 'Explicit input mask or missing/invalid required input; no value fabricated.',
    'UNDEFINED': 'Estimator mathematically undefined or nonfinite.',
    'LOW_QUALITY': 'Local relation below the configured quality threshold (Wang: at least one contributing group).',
    'INSUFFICIENT_SAMPLES': 'Fewer than the operational minimum samples; at least two still needed for a regression.',
    'PWV_OUT_OF_DOMAIN': 'PWV outside the method-specific source/operational range.',
    'NONPHYSICAL': 'Negative PWV, nonpositive regression covariance, or nonpositive absolute output temperature.',
    'ILL_CONDITIONED': 'Nonzero variance too small for the screened numerical tolerance.',
    'SPATIAL_MEAN_PWV': 'PWV supplied as a spatial aggregate rather than a local pixel estimate.',
    'LEGACY_SENSOR_TRANSFER': 'Historical AVHRR-to-Landsat coefficient transfer.',
    'DU_GENERAL_FALLBACK': 'Du per-PWV coefficients unavailable: published all-CWV coefficients used explicitly.',
}
BLOCKING_FLAGS = 1 | 2 | 4 | 8 | 16 | 32 | 64

def quality_legend():
    return {f.name: {'value': int(f), 'description': DESCRIPTIONS[f.name]} for f in QualityFlag}

def validate_quality_mode(mode):
    if mode not in ('screened', 'diagnostic'):
        raise ValueError("quality_mode must be 'screened' or 'diagnostic'.")
    return mode == 'diagnostic'

def merge_quality_flags(flags, upstream):
    if upstream is None:
        return flags
    incoming = np.asarray(upstream)
    if incoming.shape != flags.shape or incoming.dtype.kind not in 'iu' or np.any(incoming < 0) or np.any(incoming > 65535):
        raise ValueError('pwv_quality_flags must be an aligned integer array with values in [0,65535].')
    return flags | incoming.astype(np.uint16)

def temperature_quality(raw_kelvin, screened_kelvin, input_mask, *, water_vapor=None,
                        domain=None, upstream=None, legacy=False, du=False):
    raw = np.asarray(raw_kelvin, dtype=float)
    flags = np.zeros(raw.shape, dtype=np.uint16)
    flags[np.asarray(input_mask, dtype=bool)] |= int(QualityFlag.INPUT_MASKED)
    flags[~np.isfinite(raw)] |= int(QualityFlag.UNDEFINED)
    flags[np.isfinite(raw) & (raw <= 0)] |= int(QualityFlag.NONPHYSICAL)
    if water_vapor is not None and domain is not None:
        w = np.broadcast_to(np.asarray(water_vapor, dtype=float), raw.shape)
        flags[~np.isfinite(w)] |= int(QualityFlag.INPUT_MASKED)
        outside = np.isfinite(w) & ((w < domain[0]) | (w > domain[1]))
        flags[outside] |= int(QualityFlag.PWV_OUT_OF_DOMAIN)
        flags[np.isfinite(w) & (w < 0)] |= int(QualityFlag.NONPHYSICAL)
        if du:
            flags[outside] |= int(QualityFlag.DU_GENERAL_FALLBACK)
    if legacy:
        flags |= int(QualityFlag.LEGACY_SENSOR_TRANSFER)
    local_flags = flags.copy()
    flags = merge_quality_flags(flags, upstream)
    return dict(lst_quality_flags=local_flags,quality_flags=flags, quality_acceptable=(flags & BLOCKING_FLAGS) == 0,
                screened_invalid_mask=~np.isfinite(screened_kelvin), quality_legend=quality_legend())
