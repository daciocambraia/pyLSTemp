# Fichas dos metodos implementados

As 20 fichas cobrem os 13 algoritmos registrados e sete conversoes/variantes auxiliares.
A fonte de cada equacao foi conferida no artigo ou manual original. As decisoes
sobre inconsistencias e transferencias permanecem explicitas; isso nao estabelece
acuracia de campo. NDVI continua interno, sem metodo adicional no catalogo.

Os mesmos registros acompanham o pacote em [method_cards.json](../pylstemp/method_cards.json).
A regressao essencial esta em [tests/test_scientific_regression.py](../tests/test_scientific_regression.py).
Os PDFs e imagens de verificacao permanecem no arquivo local.

## avdan-2016

Avdan, U., and Jovanovska, G. Algorithm for automated mapping of land surface temperature using LANDSAT 8 satellite data. Journal of Sensors, 2016.

- **Fonte:** PDF pp.3-4, Eqs.3-6, Table 2.
- **Sensor:** Landsat 8; Landsat 9 coefficient transfer remains experimental.
- **Entradas:** Calibrated red/nir (or prepared NDVI in [-1,1]); optical convention and fixed-threshold validity require source-specific justification; same emissivity returned for bands 10/11. Intended for single-channel LST.
- **Unidades e dominio:** Not an atmospheric PWV-dependent LST method. NDVI [-1,1]; emissivity (0,1]; bands and thresholds must match the source conditions.
- **Convencao optica:** The scene NDVI input quantity is not uniquely specified. The discussion of fixed global 0.2/0.5 thresholds refers to surface reflectivities; TOA thresholds depend on atmospheric conditions. Radiance/TOA workflows are explicit adaptations, not demonstrated equivalents.

**Equacao adotada:** Pv=((NDVI-0.2)/0.3)^2 in mixed class; e=ev*Pv+es*(1-Pv)+0.005; water=.991, soil=.966, vegetation=.973.

**Coeficientes e constantes:**

```json
{
  "water_emissivity": 0.991,
  "soil_emissivity": 0.966,
  "vegetation_emissivity": 0.973,
  "roughness_correction": 0.005
}
```

**Decisoes, adaptacoes e limites:** Source internal discrepancies: soil .996 in prose vs .966 Table 2; vegetation Eq.6 vs .973 prose/Table 2. Adopt Table 2 endmembers and explicit mixed-class formula. Fixed thresholds are not universal; no atmospheric correction by this equation.

**Evidencia numerica:** Independent synthetic regression plus local numerical/scene checks; see docs/validation.md.
**Acuracia externa:** Not established by software regression or Landsat transfer.

SHA256 da fonte local: `8f299fee5025be73f9b5d6a6c912b6a7fbadc3907e51f0f44d9a59ec4c2124aa`.

## gopinadh-2018

Rongali, G., et al. Split-window algorithm for retrieval of land surface temperature using Landsat 8 thermal infrared data. Journal of Geovisualization and Spatial Analysis, 2018.

- **Fonte:** PDF pp.5-6, Eqs.3,5-7, Table 2; p.8 scene endmembers.
- **Sensor:** Landsat 8; Landsat 9 coefficient transfer remains experimental.
- **Entradas:** TOA-radiance red/nir under the adopted Rongali Step-1 interpretation (or prepared NDVI in [-1,1]); band-specific emissivity, study-scene NDVI endmembers 0.15/0.48 transferred explicitly.
- **Unidades e dominio:** Not an atmospheric PWV-dependent LST method. NDVI [-1,1]; emissivity (0,1]; bands and thresholds must match the source conditions.
- **Convencao optica:** Adopt the Step-1 optical TOA-radiance interpretation before NDVI. NDVIsoil=0.15 and NDVIvegetation=0.48 were derived for the study scene, not established as universal. Another quantity or another scene is an explicit transfer/adaptation.

**Equacao adotada:** f=clip((NDVI-.15)/(.48-.15),0,1); e=es*(1-f)+ev*f; B10 (.971,.987), B11 (.977,.989). Linear f, not squared.

**Coeficientes e constantes:**

```json
{
  "emissivity_soil_10": 0.971,
  "emissivity_veg_10": 0.987,
  "emissivity_soil_11": 0.977,
  "emissivity_veg_11": 0.989,
  "ndvi_soil": 0.15,
  "ndvi_vegetation": 0.48
}
```

**Decisoes, adaptacoes e limites:** Adopt optical TOA-radiance Step-1 interpretation. Endmembers .15/.48 are study-scene values; transfer to other scenes is an adaptation. Paper BT Celsius wording does not change absolute-Kelvin LST equations.

**Evidencia numerica:** Independent synthetic regression plus local numerical/scene checks; see docs/validation.md.
**Acuracia externa:** Not established by software regression or Landsat transfer.

SHA256 da fonte local: `b4b54e4e4fb6e5fb734e0b7cdfe55548b7983363adfe3b89ac2a95c3a0f3c6e8`.

## jimenez-munoz-2014-sc

Jimenez-Munoz, J.-C., Sobrino, J. A., Skokovic, D., Mattar, C., and Cristobal, J. Land surface temperature retrieval methods from Landsat-8 thermal infrared sensor data. IEEE Geoscience and Remote Sensing Letters 11(10), 1840-1843, 2014. https://doi.org/10.1109/LGRS.2014.2312032

