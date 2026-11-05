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

Para usar `LandsatScene`, a pasta deve conter **B4, B5, B10, B11, MTL.txt, QA_PIXEL e QA_RADSAT**,
com os nomes originais. B2 e opcional; SZA e utilizado quando presente.
Veja [instalacao](docs/installation.md) e [preparacao dos dados](exemple/README.md).

### Onde informar e aplicar as bandas QA

**Nos exemplos com GeoTIFFs preparados, informe obrigatoriamente os caminhos de QA_PIXEL e QA_RADSAT na primeira célula de código.** A segunda célula lê as duas bandas, verifica sua grade e combina a máscara QA com nodata. A terceira chama o método com `mask=mascara`.

```python
import numpy as np
from pylstemp import read_quality_mask, emissivity

mascara = read_quality_mask(
    qa_pixel_path="cena_QA_PIXEL.TIF",
    qa_radsat_path="cena_QA_RADSAT.TIF",
    reference_path="vermelho_calibrado.tif",
)
# red e nir já carregados, na mesma grade; acrescentar nodata das entradas.
mascara |= ~np.isfinite(red) | ~np.isfinite(nir)
e10 = emissivity(red=red, nir=nir, band=10,
                 method="rongali-2018", mask=mascara)
```

Os arquivos QA pertencem à mesma cena dos dados e devem coincidir em dimensões, CRS e transformação. Se as entradas são recortes, use recortes QA idênticos. Não calibre QA, não converta seus bits para reflectância e não interpole esses arquivos.

| Etapa | Onde usar a máscara QA |
| --- | --- |
| DN → radiância/reflectância/BT | `toa_radiance(..., mask=mascara)`, `toa_reflectance(..., mask=mascara)` e `brightness(..., mask=mascara)` |
| DOS/COST | `optical_correction(..., mask=mascara)`, **antes de estimar o percentil/objeto escuro** |
| Emissividade e NDVI interno | `emissivity(..., mask=mascara)` |
| PWV e suas janelas | `water_vapor(..., mask=mascara)`; o exemplo terrestre Wang usa `exclude_water=True` na leitura QA |
| Temperatura final | `single_window(..., mask=mascara)` ou `split_window(..., mask=mascara)` |

**Rota por pasta:** `LandsatScene(pasta)` exige B4/B5/B10/B11, MTL, QA_PIXEL e QA_RADSAT; B2/SZA são opcionais. `cena.calibrated()` aplica QA antes da calibração e retorna `bandas, bt, mascara`. Reutilize essa máscara nos métodos seguintes. Para leitura manual, `cena.quality_mask()` retorna a máscara sem calibrar as bandas.

As funções numéricas continuam recebendo matrizes e `mask=`; não abrem arquivos por conta própria. `mask=None` não aplica seleção QA. As duas QA são obrigatórias em `read_quality_mask()` e nos 16 exemplos; a ausência ou o desalinhamento causa erro. `True` indica pixel inválido. A seleção QA e as flags de confiabilidade dos estimadores são etapas distintas. Veja [o fluxo completo de QA](docs/quality-inputs.md).


## Exemplo de uso com uma imagem

Abra a pasta da cena, prepare as emissividades uma vez e use os rasters prontos
na funcao de LST. Se e10/e11 ja estiverem carregados, reutilize-os:

```python
from pylstemp import emissivity, split_window
from pylstemp.scene import LandsatScene

with LandsatScene("caminho/para/cena_landsat") as cena:
    bandas, bt, mascara = cena.calibrated()
    e10 = emissivity(method="rongali-2018", band=10,
                     red=bandas[4], nir=bandas[5], mask=mascara)
    e11 = emissivity(method="rongali-2018", band=11,
                     red=bandas[4], nir=bandas[5], mask=mascara)
    lst = split_window(
        bt[10], bt[11], emissivity_10=e10, emissivity_11=e11,
        lst_method="du-2015", unit="celsius", mask=mascara,
    )
    cena.write_geotiff("lst_du.tif", lst, units="celsius")
```

`calibrated()` usa o MTL e o QA da propria imagem: B4/B5 sao radiancia TOA,
e BT10/BT11 estao em kelvin. `emissivity()` calcula o NDVI e prepara cada
emissividade; `split_window()` usa esses valores sem recalcula-los. Du usa
os coeficientes gerais, sem PWV explicito, neste exemplo.
O GeoTIFF de saida preserva a grade da cena.

**Emissividade pronta e a rota recomendada para reutilizar resultados.**
Como alternativa, forneca vermelho/NIR e `emissivity_method` diretamente a
funcao de LST, omitindo as emissividades prontas. O padrao por bandas e
Avdan em `single_window()` e Rongali em `split_window()`; Avdan e bloqueado
na rota interna de Split-window. Nao combinar as duas rotas. Kerr ainda exige
NDVI pronto ou vermelho/NIR superficiais para seu fator de vegetacao.

O exemplo le a cena inteira. Para uma demonstracao em recorte pequeno,
execute [os exemplos prontos](exemple/README.md); os detalhes de janelas ficam
nesses scripts. O [guia de uso](docs/usage.md) mostra as funcoes por etapa.

