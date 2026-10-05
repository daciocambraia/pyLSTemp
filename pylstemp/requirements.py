"""Actionable input descriptions shared by API errors and the catalog."""

INPUT_HELP = {
    "spectral_index": "Provide aligned nir/red arrays. NDVI accepts calibrated radiance or reflectance; EVI requires physical reflectance and blue. Boolean mask=True marks invalid pixels.",
    "brightness": "Provide raw Level-1 thermal DN, band 10 or 11 and landsat_8 or landsat_9; use radiance gain/bias from MTL. Output is Kelvin.",
    "emissivity": "Provide NDVI in [-1,1] and band 10/11. Available methods are avdan-2016 and gopinadh-2018; neither requires red surface reflectance.",
    "single_window": "Provide aligned band-10 brightness in Kelvin and red/nir calibrated radiance or reflectance for NDVI. Select a registered LST and emissivity method.",
    "split_window": "Provide aligned band-10/11 brightness in Kelvin and red/nir calibrated radiance or reflectance for NDVI. Avdan is single-channel only. PWV is in g/cm2.",
    "water_vapor": "Provide aligned 2D band-10/11 brightness in Kelvin and NDVI. Use odd window_size>=3, group_count>=1, chunk_rows>=1 and a boolean mask.",
    "reflectance": "Use kind='toa' with Level-1 MTL/DN, or kind='surface' with Collection 2 Level-2 SR_B* DN and matching MTL. Scaling is not atmospheric correction.",
    "toa_reflectance": "Provide Level-1 MTL, optical DN/band 1..9 and a solar elevation in degrees within (0,90].",
    "surface_reflectance": "Provide existing Collection 2 Level-2 SR_B* DN. Default scale=0.0000275, offset=-0.2; this does not correct Level-1 atmosphere.",
    "brightness_from_mtl": "Provide Level-1 MTL and thermal band 10/11 DN; MTL must include radiance gain/bias and K1/K2.",
    "read_mtl": "Provide one Landsat 8/9 *_MTL.txt file for the corresponding input product.",
    "quality_mask": "Provide aligned unsigned 16-bit QA_PIXEL and optional QA_RADSAT. True means invalid.",
}

PWV_SUPPORT = {
    "du-2015": "Optional finite scalar in [0,6.3] g/cm2; raster unsupported. None uses all-CWV coefficients.",
    "jimenez-munoz-2014": "Required finite nonnegative scalar or aligned raster in g/cm2; invalid raster pixels become NaN.",
    "price-1984": "Not used; supplying water_vapor emits a RuntimeWarning.",
    "kerr-1992": "Not used; supplying water_vapor emits a RuntimeWarning.",
    "sobrino-1993": "Not used; supplying water_vapor emits a RuntimeWarning.",
}

def describe_inputs(family, key):
    """Explain per-method requirements without inventing another registry."""
    workflow={"thermal":"brightness","single_channel":"single_window"}.get(family,family)
    text=INPUT_HELP.get(workflow, "See docs/scientific-methods.md.")
    if family=="emissivity":
        if key=="avdan-2016":
            text="NDVI in [-1,1]; same emissivity returned for bands 10/11. Intended for single-channel LST."
        else:
            text="NDVI in [-1,1]; band-specific emissivity, fixed soil/vegetation NDVI endmembers 0.15/0.48."
    if family=="split_window":
        text+=" "+PWV_SUPPORT.get(key,"Check the method's PWV requirements.")
        if key=="kerr-1992":text+=" The equation uses NDVI, not emissivity values."
    return text
