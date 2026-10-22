"""Compatibility import; all NDVI computations use spectral_index.ndvi."""
from ..spectral_index.ndvi import NDVIAlgorithm, ndvi as _canonical_ndvi

def ndvi(band_5_nir, band_4_red, mask=None):
    """Translate legacy argument names to the single NDVI implementation."""
    return _canonical_ndvi(nir=band_5_nir, red=band_4_red, mask=mask)
