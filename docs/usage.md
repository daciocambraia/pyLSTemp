# Guia de uso

Este guia acompanha o fluxo publico por funcao, com imagens reais Landsat
Collection 2 Level-1. Execute os blocos em ordem no mesmo script ou notebook.
Nenhuma banda artificial precisa ser criada. Instale `pip install -e ".[examples]"`.

## Importar as funcoes publicas e escolher a imagem

```python
from pathlib import Path
from pylstemp.scene import LandsatScene
from pylstemp import (
    toa_radiance, brightness, emissivity,
    water_vapor, single_window, split_window, list_algorithms,
)

pasta = Path("caminho/para/cena_landsat")
saida = Path("resultados")
saida.mkdir(parents=True, exist_ok=True)
```

A pasta deve conter B4, B5, B10, B11, MTL.txt, QA_PIXEL e QA_RADSAT, mantendo
os nomes originais. B2 e opcional. Os coeficientes do sensor sao lidos do MTL.

## 1. Abrir as imagens

A leitura abaixo usa a cena inteira, sem definir linhas ou colunas.
A mascara QA marca pixels invalidos; aqui tambem excluimos agua para Wang.

```python
with LandsatScene(pasta) as cena:
    bandas, _, mascara = cena.calibrated(exclude_water=True)
    red, nir = bandas[4], bandas[5]  # radiancia TOA
    dn10 = cena.read("B10")
    dn11 = cena.read("B11")
    metadata = cena.metadata
```

O leitor fecha os arquivos ao sair do bloco; os arrays lidos ficam disponiveis.
A cena inteira exige mais memoria; os scripts prontos demonstram recortes
pequenos. PWV de Wang processado por blocos exige halo e limites globais de NDVI;
Ren usa halo e filtro NDVI local. Veja [metodos cientificos](scientific-methods.md).

## 2. Calcular radiancia e temperatura de brilho

```python
radiancia10 = toa_radiance(dn10, metadata=metadata, band=10, mask=mascara)
radiancia11 = toa_radiance(dn11, metadata=metadata, band=11, mask=mascara)
bt10 = brightness(radiancia10, metadata=metadata, band=10, mask=mascara)
bt11 = brightness(radiancia11, metadata=metadata, band=11, mask=mascara)
```

Radiancia: **W m-2 sr-1 um-1**. BT: **kelvin**, temperatura de brilho TOA.
BT nao e LST. `brightness` recebe radiancia por padrao; para DN, use
`input_quantity="dn"`. As constantes K1/K2 devem pertencer a mesma banda e cena.

## 3. NDVI interno

Nao e necessario calcular ou fornecer NDVI no fluxo normal. As funcoes de
emissividade e PWV calculam o indice internamente a partir de `red` e `nir`.
Use as duas bandas na mesma grade e convencao radiometrica; radiancia e
reflectancia podem produzir NDVIs diferentes.

## 4. Calcular emissividade das bandas 10 e 11

```python
emissividade10 = emissivity(red=red, nir=nir, mask=mascara, band=10, emissivity_method="gopinadh-2018")
emissividade11 = emissivity(red=red, nir=nir, mask=mascara, band=11, emissivity_method="gopinadh-2018")
```

`gopinadh-2018` fornece valores por banda. `avdan-2016` tambem esta disponivel,
com a parametrizacao single-channel da fonte. Emissividade e adimensional.
As funcoes LST calculam essa etapa internamente; o calculo separado permite
inspecionar ou exportar a emissividade. Os limiares de NDVI exigem justificativa
para a convencao radiometrica usada.

## 5. Calcular LST single-channel: Avdan

```python
lst_avdan = single_window(
    brightness_band_10=bt10, band_4_red=red, band_5_nir=nir,
    lst_method="mono-window-2016", emissivity_method="avdan-2016",
    unit="celsius", mask=mascara,
)
```

O metodo usa BT10 e corrige emissividade. Nao modela explicitamente a atmosfera.
`unit="kelvin"` entrega LST em K; `unit="celsius"` entrega LST em Celsius.

## 6. Estimar vapor d'agua

```python
pwv = water_vapor(
    brightness_band_10=bt10, brightness_band_11=bt11, red=red, nir=nir,
    method="wang-2015", window_size=21, group_count=3, mask=mascara,
)
```

Wang retorna **PWV em g/cm2**. Preserve o raster bruto para diagnostico.
Uma estimativa externa de PWV tambem pode ser usada, com unidade e origem claras.

## 7. Calcular LST single-channel: Jimenez-Munoz

```python
lst_jimenez_sc = single_window(
    brightness_band_10=bt10, band_4_red=red, band_5_nir=nir,
    lst_method="jimenez-munoz-2014-sc", emissivity_method="gopinadh-2018",
    radiance_band_10=radiancia10, water_vapor=pwv,
    unit="celsius", mask=mascara,
)
```

