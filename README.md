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

Abra a pasta da cena, leia as bandas e chame a funcao de LST:

```python
from pylstemp import split_window
from pylstemp.scene import LandsatScene

with LandsatScene("caminho/para/cena_landsat") as cena:
    bandas, bt, mascara = cena.calibrated()
    lst = split_window(
        bt[10], bt[11], bandas[4], bandas[5],
        lst_method="du-2015", unit="celsius", mask=mascara,
    )
    cena.write_geotiff("lst_du.tif", lst, units="celsius")
```

`calibrated()` usa o MTL e o QA da propria imagem: B4/B5 sao radiancia TOA,
e BT10/BT11 estao em kelvin. `split_window()` calcula NDVI e emissividades
internamente; neste exemplo, Du usa os coeficientes gerais, sem PWV explicito.
O GeoTIFF de saida preserva a grade da cena.

O exemplo le a cena inteira. Para uma demonstracao em recorte pequeno,
execute [os exemplos prontos](exemples/DATA.md); os detalhes de janelas ficam
nesses scripts. O [guia de uso](docs/usage.md) mostra as funcoes por etapa.

Para calcular PWV da propria imagem e usa-lo em Du, o
[workflow de cena](docs/du-pwv-workflow.md) permite escolher `wang-2015` ou
`ren-2015`, com modos geral, media e raster e exportacao com proveniencia.

## API publica

```python
from pylstemp import (
    toa_radiance, toa_reflectance, brightness,
    emissivity, water_vapor,
    single_window, split_window, split_window_from_emissivity,
    sobrino_2004_tm6, sobrino_2008, fit_chavez, chavez_reflectance,
    list_algorithms,
)
from pylstemp.scene import LandsatScene
```

| Funcao | Entrada principal | Saida |
|---|---|---|
| `toa_radiance` | DN Level-1 e MTL | Radiancia TOA, W m-2 sr-1 um-1 |
| `toa_reflectance` | DN optico, MTL e angulo solar | Reflectancia TOA, adimensional |
| `brightness` | Radiancia termica e K1/K2 do MTL | Temperatura de brilho TOA, K |
| `emissivity` | Vermelho/NIR e banda 10/11; NDVI interno | Emissividade, adimensional |
| `water_vapor` | BT10/BT11 e vermelho/NIR; Wang ou Ren | PWV, g/cm2 |
| `single_window` | BT10, B4/B5; radiancia10 e PWV para Jimenez SC | LST, K ou Celsius |
| `split_window` | BT10, BT11, B4/B5 e PWV conforme o metodo | LST, K ou Celsius |
| `split_window_from_emissivity` | BT10/BT11 e emissividades por banda preparadas | LST, K ou Celsius |
| `sobrino_2004_tm6` | Vermelho/NIR; parametrizacao especifica de TM5 banda 6 | Emissividade, adimensional |
| `sobrino_2008` | Vermelho/NIR e parametros espectrais por banda | Emissividade, adimensional |
| `fit_chavez` / `chavez_reflectance` | Reflectancia TOA, angulo solar e mascara | Parametros / cenario optico corrigido |
| `list_algorithms` | Sem imagens | Catalogo de metodos, referencias e requisitos |

Nas chamadas diretas, use `emissivity(red=red, nir=nir, band=10)` ou
`water_vapor(bt10, bt11, red=red, nir=nir)`. O NDVI e calculado internamente.

`brightness` recebe radiancia por padrao. Para DN, use explicitamente
`input_quantity="dn"`. Reflectancia TOA pode ser escolhida no leitor com
`optical_quantity="reflectance"`; ela nao equivale a reflectancia de superficie SR.

## Algoritmos e artigos

A tabela inclui os **13 algoritmos registrados**, as funcoes de calibracao
TOA e os metodos de emissividade Sobrino e correcao optica Chavez. Os links
apontam para os artigos originais ou para as equacoes oficiais do USGS.
O NDVI e calculado internamente pelos metodos que precisam dele, sem funcao
publica separada nem entrada propria no catalogo.