- **Fonte:** pp.1840-1842, Eqs.1-4,6.
- **Sensor:** Landsat 8; Landsat 9 coefficient transfer remains experimental.
- **Entradas:** Provide aligned band-10 brightness in Kelvin and calibrated red/nir matching the selected emissivity source contract; radiometric quantities are not interchangeable. Select a registered LST and emissivity method. Also supply radiance_band_10 [W m-2 sr-1 um-1] matching BT10 and Required scalar or aligned raster [0,3] g/cm2. Invalid/out-of-range raster pixels become NaN; scalar out of range is rejected.
- **Unidades e dominio:** Required scalar or aligned raster [0,3] g/cm2. Invalid/out-of-range raster pixels become NaN; scalar out of range is rejected. BT >0 K, emissivity (0,1]; aligned arrays and boolean masks. PWV restrictions and source fit ranges are given above.
- **Convencao optica:** NDVI convention depends on the selected emissivity parametrization; calibrated red/nir quantities are not interchangeable.

**Equacao adotada:** psi=C@[w^2,w,1]; gamma=T10^2/(1324*L10); delta=T10-T10^2/1324; LST=gamma*((psi1*L10+psi2)/e10+psi3)+delta.

**Coeficientes e constantes:**

```json
{
  "b_gamma": 1324.0,
  "coefficients": [
    [
      0.04019,
      0.02916,
      1.01523
    ],
    [
      -0.38333,
      -1.50294,
      0.20324
    ],
    [
      0.00918,
      1.36072,
      -0.27514
    ]
  ]
}
```

**Decisoes, adaptacoes e limites:** Native sensor coefficients retained; supplied emissivity must represent the corresponding thermal band. No empirical field accuracy established.

**Evidencia numerica:** Independent synthetic regression plus local numerical/scene checks; see docs/validation.md.
**Acuracia externa:** Not established by software regression or Landsat transfer.

SHA256 da fonte local: `90d022db854f27d61c4ceb597a4f07b6f2d61079ff5ee2828eaebe02a59ce00c`.

## mono-window-2016

Avdan, U., and Jovanovska, G. Algorithm for automated mapping of land surface temperature using LANDSAT 8 satellite data. Journal of Sensors, 2016.

- **Fonte:** PDF p.3, Eqs.7-8.
- **Sensor:** Landsat 8; Landsat 9 coefficient transfer remains experimental.
- **Entradas:** Provide aligned band-10 brightness in Kelvin and calibrated red/nir matching the selected emissivity source contract; radiometric quantities are not interchangeable. Select a registered LST and emissivity method.
- **Unidades e dominio:** Not an atmospheric PWV-dependent LST method. BT >0 K, emissivity (0,1]; aligned arrays and boolean masks. PWV restrictions and source fit ranges are given above.
- **Convencao optica:** NDVI convention depends on the selected emissivity parametrization; calibrated red/nir quantities are not interchangeable.

**Equacao adotada:** LST=T10/(1+(10.895e-6*T10/1.438e-2)*ln(e10)). Absolute Kelvin internally.

**Coeficientes e constantes:**

```json
{
  "wavelength_band_10": 1.0895e-05,
  "rho": 0.01438
}
```

**Decisoes, adaptacoes e limites:** Kelvin used despite ambiguous Celsius wording in paper; wavelength/rho in m and m K. Emissivity correction alone is not full atmospheric compensation.

**Evidencia numerica:** Independent synthetic regression plus local numerical/scene checks; see docs/validation.md.
**Acuracia externa:** Not established by software regression or Landsat transfer.

SHA256 da fonte local: `8f299fee5025be73f9b5d6a6c912b6a7fbadc3907e51f0f44d9a59ec4c2124aa`.

## du-2015

Du, C., Ren, H., Qin, Q., Meng, J., and Zhao, S. A practical split-window algorithm for estimating land surface temperature from Landsat 8 data. Remote Sensing, 2015.

- **Fonte:** pp.650-651, Eq.2, Table 1.
- **Sensor:** Landsat 8; Landsat 9 coefficient transfer remains experimental.
- **Entradas:** Provide aligned band-10/11 brightness in Kelvin and calibrated red/nir matching the selected emissivity source contract; radiometric quantities are not interchangeable. Avdan is single-channel only. PWV is in g/cm2. Optional scalar or aligned raster [0,6.3] g/cm2. Invalid raster pixels become NaN; invalid scalars raise. None uses all-CWV coefficients.
- **Unidades e dominio:** Optional scalar or aligned raster [0,6.3] g/cm2. Invalid raster pixels become NaN; invalid scalars raise. None uses all-CWV coefficients. BT >0 K, emissivity (0,1]; aligned arrays and boolean masks. PWV restrictions and source fit ranges are given above.
- **Convencao optica:** NDVI convention depends on the selected emissivity parametrization; calibrated red/nir quantities are not interchangeable.

**Equacao adotada:** LST=b0+(b1+b2*(1-e)/e+b3*de/e^2)*(T10+T11)/2+(b4+b5*(1-e)/e+b6*de/e^2)*(T10-T11)/2+b7*(T10-T11)^2; average LST estimates in overlapping inclusive CWV intervals.

