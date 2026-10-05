# pyLSTemp

[![CI](https://github.com/daciocambraia/pyLSTemp/actions/workflows/ci.yml/badge.svg)](https://github.com/daciocambraia/pyLSTemp/actions/workflows/ci.yml)
[![License](https://img.shields.io/badge/license-Apache%202.0-blue.svg)](LICENSE)

Biblioteca Python modular para estimar **temperatura da superficie (LST)** com
imagens **Landsat 8 e Landsat 9 Collection 2 Level-1**. Versao: **1.11.0**, em preparacao.

Repositorio: <https://github.com/daciocambraia/pyLSTemp>.

## Objetivos

- Oferecer um fluxo claro: calibracao, NDVI, emissividade, BT, PWV e LST.
- Manter radiancia TOA como padrao e reflectancia TOA como conversao explicita.
- Ler os coeficientes de calibracao do MTL correspondente a cada imagem.
- Preservar formulas publicadas, referencias, unidades e requisitos de entrada.
- Organizar cada algoritmo em seu proprio modulo, com descoberta automatica.

## Instalacao

Na raiz desta versao:

```bash
python -m pip install -e ".[examples]"
```

A pasta da cena deve conter **B4, B5, B10, B11, MTL.txt, QA_PIXEL e QA_RADSAT**,
com os nomes originais. B2 e opcional; SZA e utilizado quando presente.
Veja [instalacao](docs/installation.md) e [preparacao dos dados](exemples/DATA.md).

## Exemplo de uso com uma imagem

Abra a cena, calibre as bandas e associe as funcoes:

```python
from pathlib import Path
from pylstemp.scene import LandsatScene
from pylstemp import spectral_index, single_window, split_window

pasta = Path("caminho/para/cena_landsat")
saida = Path("resultados")
saida.mkdir(parents=True, exist_ok=True)

with LandsatScene(pasta) as cena:
    altura, largura = cena.shape
    linha = max(0, altura // 2 - 128)
    coluna = max(0, largura // 2 - 128)
    janela = (linha, min(altura, linha + 256), coluna, min(largura, coluna + 256))
    bandas, temperatura, mascara = cena.calibrated(janela)
    red, nir = bandas[4], bandas[5]              # radiancia TOA
    bt10, bt11 = temperatura[10], temperatura[11]  # kelvin

    ndvi = spectral_index(index="ndvi", red=red, nir=nir, mask=mascara)
    lst_single = single_window(
        brightness_band_10=bt10, band_4_red=red, band_5_nir=nir,
        lst_method="mono-window-2016", emissivity_method="avdan-2016",
        unit="celsius", mask=mascara,
    )
    lst_split = split_window(
        brightness_band_10=bt10, brightness_band_11=bt11,
        band_4_red=red, band_5_nir=nir,
        lst_method="du-2015", emissivity_method="gopinadh-2018",
        unit="celsius", mask=mascara,
    )
    cena.write_geotiff(saida / "ndvi.tif", ndvi, window=janela, units="dimensionless")
    cena.write_geotiff(saida / "lst_single.tif", lst_single, window=janela, units="celsius")
    cena.write_geotiff(saida / "lst_split.tif", lst_split, window=janela, units="celsius")
```

Esse recorte central de ate 256 x 256 pixels permite experimentar rapidamente.
`calibrated` le DN, usa o MTL e aplica QA. As funcoes LST calculam NDVI e
emissividade internamente. O arquivo exportado preserva a grade do recorte.

O [guia de uso](docs/usage.md) apresenta cada funcao separadamente, incluindo
DN -> radiancia -> BT e o novo single-channel Jimenez-Munoz com PWV.

## API publica

```python
from pylstemp import (
    toa_radiance, toa_reflectance, brightness,
    spectral_index, emissivity, water_vapor,
    single_window, split_window, list_algorithms,
)
from pylstemp.scene import LandsatScene
```

| Funcao | Entrada principal | Saida |
|---|---|---|
| `toa_radiance` | DN Level-1 e MTL | Radiancia TOA, W m-2 sr-1 um-1 |
| `toa_reflectance` | DN optico, MTL e angulo solar | Reflectancia TOA, adimensional |
| `brightness` | Radiancia termica e K1/K2 do MTL | Temperatura de brilho TOA, K |
| `spectral_index` | B4/B5 calibradas na mesma convencao | NDVI, adimensional |
| `emissivity` | NDVI e banda 10/11 | Emissividade, adimensional |
| `water_vapor` | BT10, BT11 e NDVI | PWV, g/cm2 |
| `single_window` | BT10, B4/B5; radiancia10 e PWV para Jimenez SC | LST, K ou Celsius |
| `split_window` | BT10, BT11, B4/B5 e PWV conforme o metodo | LST, K ou Celsius |
| `list_algorithms` | Sem imagens | Catalogo de metodos, referencias e requisitos |

`brightness` recebe radiancia por padrao. Para DN, use explicitamente
`input_quantity="dn"`. Reflectancia TOA pode ser escolhida no leitor com
`optical_quantity="reflectance"`; ela nao equivale a reflectancia de superficie SR.

## Algoritmos e artigos

O catalogo tem **12 entradas**. Os links abaixo apontam para os trabalhos
originais ou, no caso da calibracao, para as equacoes oficiais do USGS.

| Modulo | Metodo | Referencia |
|---|---|---|
| Indice | `ndvi` | [Rouse et al. (1974)](https://ntrs.nasa.gov/citations/19740022614) |
| Temperatura de brilho | `brightness` | [USGS: Landsat Level-1](https://www.usgs.gov/landsat-missions/using-usgs-landsat-level-1-data-product) |
| Emissividade | `avdan-2016` | [Avdan e Jovanovska (2016)](https://doi.org/10.1155/2016/1480307) |
| Emissividade | `gopinadh-2018` | [Rongali et al. (2018)](https://doi.org/10.1007/s41651-018-0021-y) |
| Single-channel | `mono-window-2016` | [Avdan e Jovanovska (2016)](https://doi.org/10.1155/2016/1480307) |
| Single-channel | **`jimenez-munoz-sc-2014`** | [Jimenez-Munoz et al. (2014)](https://doi.org/10.1109/LGRS.2014.2312032) |
| Split-window | `jimenez-munoz-2014` | [Jimenez-Munoz et al. (2014)](https://doi.org/10.1109/LGRS.2014.2312032) |
| Split-window | `du-2015` | [Du et al. (2015)](https://doi.org/10.3390/rs70100647) |
| Split-window | `sobrino-1993` | [Sobrino et al. (1993)](https://doi.org/10.1007/BF02524225) |
| Split-window | `kerr-1992` | [Kerr, Lagouarde e Imbernon (1992)](https://doi.org/10.1016/0034-4257(92)90078-X) |
| Split-window | `price-1984` | [Price (1984)](https://doi.org/10.1029/JD089iD05p07231) |
| Vapor d'agua | `wang-2015` | [Wang et al. (2015)](https://doi.org/10.1080/2150704X.2015.1089363) |

Jimenez **SC** usa B10, sua radiancia e PWV; Jimenez **SW** usa B10/B11 e PWV.
No SC adotamos uma restricao operacional de **0..3 g/cm2**: escalar fora desse
intervalo gera erro; pixels de PWV raster invalidos ou fora dele produzem NaN.
Essa restricao responde a perda de precisao do ajuste polinomial descrita no artigo.
Com PWV estimado por Wang, o fluxo SC ainda utiliza B11 nessa etapa atmosferica.

## Exemplos executaveis

```bash
python exemples/fluxo_completo.py CAMINHO_DA_CENA --saida resultados
```

O script conecta todos os modulos e salva **dez GeoTIFFs**, incluindo Jimenez
single-channel e split-window. Os [seis notebooks](exemples/DATA.md) mostram
as funcoes por modulo; altere a pasta da cena na primeira celula.

## Estrutura e extensao

```text
pylstemp/
  api.py                 # funcoes publicas
  calibration.py         # MTL, radiancia, reflectancia e BT
  scene.py               # leitura e exportacao de imagens
  registry.py            # descoberta dos algoritmos
  sensors/               # constantes dos sensores
  algorithms/
    spectral_index/
    thermal/
    emissivity/
    single_channel/
    split_window/
    water_vapor/
    radiative_transfer/  # familia reservada; sem metodo implementado
```

Cada arquivo de algoritmo declara `ALGORITHM_SPEC`. A descoberta automatica
por familia alimenta `list_algorithms()`; consulte [arquitetura](docs/architecture.md)
e [como adicionar metodos](docs/extending.md).

## Documentacao

- [Indice da documentacao](docs/index.md)
- [Instalacao](docs/installation.md)
- [Guia de uso por funcao](docs/usage.md)
- [Referencia da API](docs/api-reference.md)
- [Metodos cientificos e migracao](docs/scientific-methods.md)
- [Validacao atual](docs/validation.md)
- [Referencias bibliograficas](docs/references.md)

## Validacao e limites cientificos

Testes de formulas e execucao em imagens verificam a implementacao; ainda nao
ha validacao independente de acuracia de LST/PWV com dados de campo.
Coeficientes de recuperacao Landsat 8 aplicados ao Landsat 9 sao experimentais.
Price/Kerr/Sobrino sao adaptacoes historicas AVHRR. NDVI em radiancia e
reflectancia pode diferir; os limiares de emissividade requerem justificativa
para a convencao adotada. Os [contratos cientificos](docs/scientific-methods.md)
detalham esses limites e as decisoes sobre as fontes.

## Desenvolvimento

```bash
python -m pip install -e ".[dev,examples]"
python -c "import pylstemp; print(pylstemp.__file__)"
python -m pytest
python -m build
```

Resultados de verificacao ficam em `Verificacao/`; imagens, relatorios locais
e resultados historicos nao sao distribuidos com a biblioteca.

## Creditos

Biblioteca original: **pylandtemp**, de **Oladimeji Mudele**.
Repositorio original: <https://github.com/pylandtemp/pylandtemp>.
Veja [CREDITS.md](CREDITS.md) e [referencias](docs/references.md).
