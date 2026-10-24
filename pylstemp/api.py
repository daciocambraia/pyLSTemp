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
from .calibration import brightness, normalize_thermal_band as _normalize_thermal_band
from .utils import _compute_ndvi as _ndvi, _resolve_ndvi
from .algorithms.water_vapor import water_vapor_registry
from .references import ORIGINAL_LIBRARY_CREDIT
from .validation import (
    build_mask_from,
    ensure_same_shape,
    ensure_boolean_mask,
    normalize_temperature_unit,
    to_float_array,
)

CELSIUS_SCALER = 273.15
SINGLE_CHANNEL_EMISSIVITY_METHODS = {"avdan-2016"}


def _emissivity_pair(ndvi_image, band_4_red=None, emissivity_method: str = "avdan-2016"):
    """
    Compute Band 10 and Band 11 emissivity from NDVI.

    Parameters
    ----------
    ndvi_image : array-like
        NDVI image used by the emissivity method.
    band_4_red : array-like, optional
        Red band image required by selected methods.
    emissivity_method : str, default="avdan-2016"
        Registered emissivity method key.

    Returns
    -------
    tuple of ndarray
        Emissivity arrays for Band 10 and Band 11.
    """
    ndvi_array = to_float_array("ndvi_image", ndvi_image)
    validated_red_band = None if band_4_red is None else to_float_array("band_4_red", band_4_red)
    ensure_same_shape(ndvi_image=ndvi_array, band_4_red=validated_red_band)

    algorithm = emissivity_registry.create(emissivity_method)
    return algorithm(ndvi=ndvi_array, red_band=validated_red_band)


@contextual_errors
def emissivity_band_10(ndvi_image, band_4_red=None, emissivity_method: str = "avdan-2016"):
    """
    Compute emissivity for the Band 10 thermal workflow.

    Parameters
    ----------
    ndvi_image : array-like
        NDVI image used by the emissivity method.
    band_4_red : array-like, optional
        Red band image required by selected methods.
    emissivity_method : str, default="avdan-2016"
        Registered emissivity method key.

    Returns
    -------
    ndarray
        Band 10 emissivity image.
    """

    emissivity_10, _ = _emissivity_pair(
        ndvi_image,
        band_4_red=band_4_red,
        emissivity_method=emissivity_method,
    )
    return emissivity_10


@contextual_errors
def emissivity_band_11(ndvi_image, band_4_red=None, emissivity_method: str = "avdan-2016"):
    """
    Compute emissivity for the Band 11 thermal workflow.

    Parameters
    ----------
    ndvi_image : array-like
        NDVI image used by the emissivity method.
    band_4_red : array-like, optional
        Red band image required by selected methods.
    emissivity_method : str, default="avdan-2016"
        Registered emissivity method key.

    Returns
    -------
    ndarray
        Band 11 emissivity image.
    """

    _, emissivity_11 = _emissivity_pair(
        ndvi_image,
        band_4_red=band_4_red,
        emissivity_method=emissivity_method,
    )
    return emissivity_11


