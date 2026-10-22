"""Actionable input descriptions shared by API errors and the catalog."""

INPUT_HELP = {
    "spectral_index": "Provide aligned nir/red arrays. NDVI uses TOA radiance in the standard workflow; calibrated reflectance is an explicit alternative. Boolean mask=True marks invalid pixels.",
    "brightness": "Provide TOA radiance [W m-2 sr-1 um-1], band 10/11 and matching MTL (metadata=) or sensor. Output is TOA BT [K]. For raw Level-1 DN explicitly set input_quantity='dn'; never rescale radiance again.",
    "emissivity": "Provide NDVI in [-1,1] and band 10/11. Available methods are avdan-2016 and gopinadh-2018; neither requires red surface reflectance.",
    "single_window": "Provide aligned band-10 brightness in Kelvin and red/nir TOA radiance [W m-2 sr-1 um-1] for NDVI (reflectance is an explicit alternative). Select a registered LST and emissivity method.",
    "split_window": "Provide aligned band-10/11 brightness in Kelvin and red/nir TOA radiance [W m-2 sr-1 um-1] for NDVI (reflectance is an explicit alternative). Avdan is single-channel only. PWV is in g/cm2.",
    "water_vapor": "Provide aligned 2D band-10/11 brightness in Kelvin and NDVI. Use odd window_size>=3, group_count>=1, chunk_rows>=1 and a boolean mask.",
    "toa_radiance": "Provide Level-1 DN, band 1..11 and matching MTL radiance gain/bias. Output W m-2 sr-1 um-1; no solar-angle correction.",
    "toa_reflectance": "Provide Level-1 MTL, optical DN/band 1..9 and a solar elevation in degrees within (0,90].",
    "surface_reflectance": "Provide existing Collection 2 Level-2 SR_B* DN. Default scale=0.0000275, offset=-0.2; this does not correct Level-1 atmosphere.",
    "brightness_from_mtl": "Provide Level-1 MTL and thermal band 10/11 DN; MTL must include radiance gain/bias and K1/K2.",
    "read_mtl": "Provide one Landsat 8/9 *_MTL.txt file for the corresponding input product.",
    "quality_mask": "Provide aligned unsigned 16-bit QA_PIXEL and optional QA_RADSAT. True means invalid.",
}

PWV_SUPPORT = {
    "rozenstein-2014": "Required PWV scalar/aligned raster [0.5,3] g/cm2, explicit atmospheric_profile and preselected temperature_range. Invalid raster pixels become NaN.",
    "jimenez-munoz-sc-2014": "Required scalar or aligned raster [0,3] g/cm2. Invalid/out-of-range raster pixels become NaN; scalar out of range is rejected.",
    "du-2015": "Optional scalar or aligned raster [0,6.3] g/cm2. Invalid raster pixels become NaN; invalid scalars raise. None uses all-CWV coefficients.",
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
    if family=="single_channel" and key=="jimenez-munoz-sc-2014":
        text+=" Also supply radiance_band_10 [W m-2 sr-1 um-1] matching BT10 and "+PWV_SUPPORT[key]
    if family=="split_window":
        text+=" "+PWV_SUPPORT.get(key,"Check the method's PWV requirements.")
        if key=="kerr-1992":text+=" The equation uses NDVI, not emissivity values."
    return text
