# References

This rebuild keeps the conversion methods tied to the references listed by the original `pylandtemp` project and by the current modular implementations.

## Original project credit

- Original project: <https://github.com/pylandtemp/pylandtemp>
- Original author: Oladimeji Mudele

## Vegetation

- `ndvi`
  Rouse, J. W., Haas, R. H., Schell, J. A., and Deering, D. W. Monitoring vegetation systems in the Great Plains with ERTS. NASA SP-351, 1974.
- `evi`
  Huete, A. R., Liu, H. Q., Batchily, K., and van Leeuwen, W. A comparison of vegetation indices over a global set of TM images for EOS-MODIS. Remote Sensing of Environment, 1997.
  The article names this equation SARVI2; pyLSTemp exposes it as EVI because the implemented coefficients match the common enhanced vegetation index structure: `2.5 * ((NIR - RED) / (NIR + 6 * RED - 7.5 * BLUE + 1))`.

## Thermal

- `brightness`
  Brightness temperature conversion using scene-specific radiance gain and bias supplied in the function call together with sensor-specific `K1` and `K2` constants for Landsat 8 or Landsat 9.

## Single-channel temperature algorithms

- `mono-window-2016`
  Avdan, U., and Jovanovska, G. Algorithm for automated mapping of land surface temperature using LANDSAT 8 satellite data. Journal of Sensors, 2016.
  This is a Band 10 single-channel workflow. The implementation uses `lambda=10.895e-6 m`, calculated as the midpoint of the Landsat 8/9 TIRS Band 10 range (`10.6-11.19 um`).

## Split-window temperature algorithms

- `jimenez-munoz-2014`
  - **Reference:** Jimenez-Munoz et al. (2014)
  - **Title:** Land surface temperature retrieval methods from Landsat-8 thermal infrared sensor data
  - **Journal:** IEEE Geoscience and Remote Sensing Letters, 2015, vol.11, n.10, 1840-1843
  - **DOI:** [10.1109/LGRS.2014.2312032](https://doi.org/10.1109/LGRS.2014.2312032)

- `du-2015`
  - **Reference:** Du et al. (2015)
  - **Title:** A practical split-window algorithm for estimating land surface temperature from Landsat 8 data
  - **Journal:** Remote Sensing, vol.7, n.1, 2015, 647-665
  - **DOI:** [10.3390/rs70100647](https://doi.org/10.3390/rs70100647)

- `sobrino-1993`
  - **Reference:** Sobrino, J.A., Caselles, V., Coll, C.
  - **Title:** Theoretical split-window algorithms for determining the actual surface temperature
  - **Journal:** Il Nuovo Cimento, vol.C16, n.3, 1993, 219-236
  - **DOI:** [10.1007/BF02524225](https://doi.org/10.1007/BF02524225)

- `kerr-1992`
  - **Reference:** Kerr, Y.H., Lagouarde, J.P., Imbernon, J.
  - **Title:** Accurate land surface temperature retrieval from AVHRR data with use of an improved split window algorithm
  - **Journal:** Remote Sensing of Environment, v.41, n.2-3, 1992, 197-209
  - **DOI:** [10.1016/0034-4257(92)90078-X](https://doi.org/10.1016/0034-4257(92)90078-X)
  - **Observation:** The implementation interpolates the paper's bare-soil and vegetation coefficients using the linear NDVI cover from the article, with `NDVIbs=0.11` and `NDVIv=0.72` cited from Begue (1991).

- `price-1984`
  - **Reference:** Price, J.C.
  - **Title:** Land surface temperature measurements from the split window channels of the NOAA advanced very high-resolution radiometer
  - **Journal:** Journal of Geophysical Research, 1984
  - **DOI:** [10.1029/JD089iD05p07231](https://doi.org/10.1029/JD089iD05p07231)

## Emissivity algorithms

- `avdan-2016`
  Avdan, U., and Jovanovska, G. Algorithm for automated mapping of land surface temperature using LANDSAT 8 satellite data. Journal of Sensors, 2016.
  Emissivity follows the article's NDVI conditional rules, including `C=0.005` for mixed pixels.
- `xiaolei-2014`
  Yu, X., Guo, X., and Wu, Z. Land surface temperature retrieval from Landsat 8 TIRS - comparison between radiative transfer equation-based method, split window algorithm and single channel method. Remote Sensing, 2014.
- `gopinadh-2018`
  Rongali, G., et al. Split-window algorithm for retrieval of land surface temperature using Landsat 8 thermal infrared data. Journal of Geovisualization and Spatial Analysis, 2018.

## Water vapor algorithms

- `wang-2015`
  Wang, M., He, G., Zhang, Z., Wang, G., and Long, T. NDVI-based split-window algorithm for precipitable water vapour retrieval from Landsat-8 TIRS data over land area. Remote Sensing Letters, 2015.

## Radiative transfer

This family is currently reserved for future methods.
