# References

This rebuild keeps the conversion methods tied to the references listed by the original `pylandtemp` project and by the current modular implementations.

## Original project credit

- Original project: <https://github.com/pylandtemp/pylandtemp>
- Original author: Oladimeji Mudele

## Internal vegetation calculation

- Internal NDVI, shared by retained workflows (not a public algorithm)
  Rouse, J. W., Haas, R. H., Schell, J. A., and Deering, D. W. Monitoring vegetation systems in the Great Plains with ERTS. NASA SP-351, 1974.
## Thermal

- `brightness`
  TOA radiance to TOA brightness temperature using band-specific K1/K2 from the matching MTL. DN-to-radiance uses per-band gain/bias first.
  [USGS Level-1 calibration equations](https://www.usgs.gov/landsat-missions/using-usgs-landsat-level-1-data-product).

## Single-channel temperature algorithms

- `mono-window-2016`
  Avdan, U., and Jovanovska, G. Algorithm for automated mapping of land surface temperature using LANDSAT 8 satellite data. Journal of Sensors, 2016.
  This is a Band 10 single-channel workflow. The implementation uses `lambda=10.895e-6 m`, calculated as the midpoint of the Landsat 8/9 TIRS Band 10 range (`10.6-11.19 um`).

- `jimenez-munoz-2014-sc`
  Jimenez-Munoz et al. (2014). Band-10 SC: Eqs. 1, 2, 4 and 6.
  [Article](https://doi.org/10.1109/LGRS.2014.2312032).

## Split-window temperature algorithms

- `jimenez-munoz-2014-sw`
  Jimenez-Munoz, J.-C., Sobrino, J. A., Skokovic, D., Mattar, C., and Cristobal, J. Land surface temperature retrieval methods from Landsat-8 thermal infrared sensor data. IEEE Geoscience and Remote Sensing Letters, 2014.
- `du-2015`
  Du, C., Ren, H., Qin, Q., Meng, J., and Zhao, S. A practical split-window algorithm for estimating land surface temperature from Landsat 8 data. Remote Sensing, 2015.
- `sobrino-1993`
  Sobrino, J. A., Caselles, V., and Coll, C. Theoretical split window algorithms for determining the actual surface temperature. Il Nuovo Cimento, 1993.
- `kerr-1992`
  Kerr, Y. H., Lagouarde, J. P., and Imbernon, J. Accurate land surface temperature retrieval from AVHRR data with use of an improved split window algorithm. Remote Sensing of Environment, 1992.
  The implementation interpolates the paper's bare-soil and vegetation coefficients using the linear NDVI cover from the article, with `NDVIbs=0.11` and `NDVIv=0.72` cited from Begue (1991).
- `price-1984`
  Price, J. C. Land surface temperature measurements from the split window channels of the NOAA advanced very high-resolution radiometer. Journal of Geophysical Research, 1984.
  This is an adaptation of the AVHRR split-window structure to Landsat Band 10/11 brightness temperatures and band-specific emissivity.

## Emissivity algorithms

- `avdan-2016`
  Avdan, U., and Jovanovska, G. Algorithm for automated mapping of land surface temperature using LANDSAT 8 satellite data. Journal of Sensors, 2016.
  Emissivity follows the article's NDVI conditional rules, including `C=0.005` for mixed pixels.
- `gopinadh-2018`
  Rongali, G., et al. Split-window algorithm for retrieval of land surface temperature using Landsat 8 thermal infrared data. Journal of Geovisualization and Spatial Analysis, 2018.

## Water vapor algorithms

- `wang-2015`
  Wang, M., He, G., Zhang, Z., Wang, G., and Long, T. NDVI-based split-window algorithm for precipitable water vapour retrieval from Landsat-8 TIRS data over land area. Remote Sensing Letters, 2015.

- `ren-2015`
  Ren, H., Du, C., Liu, R., Qin, Q., Yan, G., Li, Z.-L., Meng, J. (2015). Atmospheric water vapor retrieval from Landsat 8 thermal infrared images. JGR Atmospheres, 120, 1723-1738. [Article](https://doi.org/10.1002/2014JD022619). Eqs.1b/1c, p.1724; Eq.2, p.1726; local NDVI filtering, Section 4.2. Verified against the supplied PDF.

## Historical method removed from the current release

Xiaolei (xiaolei-2014) is no longer registered or shipped because the selected
release scope does not include its additional surface-reflectance input.
Yu, X., Guo, X., and Wu, Z. Land surface temperature retrieval from Landsat 8 TIRS -
comparison between radiative transfer equation-based method, split window
algorithm and single channel method. Remote Sensing, 2014.

Links for all current algorithms are also listed in the [README](../README.md#algoritmos-e-artigos).

## Metodos adicionais

- Rozenstein, O., Qin, Z., Derimian, Y., Karnieli, A. (2014). Derivation of Land Surface Temperature for Landsat-8 TIRS Using a Split Window Algorithm. Sensors, 14, 5768-5780. [Artigo](https://doi.org/10.3390/s140405768). Eqs.3--10; Tabelas 1--2.
- Sobrino, J.A., Jimenez-Munoz, J.C., Paolini, L. (2004). Land surface temperature retrieval from LANDSAT TM 5. Remote Sensing of Environment, 90, 434-440. [Artigo](https://doi.org/10.1016/j.rse.2004.02.003). Secao 3, Eqs.8--13. Constantes de TM6.
- Sobrino, J.A., et al. (2008). Land Surface Emissivity Retrieval From Different VNIR and TIR Sensors. IEEE TGRS, 46, 316-327. [Artigo](https://doi.org/10.1109/TGRS.2007.904834). Eqs.5--9. Endmembers devem corresponder a banda.
- Chavez, P.S., Jr. (1996). Image-Based Atmospheric Corrections - Revisited and Improved. PE&RS, 62, 1025-1036. [Artigo](https://static1.1.sqspcdn.com/static/f/891472/15133582/1321370214637/Chavez_P.S._1996.pdf). Eq.2 e discussoes DOS/COST, pp.1027--1029.
