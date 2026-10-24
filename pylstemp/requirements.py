"""Actionable input descriptions shared by API errors and the catalog."""

INPUT_HELP = {
    "brightness": "Provide TOA radiance [W m-2 sr-1 um-1], band 10/11 and matching MTL (metadata=) or sensor. Output is TOA BT [K]. For raw Level-1 DN explicitly set input_quantity='dn'; never rescale radiance again.",
    "optical_correction": "Provide TOA reflectance [0,1], method=chavez-dos/chavez-cost and scene solar elevation; for tiles reuse returned parameters and omit fitting options.",
    "emissivity": "Provide aligned red/nir bands and band 10/11; NDVI is calculated internally. Prepared NDVI remains an alternative. Select method=avdan-2016, gopinadh-2018, sobrino-2004-tm6 or sobrino-2008. Sobrino2008 full requires red_surface and band-specific parameters.",
    "single_window": "Provide aligned band-10 brightness in Kelvin and calibrated red/nir matching the selected emissivity source contract; radiometric quantities are not interchangeable. Select a registered LST and emissivity method.",
    "split_window": "Provide aligned band-10/11 brightness in Kelvin and calibrated red/nir matching the selected emissivity source contract; radiometric quantities are not interchangeable. Avdan is single-channel only. PWV is in g/cm2.",
    "water_vapor": "Provide aligned 2D band-10/11 brightness in Kelvin and red/nir for internal NDVI (or prepared NDVI). Use odd window_size>=3, group_count>=1, chunk_rows>=1 and a boolean mask.",
    "toa_radiance": "Provide Level-1 DN, band 1..11 and matching MTL radiance gain/bias. Output W m-2 sr-1 um-1; no solar-angle correction.",
    "toa_reflectance": "Provide Level-1 MTL, optical DN/band 1..9 and a solar elevation in degrees within (0,90].",
    "surface_reflectance": "Provide existing Collection 2 Level-2 SR_B* DN. Default scale=0.0000275, offset=-0.2; this does not correct Level-1 atmosphere.",
    "brightness_from_mtl": "Provide Level-1 MTL and thermal band 10/11 DN; MTL must include radiance gain/bias and K1/K2.",
    "read_mtl": "Provide one Landsat 8/9 *_MTL.txt file for the corresponding input product.",
    "quality_mask": "Provide aligned unsigned 16-bit QA_PIXEL and optional QA_RADSAT. True means invalid.",
}

PWV_SUPPORT = {
    "rozenstein-2014": "Required PWV scalar/aligned raster [0.5,3] g/cm2, explicit atmospheric_profile and preselected temperature_range. Invalid raster pixels become NaN.",
    "jimenez-munoz-2014-sc": "Required scalar or aligned raster [0,3] g/cm2. Invalid/out-of-range raster pixels become NaN; scalar out of range is rejected.",
    "du-2015": "Optional scalar or aligned raster [0,6.3] g/cm2. Invalid raster pixels become NaN; invalid scalars raise. None uses all-CWV coefficients.",
    "jimenez-munoz-2014-sw": "Required finite nonnegative scalar or aligned raster in g/cm2; invalid raster pixels become NaN.",
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
            text="Calibrated red/nir (or prepared NDVI in [-1,1]); optical convention and fixed-threshold validity require source-specific justification; same emissivity returned for bands 10/11. Intended for single-channel LST."
        else:
            text="TOA-radiance red/nir under the adopted Rongali Step-1 interpretation (or prepared NDVI in [-1,1]); band-specific emissivity, study-scene NDVI endmembers 0.15/0.48 transferred explicitly."
    if family=="water_vapor" and key=="ren-2015":
        text="Aligned 2D BT10/BT11 in K; Red/nir for internal NDVI, or prepared NDVI, required by default local +/-1.5 sigma filter; optional only with ndvi_filter=False. Odd window, minimum samples, chi-squared screen; PWV [.06,6.3] g/cm2. Diagnostics available. No global NDVI groups."
    if family=="single_channel" and key=="jimenez-munoz-2014-sc":
        text+=" Also supply radiance_band_10 [W m-2 sr-1 um-1] matching BT10 and "+PWV_SUPPORT[key]
    if family=="split_window":
        text+=" "+PWV_SUPPORT.get(key,"Check the method's PWV requirements.")
        if key=="kerr-1992":text+=" The equation uses NDVI, not emissivity values."
    return text


def describe_source_contract(family, key):
    """Expose the reviewed source contract shipped with the installed package."""
    import json
    from pathlib import Path
    cards = json.loads(Path(__file__).with_name("method_cards.json").read_text(encoding="utf8"))
    card = next((item for item in cards if item["method"] == key), None)
    if card is None:
        return dict(source_sensor="Source sensor not declared", source_location="Not reviewed",
                    optical_input_contract="Not established", source_review_status="Not reviewed")
    return dict(source_sensor=card["sensor"], source_location=card["source_location"],
                optical_input_contract=card["optical_contract"],
                source_review_status=card["source_review_status"])
