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

- `mono-window`
  Avdan, U., and Jovanovska, G. Algorithm for automated mapping of land surface temperature using LANDSAT 8 satellite data. Journal of Sensors, 2016.

## Split-window temperature algorithms

- `jiminez-munoz`
  Jimenez-Munoz, J.-C., and Sobrino, J. A. Split-window coefficients for land surface temperature retrieval from low-resolution thermal infrared sensors. IEEE Geoscience and Remote Sensing Letters, 2008.
- `sobrino-1993`
  Sobrino, J. A., Caselles, V., and Coll, C. Theoretical split window algorithms for determining the actual surface temperature. Il Nuovo Cimento, 1993.
- `kerr`
  Kerr, Y., Lagouarde, J., Nerry, F., and Ottle, C. Land surface temperature retrieval techniques and applications: case of the AVHRR. Thermal Remote Sensing in Land Surface Processing, 2004.
- `mc-millin`
  McMillin, L. M. Estimation of sea surface temperatures from two infrared window measurements with different absorption. Journal of Geophysical Research, 1975.
- `price`
  Price, J. C. Land surface temperature measurements from the split window channels of the NOAA advanced very high-resolution radiometer. Journal of Geophysical Research, 1984.

## Emissivity algorithms

- `avdan`
  Avdan, U., and Jovanovska, G. Algorithm for automated mapping of land surface temperature using LANDSAT 8 satellite data. Journal of Sensors, 2016.
- `xiaolei`
  Yu, X., Guo, X., and Wu, Z. Land surface temperature retrieval from Landsat 8 TIRS - comparison between radiative transfer equation-based method, split window algorithm and single channel method. Remote Sensing, 2014.
- `gopinadh`
  Rongali, G., et al. Split-window algorithm for retrieval of land surface temperature using Landsat 8 thermal infrared data. Journal of Geovisualization and Spatial Analysis, 2018.

## Radiative transfer

This family is currently reserved for future methods.