| Modulo | Metodo | Referencia |
|---|---|---|
| Calibracao | `toa_radiance` | [USGS: radiancia Level-1](https://www.usgs.gov/landsat-missions/using-usgs-landsat-level-1-data-product) |
| Calibracao | `toa_reflectance` | [USGS: reflectancia TOA Level-1](https://www.usgs.gov/landsat-missions/using-usgs-landsat-level-1-data-product) |
| Temperatura de brilho | `brightness` | [USGS: Landsat Level-1](https://www.usgs.gov/landsat-missions/using-usgs-landsat-level-1-data-product) |
| Emissividade | `avdan-2016` | [Avdan e Jovanovska (2016)](https://doi.org/10.1155/2016/1480307) |
| Emissividade | `gopinadh-2018` | [Rongali et al. (2018)](https://doi.org/10.1007/s41651-018-0021-y) |
| Emissividade | `sobrino_2004_tm6` - Landsat TM5, banda 6 | [Sobrino, Jimenez-Munoz e Paolini (2004)](https://doi.org/10.1016/j.rse.2004.02.003) |
| Emissividade | `sobrino_2008(..., variant="simplified")` - Eq.9 | [Sobrino et al. (2008)](https://doi.org/10.1109/TGRS.2007.904834) |
| Emissividade | `sobrino_2008(..., variant="full")` - Eqs.5-8 | [Sobrino et al. (2008)](https://doi.org/10.1109/TGRS.2007.904834) |
| Single-channel | `mono-window-2016` | [Avdan e Jovanovska (2016)](https://doi.org/10.1155/2016/1480307) |
| Single-channel | **`jimenez-munoz-sc-2014`** | [Jimenez-Munoz et al. (2014)](https://doi.org/10.1109/LGRS.2014.2312032) |
| Split-window | `jimenez-munoz-2014` | [Jimenez-Munoz et al. (2014)](https://doi.org/10.1109/LGRS.2014.2312032) |
| Split-window | `du-2015` | [Du et al. (2015)](https://doi.org/10.3390/rs70100647) |
| Split-window | `sobrino-1993` | [Sobrino et al. (1993)](https://doi.org/10.1007/BF02524225) |
| Split-window | `kerr-1992` | [Kerr, Lagouarde e Imbernon (1992)](https://doi.org/10.1016/0034-4257(92)90078-X) |
| Split-window | `price-1984` | [Price (1984)](https://doi.org/10.1029/JD089iD05p07231) |
| Split-window | `rozenstein-2014` | [Rozenstein et al. (2014)](https://doi.org/10.3390/s140405768) |
| Vapor d'agua | `ren-2015` | [Ren et al. (2015)](https://doi.org/10.1002/2014JD022619) |
| Vapor d'agua | `wang-2015` | [Wang et al. (2015)](https://doi.org/10.1080/2150704X.2015.1089363) |
| Correcao optica | Chavez DOS - `fit_chavez(..., method="dos")` e `chavez_reflectance` | [Chavez (1996)](https://static1.1.sqspcdn.com/static/f/891472/15133582/1321370214637/Chavez_P.S._1996.pdf) |
| Correcao optica | Chavez COST - `fit_chavez(..., method="cost")` e `chavez_reflectance` | [Chavez (1996)](https://static1.1.sqspcdn.com/static/f/891472/15133582/1321370214637/Chavez_P.S._1996.pdf) |

Jimenez **SC** usa B10, sua radiancia e PWV; Jimenez **SW** usa B10/B11 e PWV.
No SC adotamos uma restricao operacional de **0..3 g/cm2**: escalar fora desse
intervalo gera erro; pixels de PWV raster invalidos ou fora dele produzem NaN.
Essa restricao responde a perda de precisao do ajuste polinomial descrita no artigo.
Com PWV estimado por Wang, o fluxo SC ainda utiliza B11 nessa etapa atmosferica.

Os [metodos adicionais](docs/image-only-methods.md) incluem Rozenstein,
Ren/MSWCVR, Sobrino 2004/2008 e Chavez DOS/COST, com dominios e adaptacoes explicitos.
Ren/MSWCVR esta disponivel como `water_vapor(..., method="ren-2015")`.
As funcoes Sobrino e Chavez sao parametrizadas e nao acrescentam entradas
ao registro de `list_algorithms()`, mas estao implementadas e listadas na tabela.
Sobrino 2004 e especifico de TM6; Sobrino 2008 exige parametros por banda e,
na variante completa, reflectancia de superficie. Chavez DOS/COST recebe
reflectancia TOA e usa os parametros retornados por `fit_chavez`.

## Exemplos executaveis

```bash
python exemples/fluxo_completo.py CAMINHO_DA_CENA --saida resultados
```

O script demonstra a cadeia com Wang e salva **nove GeoTIFFs**, incluindo Jimenez
single-channel e split-window. Os [cinco notebooks](exemples/DATA.md) mostram
as funcoes por modulo; altere a pasta da cena na primeira celula.

## Estrutura e extensao

Mapa completo dos arquivos publicos existentes nesta versao, incluindo
biblioteca, documentacao, exemplos e configuracoes do repositorio:

```text
v1.11/
  .github/
    ISSUE_TEMPLATE/
      bug_report.md
      feature_request.md
    workflows/
      ci.yml
      publish.yml
    pull_request_template.md
  docs/
    api-reference.md
    architecture.md
    du-pwv-workflow.md
    extending.md
    image-only-methods.md
    index.md
    installation.md
    references.md
    scientific-methods.md
    usage.md
    validation.md
  exemples/
    brightness.ipynb
    DATA.md
    emissivity.ipynb
    fluxo_completo.py
    metodos_imagem.py
    single_window.ipynb
    split_window.ipynb
    water_vapor.ipynb
  pylstemp/
    algorithms/
      emissivity/
        __init__.py
        avdan_2016.py
        base.py
        gopinadh_2018.py
      radiative_transfer/  # familia reservada; sem algoritmo implementado
        __init__.py
      single_channel/
        __init__.py
        base.py
        jimenez_munoz_2014.py
        mono_window_2016.py
      split_window/
        __init__.py
        base.py
        du_2015.py
        jimenez_munoz_2014.py
        kerr_1992.py
        price_1984.py
        rozenstein_2014.py
        sobrino_1993.py
      thermal/
        __init__.py
        brightness.py
      water_vapor/
        __init__.py
        ren_2015.py
        wang_2015.py
      __init__.py
      base_temperature.py
    sensors/
      __init__.py
      landsat.py
    __init__.py
    api.py  # API publica, sem dispatcher de indices
    calibration.py
    emissivity_models.py  # Sobrino 2004/2008; NDVI interno
    exceptions.py
    messages.py
    metadata.py
    optical.py  # Chavez DOS/COST
    references.py
    registry.py
    requirements.py
    scene.py
    utils.py  # NDVI interno compartilhado e auxiliares numericos
    validation.py
    workflows.py
  .gitattributes
  .gitignore
  CHANGELOG.md
  CODE_OF_CONDUCT.md
  CONTRIBUTING.md
  CREDITS.md
  LICENSE
  MANIFEST.in
  pyproject.toml
  README.md
```

Cada algoritmo declara `ALGORITHM_SPEC`. A descoberta automatica por familia
alimenta `list_algorithms()`; arquivos de compatibilidade nao duplicam metodos.
A familia `radiative_transfer` existe como reserva, sem algoritmo implementado.
`surface_reflectance`, em `calibration.py`, apenas escala SR Level-2 existente.

Ambiente virtual, caches, builds, dados e verificacoes locais ficam fora deste
mapa de distribuicao publica. Testes e relatorios permanecem em `Verificacao/`,
fora do repositorio publico. Veja [responsabilidades dos modulos](docs/architecture.md)
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
Price/Kerr/Sobrino 1993 sao adaptacoes historicas AVHRR. NDVI em radiancia e
reflectancia pode diferir; os limiares de emissividade requerem justificativa
para a convencao adotada. Os [contratos cientificos](docs/scientific-methods.md)
detalham esses limites e as decisoes sobre as fontes.

## Desenvolvimento

```bash
python -m pip install -e ".[dev,examples]"
python -c "import pylstemp; print(pylstemp.__file__)"
python -m build
```

Testes cientificos, verificadores de cenas e relatorios ficam no arquivo local
`Verificacao/`, fora do Git e dos pacotes. A CI publica confere instalacao,
importacao e empacotamento em Windows e Linux.

## Creditos

Biblioteca original: **pylandtemp**, de **Oladimeji Mudele**.
Repositorio original: <https://github.com/pylandtemp/pylandtemp>.
Veja [CREDITS.md](CREDITS.md) e [referencias](docs/references.md).