@contextual_errors
def emissivity(ndvi_image=None, band=None, band_4_red=None, emissivity_method=None,
               *, method=None, red=None, nir=None, mask=None, variant=None,
               soil_emissivity=None, vegetation_emissivity=None, red_surface=None,
               soil_red_coefficients=None, cavity_factor=None, vegetation_cavity=None,
               ndvi_soil=None, ndvi_vegetation=None):
    """Estimate emissivity with one method selector and internal NDVI.

    method: avdan-2016 (default), gopinadh-2018, sobrino-2004-tm6 or
    sobrino-2008. band defaults to 6 for TM6, 10 otherwise. Sobrino 2008
    requires band-compatible soil/vegetation emissivities; variant is
    simplified (default) or full. Full also requires red_surface and (a,b).
    Emissivity is dimensionless. NDVI and masks must share the input grid.
    emissivity_method is a compatibility keyword; do not combine with method.
    """
    if method is not None and emissivity_method is not None:
        raise ValueError("Use method only; do not combine it with emissivity_method.")
    selected = method if method is not None else emissivity_method
    key = emissivity_registry.resolve_key("avdan-2016" if selected is None else selected)
    n = _resolve_ndvi(ndvi_image, red=red, nir=nir, mask=mask)
    options = dict(variant=variant, soil_emissivity=soil_emissivity,
        vegetation_emissivity=vegetation_emissivity, red_surface=red_surface,
        soil_red_coefficients=soil_red_coefficients, cavity_factor=cavity_factor,
        vegetation_cavity=vegetation_cavity, ndvi_soil=ndvi_soil,
        ndvi_vegetation=ndvi_vegetation)
    if band_4_red is not None:
        ensure_same_shape(ndvi=n, band_4_red=to_float_array("band_4_red", band_4_red))
    if key == "sobrino-2004-tm6":
        if band not in (None, 6, "6", "b6", "band_6") or isinstance(band, (bool, np.bool_)):
            raise ValueError("sobrino-2004-tm6 is calibrated for Landsat5 TM band6, not TIRS10/11.")
        if any(v is not None for v in options.values()) or band_4_red is not None:
            raise ValueError("TM6 does not use Sobrino2008 options or band_4_red.")
        from .emissivity_models import _sobrino_2004_tm6
        return _sobrino_2004_tm6(n, mask=mask)
    if key == "sobrino-2008":
        if band is not None and (isinstance(band,(bool,np.bool_)) or
                not isinstance(band,(int,np.integer)) or band < 1):
            raise ValueError("For Sobrino2008, band must be a positive integer identifying the supplied endmembers.")
        if band_4_red is not None:
            raise ValueError("Use red_surface for the full Sobrino2008 soil relation.")
        if soil_emissivity is None or vegetation_emissivity is None:
            raise ValueError("sobrino-2008 requires band-compatible soil_emissivity and vegetation_emissivity.")
        if variant != "full" and any(v is not None for v in
                (cavity_factor, vegetation_cavity)):
            raise ValueError("Cavity controls require Sobrino2008 variant='full'.")
        from .emissivity_models import _sobrino_2008
        supplied = {k:v for k,v in options.items() if v is not None}
        return _sobrino_2008(n, mask=mask, **supplied)
    if any(v is not None for v in options.values()):
        raise ValueError("Sobrino2008 parameters apply only to method='sobrino-2008'.")
    normalized_band = _normalize_thermal_band(10 if band is None else band)
    pair = _emissivity_pair(n, band_4_red=band_4_red, emissivity_method=key)
    return pair[0 if normalized_band == "band_10" else 1]


@contextual_errors
def single_window(
    brightness_band_10,
    band_4_red,
    band_5_nir,
    lst_method: str = "mono-window-2016",
    emissivity_method: str = "avdan-2016",
    unit: str = "kelvin",
    *, mask=None, radiance_band_10=None, water_vapor=None,
    return_diagnostics=False, optical_quantity=None,
) -> np.ndarray | dict:
    """
    Compute land surface temperature using a single-channel method.

    This workflow expects brightness temperature for thermal band 10 to be
    computed beforehand with `brightness(..., band="band_10")`.

    Parameters
    ----------
    brightness_band_10 : array-like
        Brightness temperature image for thermal band 10, in Kelvin.
    band_4_red : array-like
        Red band image used to compute NDVI internally.
    band_5_nir : array-like
        Near-infrared band image used to compute NDVI internally.
    lst_method : str, default="mono-window-2016"
        Single-channel LST method to use.
    emissivity_method : str, default="avdan-2016"
        Emissivity method used before LST computation.
    unit : {"kelvin", "celsius"}, default="kelvin"
        Output temperature unit.

    radiance_band_10 : array-like, optional
        Band-10 TOA radiance [W m-2 sr-1 um-1], required for jimenez-munoz-2014-sc.
        Must correspond to the same band, pixels and calibration as brightness_band_10.
    water_vapor : float or array-like, optional
        Required for jimenez-munoz-2014-sc, in g/cm2. Scalar range [0,3];
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
    - mono-window-2016 does not accept radiance_band_10 or water_vapor.

    Examples
    --------
    >>> from pylstemp import single_window
    >>> lst = single_window(
    ...     brightness_band_10=brightness_10,
    ...     band_4_red=red,
    ...     band_5_nir=nir,
    ...     lst_method="mono-window-2016",
    ...     unit="celsius",
    ... )
    """
    from .provenance import optical_contract
    optical_contract(emissivity_method, optical_quantity)
    if not isinstance(return_diagnostics, (bool, np.bool_)):
        raise ValueError("return_diagnostics must be boolean.")
    normalized_unit = normalize_temperature_unit(unit)

    brightness_10 = to_float_array("brightness_band_10", brightness_band_10)
    red = to_float_array("band_4_red", band_4_red)
    nir = to_float_array("band_5_nir", band_5_nir)
    ensure_same_shape(
        brightness_band_10=brightness_10,
        band_4_red=red,
        band_5_nir=nir,
    )

    user_mask = mask
    mask = build_mask_from(brightness_10) | ~np.isfinite(red) | ~np.isfinite(nir)
    if user_mask is not None:
        mask |= ensure_boolean_mask(user_mask, shape=brightness_10.shape)
    ndvi_image = _ndvi(nir=nir, red=red, mask=mask)
    emissivity_10 = emissivity_band_10(ndvi_image, band_4_red=red, emissivity_method=emissivity_method)

    key = single_channel_registry.resolve_key(lst_method)
    extra = {}
    if key == "jimenez-munoz-2014-sc":
        extra = dict(radiance_band_10=radiance_band_10, water_vapor=water_vapor)
    elif radiance_band_10 is not None or water_vapor is not None:
        raise ValueError(f"single_window(lst_method={key!r}): radiance_band_10 and "
                         "water_vapor are only used by jimenez-munoz-2014-sc.")
    result = single_channel_registry.create(key)(
        emissivity_10=emissivity_10,
        brightness_temperature_10=brightness_10,
        mask=mask,
        **extra,
    )
    output = result if normalized_unit == "kelvin" else result - CELSIUS_SCALER
    if return_diagnostics:
        from .provenance import optical_contract
        return dict(lst=output, ndvi=ndvi_image, emissivity_10=emissivity_10,
                    invalid_mask=~np.isfinite(output), units=normalized_unit,
                    optical_contract=optical_contract(emissivity_method, optical_quantity))
    return output


