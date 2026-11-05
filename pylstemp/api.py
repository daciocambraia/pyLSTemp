"""Family-oriented public API for the package."""

from __future__ import annotations

import numpy as np
import warnings

from .messages import contextual_errors
from .requirements import describe_inputs, describe_source_contract, PWV_SUPPORT

from .algorithms import FAMILY_REGISTRIES
from .algorithms.emissivity import emissivity_registry
from .algorithms.single_channel import single_channel_registry
from .algorithms.split_window import split_window_registry
from .calibration import calibrate, brightness, normalize_thermal_band as _normalize_thermal_band
from .utils import _compute_ndvi as _ndvi, _resolve_ndvi
from .algorithms.water_vapor import water_vapor_registry
from .references import ORIGINAL_LIBRARY_CREDIT
from .quality import validate_quality_mode, temperature_quality
from .diagnostics import annotate
from .exceptions import UnusedParameterWarning
from .validation import (
    ensure_bool,
    build_mask_from,
    ensure_same_shape,
    ensure_boolean_mask,
    normalize_temperature_unit,
    to_float_array,
)

CELSIUS_SCALER = 273.15


def _emissivity_pair(ndvi_image, band_4_red=None, method: str = "avdan-2016"):
    """
    Compute Band 10 and Band 11 emissivity from NDVI.

    Parameters
    ----------
    ndvi_image : array-like
        NDVI image used by the emissivity method.
    band_4_red : array-like, optional
        Red band image required by selected methods.
    method : str, default="avdan-2016"
        Registered emissivity method key.

    Returns
    -------
    tuple of ndarray
        Emissivity arrays for Band 10 and Band 11.
    """
    ndvi_array = to_float_array("ndvi_image", ndvi_image)
    validated_red_band = None if band_4_red is None else to_float_array("band_4_red", band_4_red)
    ensure_same_shape(ndvi_image=ndvi_array, band_4_red=validated_red_band)

    algorithm = emissivity_registry.create(method)
    return algorithm(ndvi=ndvi_array, red_band=validated_red_band)


@contextual_errors
def emissivity_band_10(ndvi_image, band_4_red=None, method: str = "avdan-2016"):
    """
    Compute emissivity for the Band 10 thermal workflow.

    Parameters
    ----------
    ndvi_image : array-like
        NDVI image used by the emissivity method.
    band_4_red : array-like, optional
        Red band image required by selected methods.
    method : str, default="avdan-2016"
        Registered emissivity method key.

    Returns
    -------
    ndarray
        Band 10 emissivity image.
    """

    emissivity_10, _ = _emissivity_pair(
        ndvi_image,
        band_4_red=band_4_red,
        method=method,
    )
    return emissivity_10


@contextual_errors
def emissivity_band_11(ndvi_image, band_4_red=None, method: str = "avdan-2016"):
    """
    Compute emissivity for the Band 11 thermal workflow.

    Parameters
    ----------
    ndvi_image : array-like
        NDVI image used by the emissivity method.
    band_4_red : array-like, optional
        Red band image required by selected methods.
    method : str, default="avdan-2016"
        Registered emissivity method key.

    Returns
    -------
    ndarray
        Band 11 emissivity image.
    """

    _, emissivity_11 = _emissivity_pair(
        ndvi_image,
        band_4_red=band_4_red,
        method=method,
    )
    return emissivity_11


@contextual_errors
def emissivity(ndvi_image=None, band=None, band_4_red=None,
               *, method=None, red=None, nir=None, mask=None,
               return_diagnostics=False, optical_quantity=None):
    """Estimate emissivity using Avdan or Rongali.

    Supply calibrated red/nir for internal NDVI or prepared ndvi_image.
    Output is dimensionless; methods default to band10.
    Select the emissivity model with method only.


    Quality inputs
    --------------
    Before this calculation, call quality_mask(qa_pixel_path,
    qa_radsat_path, reference_path=...) and pass the aligned boolean result
    combined with input nodata as mask=. True means invalid. QA files are
    not read by this numerical function; mask=None applies no QA screening.
    LandsatScene.calibrated() prepares and returns its QA mask automatically.
    """
    from .provenance import optical_contract
    return_diagnostics = ensure_bool("return_diagnostics", return_diagnostics)
    key = emissivity_registry.resolve_key("avdan-2016" if method is None else method)
    contract = optical_contract(key, optical_quantity)
    n = _resolve_ndvi(ndvi_image, red=red, nir=nir, mask=mask)
    if band_4_red is not None:
        ensure_same_shape(ndvi=n, band_4_red=to_float_array("band_4_red", band_4_red))
    normalized_band = _normalize_thermal_band(10 if band is None else band)
    pair = _emissivity_pair(n, band_4_red=band_4_red, method=key)
    output = pair[0 if normalized_band == "band_10" else 1]
    if return_diagnostics:
        return annotate(dict(emissivity=output, optical_contract=contract), family="emissivity",
            method=key, units="dimensionless", band=int(normalized_band[-2:]),
            optical_quantity=optical_quantity, optical_contract=contract)
    return output