**Coeficientes e constantes:**

```json
{
  "intervals": [
    [
      0,
      2.5
    ],
    [
      2,
      3.5
    ],
    [
      3,
      4.5
    ],
    [
      4,
      5.5
    ],
    [
      5,
      6.3
    ]
  ],
  "rows_b0_to_b7": [
    [
      -2.78009,
      1.01408,
      0.15833,
      -0.34991,
      4.04487,
      3.55414,
      -8.88394,
      0.09152
    ],
    [
      11.00824,
      0.95995,
      0.17243,
      -0.28852,
      7.11492,
      0.42684,
      -6.62025,
      -0.06381
    ],
    [
      9.6261,
      0.96202,
      0.13834,
      -0.17262,
      7.87883,
      5.1791,
      -13.26611,
      -0.07603
    ],
    [
      0.61258,
      0.99124,
      0.10051,
      -0.09664,
      7.85758,
      6.86626,
      -15.00742,
      -0.01185
    ],
    [
      -0.34808,
      0.98123,
      0.05599,
      -0.03518,
      11.96444,
      9.0671,
      -14.74085,
      -0.20471
    ]
  ],
  "general_b0_to_b7": [
    -0.41165,
    1.00522,
    0.14543,
    -0.27297,
    4.06655,
    -6.92512,
    -18.27461,
    0.24468
  ]
}
```

**Decisoes, adaptacoes e limites:** Do not use the conflicting polynomial coefficient order in source Eq.3a: Ren Eq.2 is authoritative for Ren retrieval. Du all-CWV row is separate from per-CWV rows. Landsat9 transfer experimental.

**Evidencia numerica:** Independent synthetic regression plus local numerical/scene checks; see docs/validation.md.
**Acuracia externa:** Not established by software regression or Landsat transfer.

SHA256 da fonte local: `60c7702be839f8b3bb066ef888fa65f20670208dd80be02921ad4b95c245da2f`.

## jimenez-munoz-2014-sw

Jimenez-Munoz, J.-C., Sobrino, J. A., Skokovic, D., Mattar, C., and Cristobal, J. Land surface temperature retrieval methods from Landsat-8 thermal infrared sensor data. IEEE Geoscience and Remote Sensing Letters, 2014.

- **Fonte:** pp.1841-1842, Eq.5, Table I.
- **Sensor:** Landsat 8; Landsat 9 coefficient transfer remains experimental.
- **Entradas:** Provide aligned band-10/11 brightness in Kelvin and calibrated red/nir matching the selected emissivity source contract; radiometric quantities are not interchangeable. Avdan is single-channel only. PWV is in g/cm2. Required finite nonnegative scalar or aligned raster in g/cm2; invalid raster pixels become NaN.
- **Unidades e dominio:** BT and LST K, e dimensionless, w g/cm2. Source evaluated 0..6; implementation accepts nonnegative w, so w>6 is explicit extrapolation, not demonstrated validity. BT >0 K, emissivity (0,1]; aligned arrays and boolean masks. PWV restrictions and source fit ranges are given above.
- **Convencao optica:** NDVI convention depends on the selected emissivity parametrization; calibrated red/nir quantities are not interchangeable.

**Equacao adotada:** d=T10-T11; LST=T10+1.378*d+.183*d^2-.268+(54.3-2.238*w)*(1-mean(e))+(-129.2+16.4*w)*(e10-e11).

**Coeficientes e constantes:**

```json
{
  "c0_to_c6": [
    -0.268,
    1.378,
    0.183,
    54.3,
    -2.238,
    -129.2,
    16.4
  ]
}
```

**Decisoes, adaptacoes e limites:** Native sensor coefficients retained; supplied emissivity must represent the corresponding thermal band. No empirical field accuracy established.

**Evidencia numerica:** Independent synthetic regression plus local numerical/scene checks; see docs/validation.md.
**Acuracia externa:** Not established by software regression or Landsat transfer.

SHA256 da fonte local: `90d022db854f27d61c4ceb597a4f07b6f2d61079ff5ee2828eaebe02a59ce00c`.

## kerr-1992

Kerr, Y. H., Lagouarde, J. P., and Imbernon, J. Accurate land surface temperature retrieval from AVHRR data with use of an improved split window algorithm. Remote Sensing of Environment, 1992. This implementation interpolates the bare-soil and vegetation coefficients reported in Table 1 using the article's linear NDVI cover with NDVIbs=0.11 and NDVIv=0.72, cited from Begue (1991).

- **Fonte:** Eqs.12-15; p.205 Table 1 and atmospherically corrected NDVI thresholds.
- **Sensor:** NOAA AVHRR; adaptation to Landsat arrays.
- **Entradas:** Provide aligned band-10/11 brightness in Kelvin and calibrated red/nir matching the selected emissivity source contract; radiometric quantities are not interchangeable. Avdan is single-channel only. PWV is in g/cm2. Not used; supplying water_vapor emits a RuntimeWarning. The equation uses NDVI, not emissivity values.
- **Unidades e dominio:** Not used; supplying water_vapor emits a RuntimeWarning. BT >0 K, emissivity (0,1]; aligned arrays and boolean masks. PWV restrictions and source fit ranges are given above.
- **Convencao optica:** Atmospherically corrected NDVI (surface-reflectance red/nir), field endpoints .11/.72. TOA or radiance inputs are adaptations, not equivalent.