@contextual_errors
def split_window(brightness_band_10, brightness_band_11, band_4_red=None,
                 band_5_nir=None, lst_method=None, emissivity_method=None,
                 unit="kelvin", water_vapor=None, *, emissivity_10=None,
                 emissivity_11=None, ndvi_image=None, mask=None,
                 atmospheric_profile=None, temperature_range="0-60",
                 return_diagnostics=False, optical_quantity=None):
    """Compute SW LST from BT10/BT11 [K] and ONE emissivity input route.

    Provide calibrated red/nir to estimate band-specific emissivity with
    gopinadh-2018 (default), OR provide emissivity_10 and emissivity_11.
    Kerr additionally needs red/nir or prepared ndvi_image with either route.
    Prepared emissivity with optical bands is accepted only for Kerr NDVI;
    emissivity_method cannot be combined with prepared emissivities.
    PWV is g/cm2; unit selects kelvin/celsius. Diagnostics preserve NDVI,
    emissivities and source conditions; NDVI is None if unused/unavailable.
    """
    from .provenance import optical_contract
    optical_contract("gopinadh-2018", optical_quantity)
    if not isinstance(return_diagnostics, (bool, np.bool_)):
        raise ValueError("return_diagnostics must be boolean.")
    normalized_unit = normalize_temperature_unit(unit)
    key = split_window_registry.resolve_key(lst_method)
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
        if emissivity_method is not None:
            raise ValueError("Prepared emissivities cannot be combined with emissivity_method.")
        if key != "kerr-1992" and any(v is not None for v in (band_4_red, band_5_nir, ndvi_image)):
            raise ValueError("Prepared emissivities do not use optical/NDVI inputs except for Kerr.")
        e10 = to_float_array("emissivity_10", emissivity_10)
        e11 = to_float_array("emissivity_11", emissivity_11)
        ensure_same_shape(brightness_band_10=t10, emissivity_10=e10, emissivity_11=e11)
        n = None
        if key == "kerr-1992":
            n = _resolve_ndvi(ndvi_image, red=band_4_red, nir=band_5_nir, mask=invalid)
            ensure_same_shape(brightness_band_10=t10, ndvi_image=n)
        contract = optical_contract("kerr-1992" if key == "kerr-1992" else "prepared-emissivity", optical_quantity)
        contract["emissivity_source"] = "caller supplied; band/sensor provenance required"
    else:
        if band_4_red is None or band_5_nir is None:
            raise ValueError("Supply red/nir bands or a prepared emissivity pair.")
        if ndvi_image is not None:
            raise ValueError("NDVI is computed internally from red/nir; do not supply ndvi_image too.")
        method = "gopinadh-2018" if emissivity_method is None else emissivity_method
        method = emissivity_registry.resolve_key(method)
        if method in SINGLE_CHANNEL_EMISSIVITY_METHODS:
            raise ValueError(f"'{method}' is a single-channel emissivity method and cannot be used with split_window().")
        red = to_float_array("band_4_red", band_4_red)
        nir = to_float_array("band_5_nir", band_5_nir)
        ensure_same_shape(brightness_band_10=t10, band_4_red=red, band_5_nir=nir)
        invalid |= ~np.isfinite(red) | ~np.isfinite(nir)
        n = _ndvi(nir=nir, red=red, mask=invalid)
        e10, e11 = _emissivity_pair(n, band_4_red=red, emissivity_method=method)
        contract = optical_contract("kerr-1992" if key == "kerr-1992" else method, optical_quantity)
    if water_vapor is not None and key in {"price-1984", "kerr-1992", "sobrino-1993"}:
        warnings.warn(f"split_window(lst_method='{key}'): water_vapor is not used by this equation; the supplied value will be ignored.", RuntimeWarning, stacklevel=2)
    extra = {}
    if key == "rozenstein-2014":
        extra = dict(atmospheric_profile=atmospheric_profile, temperature_range=temperature_range)
    elif atmospheric_profile is not None or temperature_range != "0-60":
        raise ValueError("Atmospheric profile and temperature_range apply only to rozenstein-2014.")
    result = algorithm(brightness_temperature_10=t10, brightness_temperature_11=t11,
        emissivity_10=e10, emissivity_11=e11, ndvi=n, mask=invalid,
        water_vapor=water_vapor, **extra)
    output = result if normalized_unit == "kelvin" else result-CELSIUS_SCALER
    if return_diagnostics:
        return dict(lst=output, ndvi=n, emissivity_10=e10, emissivity_11=e11,
                    invalid_mask=~np.isfinite(output), units=normalized_unit,
                    optical_contract=contract)
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
) -> np.ndarray | dict[str, np.ndarray]:
    """Estimate scene-derived PWV [g/cm2] using Wang or Ren.

    Wang keeps its 21-pixel default and global NDVI grouping. Ren defaults
    to 11 pixels, local NDVI filtering and mean-centered Eq.1b/2; use 33
    pixels for about 1 km support on Landsat's resampled 30-m grid.
    Ren-only controls: min_samples, quality_threshold, ndvi_filter,
    return_diagnostics. Ren diagnostics return a dictionary of aligned arrays.
    Supply red/nir to compute NDVI internally. A prepared ndvi_image may
    be supplied instead; never mix the two input forms.
    No PWV is estimated implicitly by split_window().
    """
    key = water_vapor_registry.resolve_key(method)
    if key == "wang-2015" or ndvi_filter or ndvi_image is not None or red is not None or nir is not None:
        ndvi_image = _resolve_ndvi(ndvi_image, red=red, nir=nir, mask=mask)
    if key == "ren-2015":
        if ndvi_range is not None or group_count != 3:
            raise ValueError("Ren uses local NDVI screening, not Wang group_count/ndvi_range.")
        return water_vapor_registry.create(key)(
            brightness_band_10=brightness_band_10,brightness_band_11=brightness_band_11,
            ndvi_image=ndvi_image,window_size=11 if window_size is None else window_size,
            mask=mask,chunk_rows=chunk_rows,min_samples=min_samples,
            quality_threshold=quality_threshold,ndvi_filter=ndvi_filter,
            return_diagnostics=return_diagnostics)
    if min_samples != 10 or quality_threshold != .95 or not ndvi_filter or return_diagnostics:
        raise ValueError("min_samples, quality_threshold, ndvi_filter and diagnostics apply to Ren only.")
    return water_vapor_registry.create(key)(
        brightness_band_10=brightness_band_10,brightness_band_11=brightness_band_11,
        ndvi_image=ndvi_image,window_size=21 if window_size is None else window_size,
        group_count=group_count,mask=mask,ndvi_range=ndvi_range,chunk_rows=chunk_rows)