@contextual_errors
def single_window(
    brightness_band_10,
    band_4_red=None,
    band_5_nir=None,
    method: str = "avdan-2016",
    unit: str = "kelvin",
    *, emissivity_10=None, mask=None, radiance_band_10=None, water_vapor=None,
    return_diagnostics=False, optical_quantity=None, quality_mode="screened",
    pwv_quality_flags=None,
) -> np.ndarray | dict:
    """
    Compute single-channel LST with optical inputs OR prepared emissivity_10.

    quality_mode="diagnostic" returns raw_lst/lst, screened_lst and uint16
    quality_flags; pass aligned pwv_quality_flags to propagate PWV issues.
    Finite out-of-domain PWV is computed and flagged; default is screened.

    Prepared band-10 emissivity omits red/nir; it enables
    independently parameterized emissivity models without changing the LST equation.
    Automatic optical mode retains Avdan as its default. Prepared values must
    be band/sensor compatible; passing an array does not establish applicability.

    This workflow expects brightness temperature for thermal band 10 to be
    computed beforehand with `brightness(..., band="band_10")`.

    Parameters
    ----------
    brightness_band_10 : array-like
        Brightness temperature image for thermal band 10, in Kelvin.
    band_4_red : array-like, optional
        Red image for the optical-input route; omit with prepared emissivity_10.
    band_5_nir : array-like, optional
        NIR image for the optical-input route; omit with prepared emissivity_10.
    method : str, default="avdan-2016"
        Single-channel LST method to use.
    emissivity_10 : array-like, optional
        Prepared band-10 emissivity, dimensionless in (0,1], aligned with BT10.
        Recommended for reuse; omit red/nir in this route.
    unit : {"kelvin", "celsius"}, default="kelvin"
        Output temperature unit.

    radiance_band_10 : array-like, optional
        Band-10 TOA radiance [W m-2 sr-1 um-1], required for jimenez-munoz-2014.
        Must correspond to the same band, pixels and calibration as brightness_band_10.
    water_vapor : float or array-like, optional
        Required for jimenez-munoz-2014, in g/cm2. Scalar range [0,3];
        raster pixels outside [0,3] or nonfinite become NaN.

    Returns
    -------
    numpy.ndarray
        Land surface temperature image in the requested unit.

    Notes
    -----
    - Input arrays must have the same shape and spatial alignment.
    - Zero and `NaN` values in the brightness image are masked internally.
    - Both methods are Band-10 workflows.
    - The polynomial Jimenez SC is screened at PWV <= 3 g/cm2 per the paper.
    - avdan-2016 does not accept radiance_band_10 or water_vapor.

    Examples
    --------
    >>> from pylstemp import single_window
    >>> lst = single_window(
    ...     brightness_band_10=brightness_10,
    ...     band_4_red=red,
    ...     band_5_nir=nir,
    ...     method="avdan-2016",
    ...     unit="celsius",
    ... )


    Quality inputs
    --------------
    Before this calculation, call quality_mask(qa_pixel_path,
    qa_radsat_path, reference_path=...) and pass the aligned boolean result
    combined with input nodata as mask=. True means invalid. QA files are
    not read by this numerical function; mask=None applies no QA screening.
    LandsatScene.calibrated() prepares and returns its QA mask automatically.
    """
    from .provenance import optical_contract
    if not isinstance(return_diagnostics, (bool, np.bool_)):
        raise ValueError("return_diagnostics must be boolean.")
    diagnostic = validate_quality_mode(quality_mode)
    if not diagnostic and not return_diagnostics and pwv_quality_flags is not None:
        raise ValueError('pwv_quality_flags requires return_diagnostics=True or quality_mode="diagnostic".')
    normalized_unit = normalize_temperature_unit(unit)
    brightness_10 = to_float_array("brightness_band_10", brightness_band_10)
    invalid = build_mask_from(brightness_10)
    if mask is not None:
        invalid |= ensure_boolean_mask(mask, shape=brightness_10.shape)
    ndvi_image = None
    if emissivity_10 is not None:
        if band_4_red is not None or band_5_nir is not None:
            raise ValueError("Prepared emissivity_10 cannot be combined with optical bands.")
        emissivity_10 = to_float_array("emissivity_10", emissivity_10)
        ensure_same_shape(brightness_temperature_10=brightness_10, emissivity_10=emissivity_10)
        contract = optical_contract("prepared-emissivity", optical_quantity)
        contract["emissivity_source"] = "caller supplied; band-10/sensor provenance required"
    else:
        if band_4_red is None or band_5_nir is None:
            raise ValueError("Supply red/nir bands or a prepared band-10 emissivity image.")
        red = to_float_array("band_4_red", band_4_red)
        nir = to_float_array("band_5_nir", band_5_nir)
        ensure_same_shape(brightness_temperature_10=brightness_10, band_4_red=red, band_5_nir=nir)
        invalid |= ~np.isfinite(red) | ~np.isfinite(nir)
        ndvi_image = _ndvi(nir=nir, red=red, mask=invalid)
        emissivity_10 = emissivity_band_10(ndvi_image, band_4_red=red, method="avdan-2016")
        contract = optical_contract("avdan-2016", optical_quantity)
    mask = invalid

    key = single_channel_registry.resolve_key(method)
    extra = {}
    if key == "jimenez-munoz-2014":
        extra = dict(radiance_band_10=radiance_band_10, water_vapor=water_vapor)
    elif radiance_band_10 is not None or water_vapor is not None:
        raise ValueError(f"single_window(method={key!r}): radiance_band_10 and "
                         "water_vapor are only used by jimenez-munoz-2014.")
    algorithm = single_channel_registry.create(key)
    parameters = dict(emissivity_10=emissivity_10,
                      brightness_temperature_10=brightness_10,mask=mask,**extra)
    result = algorithm(**parameters,diagnostic=True) if (diagnostic or return_diagnostics) else algorithm(**parameters)
    if diagnostic or return_diagnostics:
        screened_parameters = dict(parameters)
        if diagnostic and key == "jimenez-munoz-2014" and water_vapor is not None:
            screened_parameters['water_vapor'] = np.broadcast_to(np.asarray(water_vapor,dtype=float),brightness_10.shape)
        screened = algorithm(**screened_parameters)
        raw_output = result if normalized_unit == 'kelvin' else result-CELSIUS_SCALER
        screened_output = screened if normalized_unit == 'kelvin' else screened-CELSIUS_SCALER
        quality = temperature_quality(result,screened,mask,water_vapor=water_vapor,
            domain=(0,3) if key=='jimenez-munoz-2014' else None,upstream=pwv_quality_flags)
        return annotate(dict(lst=raw_output if diagnostic else screened_output,
            raw_lst=raw_output,screened_lst=screened_output,
            ndvi=ndvi_image,emissivity_10=emissivity_10,invalid_mask=~np.isfinite(raw_output if diagnostic else screened_output),
            units=normalized_unit,optical_contract=contract,**quality),
            family="single_channel", method=key, units=normalized_unit, quality_mode=quality_mode,
            input_temperature_units="kelvin", water_vapor_units="g/cm2", water_vapor=water_vapor,
            optical_quantity=optical_quantity, optical_contract=contract)
    output = result if normalized_unit == "kelvin" else result - CELSIUS_SCALER
    return output