**Equacao adotada:** C=clip((NDVI-.11)/(.72-.11),0,1); LST=T10*(3.1+.5*C)+T11*(-2.1-.5*C)+(3.1-5.5*C).

**Coeficientes e constantes:**

```json
{
  "ndvi_bare_soil": 0.11,
  "ndvi_vegetation": 0.72,
  "bare_a0_a1_a2": [
    3.1,
    3.1,
    -2.1
  ],
  "vegetation_a0_a1_a2": [
    -2.4,
    3.6,
    -2.6
  ]
}
```

**Decisoes, adaptacoes e limites:** Original thresholds .11/.72 require atmospherically corrected NDVI, derived in Niger; transferring them or using radiance/TOA NDVI is an adaptation.

**Evidencia numerica:** Independent synthetic regression plus local numerical/scene checks; see docs/validation.md.
**Acuracia externa:** Not established by software regression or Landsat transfer.

SHA256 da fonte local: `1843f18fc14d660fac0c713a5e49693935815e36175071bd09f2b809e0545d3b`.

## price-1984

Price, J. C. Land surface temperature measurements from the split window channels of the NOAA advanced very high-resolution radiometer. Journal of Geophysical Research, 1984. This implementation applies the Price split-window structure as a Landsat Band 10/11 adaptation.

- **Fonte:** p.7233 Eq.5; p.7236 unnumbered emissivity equation.
- **Sensor:** NOAA AVHRR; adaptation to Landsat arrays.
- **Entradas:** Provide aligned band-10/11 brightness in Kelvin and calibrated red/nir matching the selected emissivity source contract; radiometric quantities are not interchangeable. Avdan is single-channel only. PWV is in g/cm2. Not used; supplying water_vapor emits a RuntimeWarning.
- **Unidades e dominio:** Not used; supplying water_vapor emits a RuntimeWarning. BT >0 K, emissivity (0,1]; aligned arrays and boolean masks. PWV restrictions and source fit ranges are given above.
- **Convencao optica:** NDVI convention depends on the selected emissivity parametrization; calibrated red/nir quantities are not interchangeable.

**Equacao adotada:** Implemented adaptation: (T10+3.33*(T10-T11))*(5.5-e10)/4.5+.75*T11*(e10-e11). Printed p.7236 instead has (3.5+e4)/4.5; NOT a literal reproduction.

**Coeficientes e constantes:**

```json
{
  "split_difference": 3.33,
  "implemented_emissivity_factor": "(5.5-e10)/4.5",
  "printed_emissivity_factor": "(3.5+e4)/4.5",
  "difference_emissivity": 0.75
}
```

**Decisoes, adaptacoes e limites:** Retained legacy inverse-emissivity approximation; source printed factor conflicts with it. Explicit adaptation, not source-literal or Landsat validated.

**Evidencia numerica:** Independent synthetic regression plus local numerical/scene checks; see docs/validation.md.
**Acuracia externa:** Not established by software regression or Landsat transfer.

SHA256 da fonte local: `4011859cf02beeab075b2f636d18a2d5369ce4d015ec7169e411b911935a6dec`.

## rozenstein-2014

Rozenstein, O., Qin, Z., Derimian, Y., Karnieli, A. (2014). Derivation of Land Surface Temperature for Landsat-8 TIRS Using a Split Window Algorithm. Sensors 14, 5768-5780. https://doi.org/10.3390/s140405768

- **Fonte:** pp.5770-5773, Eqs.3-10, Tables 1-2.
- **Sensor:** Landsat 8; Landsat 9 coefficient transfer remains experimental.
- **Entradas:** Provide aligned band-10/11 brightness in Kelvin and calibrated red/nir matching the selected emissivity source contract; radiometric quantities are not interchangeable. Avdan is single-channel only. PWV is in g/cm2. Required PWV scalar/aligned raster [0.5,3] g/cm2, explicit atmospheric_profile and preselected temperature_range. Invalid raster pixels become NaN.
- **Unidades e dominio:** Required PWV scalar/aligned raster [0.5,3] g/cm2, explicit atmospheric_profile and preselected temperature_range. Invalid raster pixels become NaN. BT >0 K, emissivity (0,1]; aligned arrays and boolean masks. PWV restrictions and source fit ranges are given above.
- **Convencao optica:** NDVI convention depends on the selected emissivity parametrization; calibrated red/nir quantities are not interchangeable.

**Equacao adotada:** Ci=ei*taui; Di=(1-taui)*(1+(1-ei)*taui); E0=D11*C10-D10*C11; A=D10/E0; E1=D11*(1-C10-D10)/E0; E2=D10*(1-C11-D11)/E0; LST=E1*a10+E2*a11+(1+A+E1*b10)*T10-(A+E2*b11)*T11.

**Coeficientes e constantes:**