Para calcular PWV da propria imagem e usa-lo em Du, o
[workflow de cena](docs/du-pwv-workflow.md) permite escolher `wang-2015` ou
`ren-2015`, com modos geral, media e raster e exportacao com proveniencia.

## API publica

```python
from pylstemp import (
    toa_radiance, toa_reflectance, brightness,
    emissivity, water_vapor,
    single_window, split_window, optical_correction,
    list_algorithms, read_quality_mask,
)
from pylstemp.scene import LandsatScene
```

| Funcao | Entrada principal | Saida |
|---|---|---|
| `toa_radiance` | DN Level-1 e MTL | Radiancia TOA, W m-2 sr-1 um-1 |
| `toa_reflectance` | DN optico, MTL e angulo solar | Reflectancia TOA, adimensional |
| `brightness` | Radiancia termica e K1/K2 do MTL | Temperatura de brilho TOA, K |
| `emissivity` | Vermelho/NIR ou NDVI; metodo e parametros da banda | Emissividade, adimensional |
| `water_vapor` | BT10/BT11 e vermelho/NIR; Wang ou Ren | PWV, g/cm2 |
| `single_window` | BT10 e emissividade B10 pronta ou B4/B5; radiancia10 e PWV para Jimenez SC | LST, K ou Celsius |
| `split_window` | BT10/BT11 e bandas opticas ou emissividades prontas; PWV conforme o metodo | LST, K ou Celsius |
| `optical_correction` | Reflectancia TOA, method=chavez-dos/chavez-cost, angulo ou parametros reutilizados | Reflectancia corrigida / diagnosticos |
| `read_quality_mask` | Caminhos de QA_PIXEL, QA_RADSAT e reference_path, obrigatórios e alinhados | Máscara booleana; True = inválido |
| `list_algorithms` | Sem imagens | Catalogo de metodos, referencias e requisitos |

Nas chamadas diretas, use `emissivity(red=red, nir=nir, band=10)` ou
`water_vapor(bt10, bt11, red=red, nir=nir)`. O NDVI e calculado internamente.

`brightness` recebe radiancia por padrao. Para DN, use explicitamente
`input_quantity="dn"`. Reflectancia TOA pode ser escolhida no leitor com
`optical_quantity="reflectance"`; ela nao equivale a reflectancia de superficie SR.

## Algoritmos e artigos

A tabela inclui os **14 métodos do fluxo principal** e as conversões de calibração TOA. Os links
apontam para os artigos originais ou para as equacoes oficiais do USGS.
O NDVI e calculado internamente pelos metodos que precisam dele, sem funcao
publica separada nem entrada propria no catalogo.