@contextual_errors
def split_window(brightness_band_10, brightness_band_11, band_4_red=None,
                 band_5_nir=None, method=None,
                 unit="kelvin", water_vapor=None, *, emissivity_10=None,
                 emissivity_11=None, ndvi_image=None, mask=None,
                 return_diagnostics=False, optical_quantity=None,
                 quality_mode="screened", pwv_quality_flags=None):
    """Compute SW LST from BT10/BT11 [K] and ONE emissivity input route.

    return_diagnostics=True includes raw/screened results and processing identity.
    quality_mode="diagnostic" selects raw_lst/lst, with screened_lst and flags.
    Du outside its PWV bins uses the published all-CWV coefficients and
    sets DU_GENERAL_FALLBACK; no nearest-bin selection or PWV clipping.

    Provide calibrated red/nir to estimate band-specific emissivity with
    rongali-2018 (default), OR provide emissivity_10 and emissivity_11.
    Kerr additionally needs red/nir or prepared ndvi_image with either route.
    Prepared emissivity with optical bands is accepted only for Kerr NDVI;
    The optical route always uses Rongali; select another model separately
    with emissivity(method=...) and supply the prepared emissivity arrays.
    PWV is g/cm2; unit selects kelvin/celsius. Diagnostics preserve NDVI,
    emissivities and source conditions; NDVI is None if unused/unavailable.


    Quality inputs
    --------------
    Before this calculation, call quality_mask(qa_pixel_path,
    qa_radsat_path, reference_path=...) and pass the aligned boolean result
    combined with input nodata as mask=. True means invalid. QA files are
    not read by this numerical function; mask=None applies no QA screening.
    LandsatScene.calibrated() prepares and returns its QA mask automatically.
    """
    from .provenance import optical_contract
    optical_contract("rongali-2018", optical_quantity)
    if not isinstance(return_diagnostics, (bool, np.bool_)):
        raise ValueError("return_diagnostics must be boolean.")
    diagnostic = validate_quality_mode(quality_mode)
    if not diagnostic and not return_diagnostics and pwv_quality_flags is not None:
        raise ValueError('pwv_quality_flags requires return_diagnostics=True or quality_mode="diagnostic".')
    normalized_unit = normalize_temperature_unit(unit)
    key = split_window_registry.resolve_key(method)
    algorithm = split_window_registry.create(key)
    t10 = to_float_array("brightness_band_10", brightness_band_10)
    t11 = to_float_array("brightness_band_11", brightness_band_11)
    ensure_same_shape(brightness_band_10=t10, brightness_band_11=t11)
    invalid = build_mask_from(t10, t11)
    if mask is not None:
        invalid |= ensure_boolean_mask(mask, shape=t10.shape)
    prepared = emissivity_10 is not None or emissivity_11 is not None
    if prepared:
        if emissivity_10 is None or emissivity_11 is None:
            raise ValueError("Supply both emissivity_10 and emissivity_11.")
        if key != "kerr-1992" and any(v is not None for v in (band_4_red, band_5_nir, ndvi_image)):
            raise ValueError("Prepared emissivities do not use optical/NDVI inputs except for Kerr.")
        e10 = to_float_array("emissivity_10", emissivity_10)
        e11 = to_float_array("emissivity_11", emissivity_11)
        ensure_same_shape(brightness_band_10=t10, emissivity_10=e10, emissivity_11=e11)
        n = None
        if key == "kerr-1992":
            n = _resolve_ndvi(ndvi_image, red=band_4_red, nir=band_5_nir, mask=invalid)
            ensure_same_shape(brightness_band_10=t10, ndvi_image=n)
        contract = optical_contract("kerr-1992" if key == "kerr-1992" else "prepared-emissivity", optical_quantity,
                                    family="split_window" if key == "kerr-1992" else "emissivity")
        contract["emissivity_source"] = "caller supplied; band/sensor provenance required"
    else:
        if band_4_red is None or band_5_nir is None:
            raise ValueError("Supply red/nir bands or a prepared emissivity pair.")
        if ndvi_image is not None:
            raise ValueError("NDVI is computed internally from red/nir; do not supply ndvi_image too.")
        red = to_float_array("band_4_red", band_4_red)
        nir = to_float_array("band_5_nir", band_5_nir)
        ensure_same_shape(brightness_band_10=t10, band_4_red=red, band_5_nir=nir)
        invalid |= ~np.isfinite(red) | ~np.isfinite(nir)
        n = _ndvi(nir=nir, red=red, mask=invalid)
        e10, e11 = _emissivity_pair(n, band_4_red=red, method="rongali-2018")
        contract = optical_contract("kerr-1992" if key == "kerr-1992" else "rongali-2018", optical_quantity,
                                    family="split_window" if key == "kerr-1992" else "emissivity")
    if water_vapor is not None and key in {"price-1984", "kerr-1992", "sobrino-1993"}:
        warnings.warn(f"split_window(method='{key}'): water_vapor is not used by this equation; the supplied value will be ignored.", UnusedParameterWarning, stacklevel=2)
    parameters = dict(brightness_temperature_10=t10,brightness_temperature_11=t11,
        emissivity_10=e10,emissivity_11=e11,ndvi=n,mask=invalid,water_vapor=water_vapor)
    result = algorithm(**parameters,diagnostic=True) if (diagnostic or return_diagnostics) else algorithm(**parameters)
    if diagnostic or return_diagnostics:
        screened_parameters = dict(parameters)
        domains={'du-2015':(0,6.3),'jimenez-munoz-2014':(0,6)}
        if diagnostic and water_vapor is not None and key in domains:
            screened_parameters['water_vapor']=np.broadcast_to(np.asarray(water_vapor,dtype=float),t10.shape)
        screened=algorithm(**screened_parameters)
        raw_output=result if normalized_unit=='kelvin' else result-CELSIUS_SCALER
        screened_output=screened if normalized_unit=='kelvin' else screened-CELSIUS_SCALER
        quality=temperature_quality(result,screened,invalid,water_vapor=water_vapor,
            domain=domains.get(key),upstream=pwv_quality_flags,
            legacy=key in {'price-1984','kerr-1992','sobrino-1993'},du=key=='du-2015')
        return annotate(dict(lst=raw_output if diagnostic else screened_output,
            raw_lst=raw_output,screened_lst=screened_output,
            ndvi=n,emissivity_10=e10,emissivity_11=e11,invalid_mask=~np.isfinite(raw_output if diagnostic else screened_output),
            units=normalized_unit,optical_contract=contract,**quality),
            family="split_window", method=key, units=normalized_unit, quality_mode=quality_mode,
            input_temperature_units="kelvin", water_vapor_units="g/cm2", water_vapor=water_vapor,
            optical_quantity=optical_quantity, optical_contract=contract)
    output = result if normalized_unit == "kelvin" else result-CELSIUS_SCALER
    return output