```json
{
  "thermal_a10_b10_a11_b11": {
    "0-60": [
      -64.4661,
      0.4398,
      -68.8678,
      0.4755
    ],
    "0-30": [
      -59.1391,
      0.4213,
      -63.3921,
      0.4565
    ],
    "0-40": [
      -60.9196,
      0.4276,
      -65.224,
      0.4629
    ],
    "10-40": [
      -62.8065,
      0.4338,
      -67.1728,
      0.4694
    ],
    "10-50": [
      -64.6081,
      0.4399,
      -69.0215,
      0.4756
    ]
  },
  "tau_intercept10_slope10_intercept11_slope11": {
    "us-standard-1976": [
      1.0286,
      -0.1146,
      1.0083,
      -0.1568
    ],
    "midlatitude-summer": [
      1.0335,
      -0.1134,
      1.0078,
      -0.1546
    ]
  },
  "PWV_domain": [
    0.5,
    3
  ]
}
```

**Decisoes, adaptacoes e limites:** Explicit atmosphere selection; no assumed tropical profile. Mask singular denominator and LST outside preselected fit interval. Landsat9 transfer experimental.

**Evidencia numerica:** Independent synthetic regression plus local numerical/scene checks; see docs/validation.md.
**Acuracia externa:** Not established by software regression or Landsat transfer.

SHA256 da fonte local: `71c5a68e0d63d5ccbf42975ea27b3fd49b926e9bbe64e5475cf8902c09d1d735`.

## sobrino-1993

Sobrino, J. A., Caselles, V., and Coll, C. Theoretical split window algorithms for determining the actual surface temperature. Il Nuovo Cimento, 1993.

- **Fonte:** p.225, Eq.16.
- **Sensor:** NOAA AVHRR; adaptation to Landsat arrays.
- **Entradas:** Provide aligned band-10/11 brightness in Kelvin and calibrated red/nir matching the selected emissivity source contract; radiometric quantities are not interchangeable. Avdan is single-channel only. PWV is in g/cm2. Not used; supplying water_vapor emits a RuntimeWarning.
- **Unidades e dominio:** Not used; supplying water_vapor emits a RuntimeWarning. BT >0 K, emissivity (0,1]; aligned arrays and boolean masks. PWV restrictions and source fit ranges are given above.
- **Convencao optica:** NDVI convention depends on the selected emissivity parametrization; calibrated red/nir quantities are not interchangeable.

**Equacao adotada:** LST=T10+(1.060+.46*(T10-T11))*(T10-T11)+53*(1-e10)-53*(e10-e11).

**Coeficientes e constantes:**

```json
{
  "difference_linear": 1.06,
  "difference_squared": 0.46,
  "one_minus_e10": 53,
  "e10_minus_e11": -53
}
```

**Decisoes, adaptacoes e limites:** Native sensor coefficients retained; supplied emissivity must represent the corresponding thermal band. No empirical field accuracy established.

**Evidencia numerica:** Independent synthetic regression plus local numerical/scene checks; see docs/validation.md.
**Acuracia externa:** Not established by software regression or Landsat transfer.

SHA256 da fonte local: `07ebbe08ad41541cfcc3f1638782b9a0f21cc1d28536f4f19e439ef529634e80`.

## brightness

USGS LSDS-1747, Landsat 8-9 Calibration and Validation Algorithm Description Document, version 5, Sections 4.7.2.5/4.7.3.4.

- **Fonte:** PDF pp.793-794 (printed 781-782), Sections 4.7.2.5/4.7.3.4.
- **Sensor:** Landsat 8/9 radiometric calibration.
- **Entradas:** Provide TOA radiance [W m-2 sr-1 um-1], band 10/11 and matching MTL (metadata=) or sensor. Output is TOA BT [K]. For raw Level-1 DN explicitly set input_quantity='dn'; never rescale radiance again.
- **Unidades e dominio:** Positive TOA thermal radiance W m-2 sr-1 um-1; T in K. DN only explicitly declared Level1. MTL calibration covers L8/L9, not LST coefficient validity. Positive TOA thermal radiance; matching band/sensor MTL.
- **Convencao optica:** Not applicable: input is thermal TOA radiance, or explicitly declared Level-1 DN.

**Equacao adotada:** L=gain*DN+bias; T=K2/ln(1+K1/L); use matching MTL band constants.

**Coeficientes e constantes:**

```json
{
  "K1_K2": "Matching scene MTL K1_CONSTANT_BAND_10/11 and K2_CONSTANT_BAND_10/11; sensor fallback is explicitly separate from MTL calibration",
  "gain_bias": "Matching MTL RADIANCE_MULT_BAND_x and RADIANCE_ADD_BAND_x when input_quantity=dn"
}
```

**Decisoes, adaptacoes e limites:** Native sensor coefficients retained; supplied emissivity must represent the corresponding thermal band. No empirical field accuracy established.

**Evidencia numerica:** Independent synthetic regression plus local numerical/scene checks; see docs/validation.md.
**Acuracia externa:** Not established by software regression or Landsat transfer.

SHA256 da fonte local: `8e39d9abc926cbdb2be2ca68808260f7cb5da683d85ef134edd03d7252fe25a4`.

## ren-2015

Ren, H., Du, C., Liu, R., Qin, Q., Yan, G., Li, Z.-L., Meng, J. (2015). Atmospheric water vapor retrieval from Landsat 8 thermal infrared images. JGR Atmospheres 120, 1723-1738. https://doi.org/10.1002/2014JD022619

