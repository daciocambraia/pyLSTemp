"""Bibliographic metadata and original project attribution."""

ORIGINAL_LIBRARY_CREDIT = (
    "Original library credit: pylandtemp by Oladimeji Mudele "
    "(https://github.com/pylandtemp/pylandtemp)."
)

TEMPERATURE_REFERENCES = {
    "mono-window": {
        "name": "Mono-window LST",
        "reference": "Avdan and Jovanovska (2016)",
        "citation": (
            "Avdan, U., and Jovanovska, G. Algorithm for automated mapping of "
            "land surface temperature using LANDSAT 8 satellite data. Journal "
            "of Sensors, 2016."
        ),
    },
    "jiminez-munoz": {
        "name": "Jiminez-Munoz split-window LST",
        "reference": "Jimenez-Munoz and Sobrino (2008)",
        "citation": (
            "Jimenez-Munoz, J.-C., and Sobrino, J. A. Split-window coefficients "
            "for land surface temperature retrieval from low-resolution thermal "
            "infrared sensors. IEEE Geoscience and Remote Sensing Letters, 2008."
        ),
    },
    "kerr": {
        "name": "Kerr split-window LST",
        "reference": "Kerr et al. (2004)",
        "citation": (
            "Kerr, Y., Lagouarde, J., Nerry, F., and Ottle, C. Land surface "
            "temperature retrieval techniques and applications: case of the AVHRR. "
            "Thermal Remote Sensing in Land Surface Processing, 2004."
        ),
    },
    "mc-millin": {
        "name": "McMillin split-window LST",
        "reference": "McMillin (1975)",
        "citation": (
            "McMillin, L. M. Estimation of sea surface temperatures from two "
            "infrared window measurements with different absorption. Journal of "
            "Geophysical Research, 1975."
        ),
    },
    "price": {
        "name": "Price split-window LST",
        "reference": "Price (1984)",
        "citation": (
            "Price, J. C. Land surface temperature measurements from the split "
            "window channels of the NOAA advanced very high-resolution radiometer. "
            "Journal of Geophysical Research, 1984."
        ),
    },
    "sobrino-1993": {
        "name": "Sobrino 1993 split-window LST",
        "reference": "Sobrino et al. (1993)",
        "citation": (
            "Sobrino, J. A., Caselles, V., and Coll, C. Theoretical split window "
            "algorithms for determining the actual surface temperature. Il Nuovo "
            "Cimento, 1993."
        ),
    },
}

EMISSIVITY_REFERENCES = {
    "avdan": {
        "name": "Avdan emissivity",
        "reference": "Avdan and Jovanovska (2016)",
        "citation": (
            "Avdan, U., and Jovanovska, G. Algorithm for automated mapping of "
            "land surface temperature using LANDSAT 8 satellite data. Journal "
            "of Sensors, 2016."
        ),
    },
    "xiaolei": {
        "name": "Xiaolei emissivity",
        "reference": "Yu, Guo and Wu (2014)",
        "citation": (
            "Yu, X., Guo, X., and Wu, Z. Land surface temperature retrieval from "
            "Landsat 8 TIRS - comparison between radiative transfer equation-based "
            "method, split window algorithm and single channel method. Remote "
            "Sensing, 2014."
        ),
    },
    "gopinadh": {
        "name": "Gopinadh emissivity",
        "reference": "Rongali et al. (2018)",
        "citation": (
            "Rongali, G., et al. Split-window algorithm for retrieval of land "
            "surface temperature using Landsat 8 thermal infrared data. Journal "
            "of Geovisualization and Spatial Analysis, 2018."
        ),
    },
}