| Modulo | Metodo | Referencia |
|---|---|---|
| Calibracao | `toa_radiance` | [USGS: radiancia Level-1](https://www.usgs.gov/landsat-missions/using-usgs-landsat-level-1-data-product) |
| Calibracao | `toa_reflectance` | [USGS: reflectancia TOA Level-1](https://www.usgs.gov/landsat-missions/using-usgs-landsat-level-1-data-product) |
| Temperatura de brilho | `brightness` | [USGS: Landsat Level-1](https://www.usgs.gov/landsat-missions/using-usgs-landsat-level-1-data-product) |
| Emissividade | `avdan-2016` | [Avdan e Jovanovska (2016)](https://doi.org/10.1155/2016/1480307) |
| Emissividade | `rongali-2018` | [Rongali et al. (2018)](https://doi.org/10.1007/s41651-018-0021-y) |
| Single-channel | `mono-window-2016` | [Avdan e Jovanovska (2016)](https://doi.org/10.1155/2016/1480307) |
| Single-channel | **`jimenez-munoz-2014-sc`** | [Jimenez-Munoz et al. (2014)](https://doi.org/10.1109/LGRS.2014.2312032) |
| Split-window | `jimenez-munoz-2014-sw` | [Jimenez-Munoz et al. (2014)](https://doi.org/10.1109/LGRS.2014.2312032) |
| Split-window | `du-2015` | [Du et al. (2015)](https://doi.org/10.3390/rs70100647) |
| Split-window | `sobrino-1993` | [Sobrino et al. (1993)](https://doi.org/10.1007/BF02524225) |
| Split-window | `kerr-1992` | [Kerr, Lagouarde e Imbernon (1992)](https://doi.org/10.1016/0034-4257(92)90078-X) |
| Split-window | `price-1984` | [Price (1984)](https://doi.org/10.1029/JD089iD05p07231) |
| Vapor d'agua | `ren-2015` | [Ren et al. (2015)](https://doi.org/10.1002/2014JD022619) |
| Vapor d'agua | `wang-2015` | [Wang et al. (2015)](https://doi.org/10.1080/2150704X.2015.1089363) |
| Correcao optica | Chavez DOS - `optical_correction(method="chavez-dos", ...)` | [Chavez (1996)](https://static1.1.sqspcdn.com/static/f/891472/15133582/1321370214637/Chavez_P.S._1996.pdf) |
| Correcao optica | Chavez COST - `optical_correction(method="chavez-cost", ...)` | [Chavez (1996)](https://static1.1.sqspcdn.com/static/f/891472/15133582/1321370214637/Chavez_P.S._1996.pdf) |

Jimenez **SC** usa B10, sua radiancia e PWV; Jimenez **SW** usa B10/B11 e PWV.
No SC adotamos uma restricao operacional de **0..3 g/cm2**: escalar fora desse
intervalo gera erro; pixels de PWV raster invalidos ou fora dele produzem NaN.
Essa restricao responde a perda de precisao do ajuste polinomial descrita no artigo.
Com PWV estimado por Wang, o fluxo SC ainda utiliza B11 nessa etapa atmosferica.

Os [métodos adicionais](docs/image-only-methods.md) incluem Ren/MSWCVR e Chavez DOS/COST, com domínios e adaptações explícitos.
Ren/MSWCVR esta disponivel como `water_vapor(..., method="ren-2015")`.
O catálogo contém 14 métodos disponíveis. Todos estão ativos; include_inactive=True retorna o mesmo conjunto. Métodos removidos não possuem chamadas explícitas.
Chavez é selecionado em `optical_correction(..., method="chavez-cost")`;
`return_diagnostics=True` retorna a reflectância corrigida e os parâmetros para reutilizar entre blocos.

`split_window` aceita bandas opticas ou emissividades prontas, na mesma funcao:

```python
lst = split_window(bt10, bt11, emissivity_10=e10, emissivity_11=e11,
                   lst_method="du-2015")
```

## Exemplos por metodo

Escolha um dos [16 notebooks em `exemple/`](exemple/README.md).
Cada notebook começa pelas entradas necessárias e suas unidades, seguidas da
chamada mínima. O exemplo executável lê somente os arquivos necessários,
aplica o método e salva o resultado. A preparação de entradas que faltarem,
as alternativas de uso e a referência completa dos parâmetros vêm depois.

Os guias agregados e scripts anteriores foram retirados da distribuicao
publica; as copias de verificacao permanecem no arquivo local.

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
    method-cards.md
    references.md
    scientific-methods.md
    usage.md
    validation.md
  exemple/
    README.md
    brightness.ipynb
    emissivity__avdan-2016.ipynb
    emissivity__rongali-2018.ipynb
    optical_correction__chavez-cost.ipynb
    optical_correction__chavez-dos.ipynb
    single_window__jimenez-munoz-2014-sc.ipynb
    single_window__mono-window-2016.ipynb
    split_window__du-2015.ipynb
    split_window__jimenez-munoz-2014-sw.ipynb
    split_window__kerr-1992.ipynb
    split_window__price-1984.ipynb
    split_window__sobrino-1993.ipynb
    toa_radiance.ipynb
    toa_reflectance.ipynb
    water_vapor__ren-2015.ipynb
    water_vapor__wang-2015.ipynb
  pylstemp/
    algorithms/
      emissivity/
        __init__.py
        avdan_2016.py
        base.py
        rongali_2018.py
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
    api.py
    calibration.py
    emissivity_models.py
    exceptions.py
    messages.py
    metadata.py
    method_cards.json
    optical.py
    provenance.py
    references.py
    registry.py
    requirements.py
    scene.py
    utils.py
    validation.py
    workflows.py
  tests/
    test_scientific_regression.py
    test_unified_api.py
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
`surface_reflectance`, em `calibration.py`, apenas escala SR Level-2 existente.

Ambiente virtual, caches, builds, dados e verificacoes locais ficam fora deste
mapa de distribuicao publica. A bateria completa e os relatorios permanecem em
`Verificacao/`; somente a regressao essencial sintetica acompanha o repositorio. Veja [responsabilidades dos modulos](docs/architecture.md)
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
detalham esses limites e as decisoes sobre as fontes. O catalogo informa
origem do sensor, localizacao na fonte e requisitos opticos; limiares de
NDVI nao sao presumidos equivalentes entre radiancia e reflectancia.

## Desenvolvimento

```bash
python -m pip install -e ".[dev,examples]"
python -c "import pylstemp; print(pylstemp.__file__)"
python -m unittest discover -s tests -v
python -m build
```

A suite essencial em `tests/` usa apenas casos sinteticos e equacoes de referencia;
a CI a executa contra o wheel instalado em Windows e Linux. A bateria completa,
verificadores de cenas, artigos, imagens e relatorios continuam em `Verificacao/`,
fora do Git e dos pacotes. As [16 fichas metodologicas](docs/method-cards.md)
registram equacoes, coeficientes, dominios e adaptacoes de todos os metodos.

## Creditos

Biblioteca original: **pylandtemp**, de **Oladimeji Mudele**.
Repositorio original: <https://github.com/pylandtemp/pylandtemp>.
Veja [CREDITS.md](CREDITS.md) e [referencias](docs/references.md).

## Diagnostic quality mode

`water_vapor`, `single_window` and `split_window` accept `quality_mode="diagnostic"` to retain mathematically calculable PWV/LST and export per-pixel quality flags. Default screened behavior is unchanged. See [diagnostic mode](docs/diagnostic-quality.md).