- **Fonte:** pp.1724/1726 Eqs.1b/1c/2; Section 4.2.
- **Sensor:** Landsat 8; Landsat 9 coefficient transfer remains experimental.
- **Entradas:** Aligned 2D BT10/BT11 in K; Red/nir for internal NDVI, or prepared NDVI, required by default local +/-1.5 sigma filter; optional only with ndvi_filter=False. Odd window, minimum samples, chi-squared screen; PWV [.06,6.3] g/cm2. Diagnostics available. No global NDVI groups.
- **Unidades e dominio:** Not an atmospheric PWV-dependent LST method. Positive thermal BT, aligned 2D windows; undefined variance, insufficient samples or failed quality screens produce NaN.
- **Convencao optica:** Section 4.2 specifies a local NDVI filter without explicitly specifying its optical radiometric quantity. Record the supplied quantity. Thermal-only ndvi_filter=False is a separately declared mode.

**Equacao adotada:** r=cov(T10,T11)/var(T10); chi2=cov^2/(var(T10)*var(T11)); PWV=-9.674*r^2+.653*r+9.087. Means after local NDVI +/-1.5 population-SD selection; no symmetric inverse slope.

**Coeficientes e constantes:**

```json
{
  "r_squared_r_intercept": [
    -9.674,
    0.653,
    9.087
  ],
  "ndvi_population_sigma_multiple": 1.5,
  "PWV_domain": [
    0.06,
    6.3
  ],
  "operational_min_samples": 10,
  "operational_chi2_min": 0.95,
  "standalone_window": 11,
  "scene_window_30m": 33
}
```

**Decisoes, adaptacoes e limites:** Eq.2 intercept 9.087 adopted over figure annotation 9.088. Source native n=10 adapted to centered odd windows (11 standalone,33 scene on usual30m grid). min_samples=10 and chi2=.95 are declared operational controls. Optical quantity unspecified.

**Evidencia numerica:** Independent synthetic regression plus local numerical/scene checks; see docs/validation.md.
**Acuracia externa:** Not established by software regression or Landsat transfer.

SHA256 da fonte local: `c7d2acf96ebf65e7c01223c31ab839efac718bcc03481a622eb09d2e6799891b`.

## wang-2015

Wang, M., He, G., Zhang, Z., Wang, G., and Long, T. NDVI-based split-window algorithm for precipitable water vapour retrieval from Landsat-8 TIRS data over land area. Remote Sensing Letters, 2015.

- **Fonte:** pp.905-909, Eqs.1-4, Figure 3, Section 2.3.
- **Sensor:** Landsat 8; Landsat 9 coefficient transfer remains experimental.
- **Entradas:** Provide aligned 2D band-10/11 brightness in Kelvin and red/nir for internal NDVI (or prepared NDVI). Use odd window_size>=3, group_count>=1, chunk_rows>=1 and a boolean mask.
- **Unidades e dominio:** PWV g/cm2; source TIGR .066..7.833; estimator accepts finite nonnegative output without a source-upper-bound screen. Du scene chain screens to .066..6.3. Values outside calibration are extrapolations. Positive thermal BT, aligned 2D windows; undefined variance, insufficient samples or failed quality screens produce NaN.
- **Convencao optica:** The inspected source defines NDVI grouping and emissivity-ratio thresholds without explicitly specifying the optical radiometric quantity. Record the supplied quantity; no equivalence of radiance, TOA reflectance and surface reflectance is established.

**Equacao adotada:** NDVI groups using global min/max. Center BT before thermal filtering; symmetric forward/inverse slopes; r^2>=.97; emissivity ratio .9939/.9966 or (.0195*Pv+.9688)/(.0149*Pv+.9747), Pv squared (.2,.5). PWV=19.13-18.973*R for R>.9 else 14.158-13.412*R; sample-count weighted groups.

**Coeficientes e constantes:**

```json
{
  "ndvi_soil": 0.2,
  "ndvi_vegetation": 0.5,
  "correlation_threshold": 0.97,
  "soil_ratio": 0.9939,
  "vegetation_ratio": 0.9966,
  "mixed_ratio": "(.0195*Pv+.9688)/(.0149*Pv+.9747)",
  "r_above_point9_intercept_slope": [
    19.13,
    -18.973
  ],
  "r_at_or_below_point9_intercept_slope": [
    14.158,
    -13.412
  ],
  "operational_window": 21,
  "source_window": 20,
  "source_TIGR_PWV_domain": [
    0.066,
    7.833
  ]
}
```

**Decisoes, adaptacoes e limites:** Source optical quantity unspecified; record it. Source n=20 adapted to odd centered n=21. Global bounds must be reused across tiles. Native samples differ from 30-m resampled support.

**Evidencia numerica:** Independent synthetic regression plus local numerical/scene checks; see docs/validation.md.
**Acuracia externa:** Not established by software regression or Landsat transfer.

SHA256 da fonte local: `25ff799f57450bb428ddc0d74fa4fe1aa3f594eed4707a0cdb7ebd68dbba35d1`.

## toa_radiance

USGS LSDS-1747, Landsat 8-9 Calibration and Validation Algorithm Description Document, version 5.