@contextual_errors
def water_vapor(
    brightness_band_10,
    brightness_band_11,
    ndvi_image=None,
    method: str = "wang-2015",
    window_size: int | None = None,
    group_count: int = 3,
    *, red=None, nir=None, mask=None, ndvi_range=None, chunk_rows=8,
    min_samples=10, quality_threshold=.95, ndvi_filter=True, return_diagnostics=False,
    quality_mode="screened",
) -> np.ndarray | dict[str, np.ndarray]:
    """Estimate scene-derived PWV [g/cm2] using Wang or Ren.

    quality_mode="diagnostic" returns a dictionary for either method, with
    raw water_vapor, screened_water_vapor, quality_flags and continuous
    quality/sample diagnostics. Operational rejection becomes flags; explicit
    masks and mathematical impossibilities remain NaN. See diagnostic-quality.md.

    Wang keeps its 21-pixel default and global NDVI grouping. Ren defaults
    to 11 pixels, local NDVI filtering and mean-centered Eq.1b/2; use 33
    pixels for about 1 km support on Landsat's resampled 30-m grid.
    Ren-only controls: min_samples, quality_threshold and ndvi_filter.
    return_diagnostics is supported by both estimators.
    Supply red/nir to compute NDVI internally. A prepared ndvi_image may
    be supplied instead; never mix the two input forms.
    No PWV is estimated implicitly by split_window().


    Quality inputs
    --------------
    Before this calculation, call quality_mask(qa_pixel_path,
    qa_radsat_path, reference_path=...) and pass the aligned boolean result
    combined with input nodata as mask=. True means invalid. QA files are
    not read by this numerical function; mask=None applies no QA screening.
    LandsatScene.calibrated() prepares and returns its QA mask automatically.
    """
    return_diagnostics = ensure_bool("return_diagnostics", return_diagnostics)
    ndvi_filter = ensure_bool("ndvi_filter", ndvi_filter)
    diagnostic = validate_quality_mode(quality_mode)
    details = diagnostic or return_diagnostics
    key = water_vapor_registry.resolve_key(method)
    if key == "wang-2015" or ndvi_filter or ndvi_image is not None or red is not None or nir is not None:
        ndvi_image = _resolve_ndvi(ndvi_image, red=red, nir=nir, mask=mask)
    size = (11 if key == "ren-2015" else 21) if window_size is None else window_size
    if key == "ren-2015":
        if ndvi_range is not None or group_count != 3:
            raise ValueError("Ren uses local NDVI screening, not Wang group_count/ndvi_range.")
        result = water_vapor_registry.create(key)(
            brightness_band_10=brightness_band_10,brightness_band_11=brightness_band_11,
            ndvi_image=ndvi_image,window_size=size,
            mask=mask,chunk_rows=chunk_rows,min_samples=min_samples,
            quality_threshold=quality_threshold,ndvi_filter=ndvi_filter,
            return_diagnostics=details,diagnostic=details)
    else:
        if min_samples != 10 or quality_threshold != .95 or not ndvi_filter:
            raise ValueError("min_samples, quality_threshold and ndvi_filter apply to Ren only.")
        result = water_vapor_registry.create(key)(
            brightness_band_10=brightness_band_10,brightness_band_11=brightness_band_11,
            ndvi_image=ndvi_image,window_size=size,
            group_count=group_count,mask=mask,ndvi_range=ndvi_range,chunk_rows=chunk_rows,diagnostic=details)
    if not details:
        return result
    result["water_vapor"] = result["raw_water_vapor"] if diagnostic else result["screened_water_vapor"]
    return annotate(result, family="water_vapor", method=key, units="g/cm2", quality_mode=quality_mode,
        window_size=size, group_count=group_count if key=="wang-2015" else None,
        min_samples=min_samples if key=="ren-2015" else 2,
        quality_threshold=quality_threshold if key=="ren-2015" else .97,
        ndvi_filter=ndvi_filter if key=="ren-2015" else True, ndvi_range=ndvi_range,
        input_temperature_units="kelvin")