Este metodo requer radiancia TOA da B10, BT10 correspondente, emissividade e
PWV. A restricao operacional adotada e **0..3 g/cm2**, pela perda de precisao
acima de 3 descrita no [artigo](https://doi.org/10.1109/LGRS.2014.2312032).
PWV escalar fora desse intervalo gera erro; valores raster invalidos ou fora
dele viram NaN na LST. Nao ha recorte artificial do PWV nem ajuste dos coeficientes.
B11 e usada para estimar PWV por Wang; a equacao termica SC utiliza apenas B10.

## 8. Calcular LST split-window

```python
lst_du = split_window(
    brightness_band_10=bt10, brightness_band_11=bt11,
    band_4_red=red, band_5_nir=nir,
    lst_method="du-2015", emissivity_method="gopinadh-2018",
    unit="celsius", mask=mascara,
)
mascara_pwv_sw = mascara | (pwv < 0.066) | (pwv > 7.833)
lst_jimenez_sw = split_window(
    brightness_band_10=bt10, brightness_band_11=bt11,
    band_4_red=red, band_5_nir=nir,
    lst_method="jimenez-munoz-2014-sw", emissivity_method="gopinadh-2018",
    water_vapor=pwv, unit="celsius", mask=mascara_pwv_sw,
)
```

Du sem PWV usa seu conjunto geral de coeficientes. Com PWV externo, Du aceita
escalar ou raster alinhado em 0..6.3 g/cm2. Pixels PWV invalidos viram NaN;
nao ha estimativa automatica em split_window(). Jimenez SW requer PWV.
Veja o [workflow de cena Wang -> Du](du-pwv-workflow.md).
A mascara SW acima usa o intervalo de referencia TIGR3 do estimador Wang
(0.066..7.833 g/cm2), distinto da restricao SC de 0..3; ela nao certifica acuracia.
`avdan-2016` e bloqueado no split-window; escolha `gopinadh-2018`.

## 9. Converter reflectancia TOA, se necessario

```python
with LandsatScene(pasta) as cena:
    reflectancia, _, _ = cena.calibrated(optical_quantity="reflectance")
    rho4 = reflectancia[4]
```

Esse modo usa `toa_reflectance`, com correcao solar por SZA ou MTL.
Reflectancia TOA e adimensional e nao e SR Level-2. O fluxo principal deste
guia continua em radiancia; nenhum metodo termico acrescentado exige SR.

## 10. Salvar os resultados como imagens

```python
produtos = {
    "emissividade10": (emissividade10, "dimensionless"),
    "emissividade11": (emissividade11, "dimensionless"),
    "bt10": (bt10, "kelvin"), "bt11": (bt11, "kelvin"),
    "lst_avdan": (lst_avdan, "celsius"),
    "lst_jimenez_sc": (lst_jimenez_sc, "celsius"),
    "lst_du": (lst_du, "celsius"),
    "lst_jimenez_sw": (lst_jimenez_sw, "celsius"),
    "pwv": (pwv, "g/cm2"), "reflectancia_b4": (rho4, "dimensionless"),
}
with LandsatScene(pasta) as cena:
    for nome, (imagem, unidade) in produtos.items():
        cena.write_geotiff(saida / f"{nome}.tif", imagem, units=unidade)
```

Os GeoTIFFs conservam coordenadas, unidade e NoData NaN.

## 11. Consultar metodos e requisitos

```python
catalogo = list_algorithms()
print(catalogo["single_channel"].keys())
print(catalogo["split_window"].keys())
print(catalogo["single_channel"]["jimenez-munoz-2014-sc"]["input_requirements"])
```

## Exemplos por metodo

Veja o [indice de notebooks](../exemple/README.md). Cada metodo possui seu
proprio notebook, com introducao, entradas necessarias, funcao geral,
parametros e uso com imagens. Calibracao Landsat8/9 usa o MTL;
transferencia de coeficientes de recuperacao para Landsat9 e experimental.

## PWV por Ren/MSWCVR

Com as mesmas imagens BT10/BT11, vermelho e infravermelho:

```python
pwv_ren = water_vapor(bt10, bt11, red=red, nir=nir, method="ren-2015", window_size=33, mask=mascara)
```

`33` pixels representam aproximadamente 1 km na grade Landsat de 30 m.
O metodo usa covariancia/variancia local e a regressao de Ren, sem grupos
globais de NDVI. A janela centrada e uma adaptacao declarada da aplicacao
original em suporte termico nativo; pixels reamostrados nao sao amostras
termicas independentes. PWV fora de [0.06,6.3] g/cm2 ou sem suporte suficiente
fica NaN. O resultado pode ser fornecido a Du ou Jimenez, aplicando o dominio
de cada metodo. Veja [Ren e escolhas operacionais](image-only-methods.md#ren-2015-mswcvr).