- **Fonte:** PDF p.794, Section 4.7.3.4.
- **Sensor:** Landsat 8/9.
- **Entradas:** Level1 DN; matching MTL band gain/bias; W m-2 sr-1 um-1
- **Unidades e dominio:** Level1 DN >0; invalid/NoData/masked pixels NaN; calibrated output quantity and units as specified below. Level1 optical/thermal DN, matching MTL; reflectance solar elevation (0,90] degrees.
- **Convencao optica:** Level1 DN; matching MTL band gain/bias; W m-2 sr-1 um-1

**Equacao adotada:** L=ML*DN+AL

**Coeficientes e constantes:**

```json
{
  "gain_bias": "RADIANCE_MULT_BAND_x and RADIANCE_ADD_BAND_x from matching MTL"
}
```

**Decisoes, adaptacoes e limites:** No solar or atmospheric correction.

**Evidencia numerica:** Independent synthetic regression; see docs/validation.md.
**Acuracia externa:** Not established by software tests.

SHA256 da fonte local: `8e39d9abc926cbdb2be2ca68808260f7cb5da683d85ef134edd03d7252fe25a4`.

## toa_reflectance

USGS LSDS-1747, Landsat 8-9 Calibration and Validation Algorithm Description Document, version 5.

- **Fonte:** PDF p.793, Section 4.7.2.5.
- **Sensor:** Landsat 8/9.
- **Entradas:** Level1 optical DN; matching MTL; solar elevation degrees; dimensionless TOA rho
- **Unidades e dominio:** Level1 DN >0; invalid/NoData/masked pixels NaN; calibrated output quantity and units as specified below. Level1 optical/thermal DN, matching MTL; reflectance solar elevation (0,90] degrees.
- **Convencao optica:** Level1 optical DN; matching MTL; solar elevation degrees; dimensionless TOA rho

**Equacao adotada:** rho=(Mrho*DN+Arho)/cos(SZA)

**Coeficientes e constantes:**

```json
{
  "gain_bias": "REFLECTANCE_MULT_BAND_x and REFLECTANCE_ADD_BAND_x from matching MTL",
  "solar_correction": "divide by cos(SZA) = sin(sun_elevation)"
}
```

**Decisoes, adaptacoes e limites:** TOA reflectance is not surface reflectance; SZA versus scene-mean angle explicitly chosen.

**Evidencia numerica:** Independent synthetic regression; see docs/validation.md.
**Acuracia externa:** Not established by software tests.

SHA256 da fonte local: `8e39d9abc926cbdb2be2ca68808260f7cb5da683d85ef134edd03d7252fe25a4`.

## sobrino-2004-tm6

Sobrino, Jimenez-Munoz and Paolini (2004). Land surface temperature retrieval from LANDSAT TM 5. Remote Sensing of Environment 90, 434-440. https://doi.org/10.1016/j.rse.2004.02.003

- **Fonte:** p.436, Eqs.8-10/13; Section4 Eq.14.
- **Sensor:** Landsat 5 TM band6.
- **Entradas:** Reflectance NDVI; surface preferred, TOA approximation; e dimensionless
- **Unidades e dominio:** Finite physical inputs; e in (0,1], corrected rho [0,1]; invalid pixels NaN NDVI [-1,1]; emissivity (0,1]; bands and thresholds must match the source conditions.
- **Convencao optica:** Reflectance NDVI; surface preferred, TOA approximation; e dimensionless

**Equacao adotada:** Pv=((NDVI-.2)/.3)^2; mixed e=.004*Pv+.986; vegetation .99; bare soil NaN

**Coeficientes e constantes:**

```json
{
  "ndvi_soil": 0.2,
  "ndvi_vegetation": 0.5,
  "mixed_slope": 0.004,
  "mixed_intercept": 0.986,
  "vegetation": 0.99,
  "bare": "NaN: no inferred soil relation"
}
```

**Decisoes, adaptacoes e limites:** No universal bare-soil red relation supplied; do not assign TIRS constants.

**Evidencia numerica:** Independent synthetic regression; see docs/validation.md.
**Acuracia externa:** Not established by software tests.

SHA256 da fonte local: `c968520726f0c5ddc6ab51335ddf9803757c55ffa9285aa2dfa58899d73126df`.

## sobrino-2008-simplified

Sobrino et al. (2008). Land Surface Emissivity Retrieval From Different VNIR and TIR Sensors. IEEE TGRS 46, 316-327. https://doi.org/10.1109/TGRS.2007.904834

- **Fonte:** pp.317-318, Eqs.5-9.
- **Sensor:** Band parameters supplied by caller.
- **Entradas:** Reflectance NDVI, user band-specific es,ev; e dimensionless
- **Unidades e dominio:** Finite physical inputs; e in (0,1], corrected rho [0,1]; invalid pixels NaN NDVI [-1,1]; emissivity (0,1]; bands and thresholds must match the source conditions.
- **Convencao optica:** Reflectance NDVI, user band-specific es,ev; e dimensionless

**Equacao adotada:** e=es*(1-Pv)+ev*Pv; Pv=clip((NDVI-ns)/(nv-ns),0,1)^2

**Coeficientes e constantes:**

```json
{
  "ndvi_soil_default": 0.2,
  "ndvi_vegetation_default": 0.5,
  "vegetation_fraction_exponent": 2,
  "es_ev": "Caller-supplied for the selected band"
}
```