def list_algorithms() -> dict:
    """
    Return metadata for all available family-dispatched methods.

    Returns
    -------
    dict
        Catalog containing each algorithm family, method key, display name,
        reference, citation, source conditions, optical convention and
        original-library credit. Source-review status is distinct from tests.

    Examples
    --------
    >>> from pylstemp import list_algorithms
    >>> catalog = list_algorithms()
    >>> "du-2015" in catalog["split_window"]
    True
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
                "water_vapor_support": PWV_SUPPORT.get(key, "Not an atmospheric PWV-dependent LST method."),
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
    from .provenance import _cards
    cards = {card["method"]: card for card in _cards()}
    for family, key, source in (("emissivity", "sobrino-2004-tm6", "sobrino-2004-tm6"),
            ("emissivity", "sobrino-2008", "sobrino-2008-simplified"),
            ("optical_correction", "chavez-dos", "chavez-dos"),
            ("optical_correction", "chavez-cost", "chavez-cost")):
        card = cards[source]
        item = dict(name=key, reference=card["reference"], citation=card["reference"],
            source_sensor=card["sensor"], source_location=card["source_location"],
            optical_input_contract=card["optical_contract"],
            source_review_status=card["source_review_status"],
            input_requirements=card["inputs"], scientific_status=card["decisions"],
            water_vapor_support="Not used")
        if key == "sobrino-2008":
            item["variants"] = ["simplified", "full"]
            item["variant_input_requirements"] = {variant: cards["sobrino-2008-"+variant]["inputs"] for variant in item["variants"]}
            item["variant_source_locations"] = {variant: cards["sobrino-2008-"+variant]["source_location"] for variant in item["variants"]}
        catalog.setdefault(family, {})[key] = item

    return catalog
