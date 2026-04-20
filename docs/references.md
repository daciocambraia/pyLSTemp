# References

This rebuild keeps the conversion methods tied to the references listed by the original `pylandtemp` project and by the current modular implementations.

## Original project credit

- Original project: <https://github.com/pylandtemp/pylandtemp>
- Original author: Oladimeji Mudele

## Vegetation

- `ndvi`
  Rouse, J. W., Haas, R. H., Schell, J. A., and Deering, D. W. Monitoring vegetation systems in the Great Plains with ERTS. NASA SP-351, 1974.

## Thermal

- `brightness`
  Brightness temperature conversion using scene-specific radiance gain and bias supplied in the function call together with sensor-specific `K1` and `K2` constants for Landsat 8 or Landsat 9.

## Single-channel temperature algorithms

- `mono-window-2016`
  Avdan, U., and Jovanovska, G. Algorithm for automated mapping of land surface temperature using LANDSAT 8 satellite data. Journal of Sensors, 2016.
  This is a Band 10 single-channel workflow. The implementation uses `lambda=10.895e-6 m`, calculated as the midpoint of the Landsat 8/9 TIRS Band 10 range (`10.6-11.19 um`).

## Split-window temperature algorithms

- `du-2015`
  Du, C., Ren, H., Qin, Q., Meng, J., and Zhao, S. A practical split-window algorithm for estimating land surface temperature from Landsat 8 data. Remote Sensing, 2015.
- `sobrino-1993`
  Sobrino, J. A., Caselles, V., and Coll, C. Theoretical split window algorithms for determining the actual surface temperature. Il Nuovo Cimento, 1993.
- `kerr-1992`
  Kerr, Y. H., Lagouarde, J. P., Nerry, F., and Ottle, C. A semiempirical approach to the retrieval of land surface temperature from AVHRR data. Remote Sensing of Environment, 1992.
  The implementation interpolates the paper's bare-soil and vegetation coefficients using the linear NDVI cover from the article, with `NDVIbs=0.11` and `NDVIv=0.72` cited from Begue (1991).
- `price-1984`
  Price, J. C. Land surface temperature measurements from the split window channels of the NOAA advanced very high-resolution radiometer. Journal of Geophysical Research, 1984.
  This is an adaptation of the AVHRR split-window structure to Landsat Band 10/11 brightness temperatures and band-specific emissivity.

## Emissivity algorithms

- `avdan-2016`
  Avdan, U., and Jovanovska, G. Algorithm for automated mapping of land surface temperature using LANDSAT 8 satellite data. Journal of Sensors, 2016.
  Emissivity follows the article's NDVI conditional rules, including `C=0.005` for mixed pixels.
- `xiaolei-2014`
  Yu, X., Guo, X., and Wu, Z. Land surface temperature retrieval from Landsat 8 TIRS - comparison between radiative transfer equation-based method, split window algorithm and single channel method. Remote Sensing, 2014.
- `gopinadh-2018`
  Rongali, G., et al. Split-window algorithm for retrieval of land surface temperature using Landsat 8 thermal infrared data. Journal of Geovisualization and Spatial Analysis, 2018.

## Radiative transfer

This family is currently reserved for future methods.