**Decisoes, adaptacoes e limites:** No universal Landsat TIRS defaults; thresholds require scene justification.

**Evidencia numerica:** Independent synthetic regression; see docs/validation.md.
**Acuracia externa:** Not established by software tests.

SHA256 da fonte local: `d62227dd284013caacf7e501d2cc448e429691294eddbe8a6b0daaf6ee2f245c`.

## sobrino-2008-full

Sobrino et al. (2008). Land Surface Emissivity Retrieval From Different VNIR and TIR Sensors. IEEE TGRS 46, 316-327. https://doi.org/10.1109/TGRS.2007.904834

- **Fonte:** pp.317-318, Eqs.5-8.
- **Sensor:** Band parameters supplied by caller.
- **Entradas:** Surface red reflectance, reflectance NDVI, user band-specific a,b,es,ev; e dimensionless
- **Unidades e dominio:** Finite physical inputs; e in (0,1], corrected rho [0,1]; invalid pixels NaN NDVI [-1,1]; emissivity (0,1]; bands and thresholds must match the source conditions.
- **Convencao optica:** Surface red reflectance, reflectance NDVI, user band-specific a,b,es,ev; e dimensionless

**Equacao adotada:** Bare e=a+b*rho_red; mixed e=es*(1-Pv)+ev*Pv+(1-es)*ev*F*(1-Pv); vegetation e=ev+.005

**Coeficientes e constantes:**

```json
{
  "ndvi_soil_default": 0.2,
  "ndvi_vegetation_default": 0.5,
  "vegetation_fraction_exponent": 2,
  "cavity_factor_default": 0.55,
  "vegetation_cavity_default": 0.005,
  "es_ev_a_b": "Caller-supplied band-compatible endmembers and soil-red relation"
}
```

**Decisoes, adaptacoes e limites:** F=.55 and vegetation cavity .005 are explicit configurable assumptions; no TIRS coefficients inferred.

**Evidencia numerica:** Independent synthetic regression; see docs/validation.md.
**Acuracia externa:** Not established by software tests.

SHA256 da fonte local: `d62227dd284013caacf7e501d2cc448e429691294eddbe8a6b0daaf6ee2f245c`.

## chavez-dos

Chavez (1996). Image-Based Atmospheric Corrections - Revisited and Improved. Photogrammetric Engineering & Remote Sensing 62, 1025-1036.

- **Fonte:** pp.1027-1029, Eq.2.
- **Sensor:** TM source; OLI transfer experimental.
- **Entradas:** Solar-corrected TOA rho; one scene angle; dimensionless
- **Unidades e dominio:** Finite physical inputs; e in (0,1], corrected rho [0,1]; invalid pixels NaN Input and output reflectance [0,1]; one scene solar angle; invalid output NaN.
- **Convencao optica:** Solar-corrected TOA rho; one scene angle; dimensionless

**Equacao adotada:** rho_corrected=rho_TOA-(rho_dark-.01)

**Coeficientes e constantes:**

```json
{
  "assumed_dark_surface_default": 0.01,
  "operational_percentile_default": 0.01,
  "view_transmittance": 1,
  "downwelling": 0
}
```

**Decisoes, adaptacoes e limites:** Fit full scene once, reuse for tiles; percentile .01 is operational, not mandated by source; no clipping or automatic LaSRC equivalence.

**Evidencia numerica:** Independent synthetic regression; see docs/validation.md.
**Acuracia externa:** Not established by software tests.

SHA256 da fonte local: `e8f7822658fec59af9a8e6ea5bdbb32a2fc266bc2e5b2e76d7fd7967e2e2351e`.

## chavez-cost

Chavez (1996). Image-Based Atmospheric Corrections - Revisited and Improved. Photogrammetric Engineering & Remote Sensing 62, 1025-1036.

- **Fonte:** pp.1027-1029, Eq.2.
- **Sensor:** TM source; OLI transfer experimental.
- **Entradas:** Solar-corrected TOA rho; one scene angle; dimensionless
- **Unidades e dominio:** Finite physical inputs; e in (0,1], corrected rho [0,1]; invalid pixels NaN Input and output reflectance [0,1]; one scene solar angle; invalid output NaN.
- **Convencao optica:** Solar-corrected TOA rho; one scene angle; dimensionless

**Equacao adotada:** rho_corrected=(rho_TOA-(rho_dark-.01))/sin(sun_elevation)

**Coeficientes e constantes:**

```json
{
  "assumed_dark_surface_default": 0.01,
  "operational_percentile_default": 0.01,
  "view_transmittance": 1,
  "solar_transmittance": "sin(sun_elevation)",
  "downwelling": 0
}
```

**Decisoes, adaptacoes e limites:** TAUv=1, downwelling=0, TAUz=cos(SZA); full-scene fit reusable; percentile .01 operational; not validated OLI atmospheric correction.

**Evidencia numerica:** Independent synthetic regression; see docs/validation.md.
**Acuracia externa:** Not established by software tests.

SHA256 da fonte local: `e8f7822658fec59af9a8e6ea5bdbb32a2fc266bc2e5b2e76d7fd7967e2e2351e`.