def list_algorithms(*, include_inactive=False) -> dict:
    """
    Return metadata for methods in the main workflow.

    include_inactive is retained for call compatibility; all available methods
    are active and both catalog views contain the same methods.
    """
    catalog = {"credit": {"original_library": ORIGINAL_LIBRARY_CREDIT}}

    for family_name, registry in FAMILY_REGISTRIES.items():
        catalog[family_name] = {
            key: {
                "name": metadata.name,
                "reference": metadata.reference,
                "citation": metadata.citation,
                **describe_source_contract(family_name, key),
                "input_requirements": describe_inputs(family_name, key),
                "water_vapor_support": PWV_SUPPORT.get((family_name, key), "Not an atmospheric PWV-dependent LST method."),
                "scientific_status": (
                    "Legacy AVHRR coefficients; unvalidated Landsat adaptation"
                    if key in {"price-1984", "kerr-1992", "sobrino-1993"} else
                    "Landsat-8 formulation; Landsat-9 transfer experimental; no ground-truth validation"
                    if family_name in {"single_channel", "split_window", "water_vapor", "emissivity"} else
                    "See docs/scientific-methods.md for calibration and input contracts"
                ),
            }
            for key, metadata in registry.describe().items()
        }

    # Function-dispatched models share the reviewed source cards; no numerical
    # implementation or coefficient table is duplicated in the catalog.
    from .provenance import _card
    for family, key, source in (("optical_correction", "chavez-dos-1996", "chavez-dos-1996"),
            ("optical_correction", "chavez-cost-1996", "chavez-cost-1996")):
        card = _card(family, source)
        item = dict(name=key, reference=card["reference"], citation=card["reference"],
            source_sensor=card["sensor"], source_location=card["source_location"],
            optical_input_contract=card["optical_contract"],
            source_review_status=card["source_review_status"],
            numerical_evidence=card["numerical_evidence"],
            empirical_accuracy=card["empirical_accuracy"],
            evidence=card["evidence"],
            input_requirements=card["inputs"]+" QA preparation: quality_mask(qa_pixel_path, qa_radsat_path, reference_path=...); pass the combined QA/nodata mask as mask= BEFORE fitting dark-object parameters.", scientific_status=card["decisions"],
            water_vapor_support="Not used")
        catalog.setdefault(family, {})[key] = item

    for family, entries in catalog.items():
        if family != "credit":
            for item in entries.values():
                item["workflow_status"] = "active"
    return catalog
