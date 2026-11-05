# pyLSTemp

[![CI](https://github.com/daciocambraia/pyLSTemp/actions/workflows/ci.yml/badge.svg)](https://github.com/daciocambraia/pyLSTemp/actions/workflows/ci.yml)
[![License](https://img.shields.io/badge/license-Apache%202.0-blue.svg)](LICENSE)

Biblioteca Python modular para estimar **temperatura da superficie (LST)** com
imagens **Landsat 8 e Landsat 9 Collection 2 Level-1**. Versao: **2.0.0**.

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
from pylstemp import quality_mask, emissivity

mascara = quality_mask(
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

As funções numéricas continuam recebendo matrizes e `mask=`; não abrem arquivos por conta própria. `mask=None` não aplica seleção QA. As duas QA são obrigatórias em `quality_mask()` e nos 17 exemplos; a ausência ou o desalinhamento causa erro. `True` indica pixel inválido. A seleção QA e as flags de confiabilidade dos estimadores são etapas distintas. Veja [o fluxo completo de QA](docs/quality-inputs.md).


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
        method="du-2015", unit="celsius", mask=mascara,
    )
    cena.write_geotiff("lst_du.tif", lst, units="celsius")
```

`calibrated()` usa o MTL e o QA da propria imagem: B4/B5 sao radiancia TOA,
e BT10/BT11 estao em kelvin. `emissivity()` calcula o NDVI e prepara cada
emissividade; `split_window()` usa esses valores sem recalcula-los. Du usa
os coeficientes gerais, sem PWV explicito, neste exemplo.
O GeoTIFF de saida preserva a grade da cena.

**Emissividade pronta e a rota recomendada para reutilizar resultados.**
Como alternativa, forneca vermelho/NIR diretamente a funcao de LST, omitindo
as emissividades prontas. Essa rota usa Avdan em `single_window()` e Rongali
em `split_window()`. Para escolher o modelo de emissividade, use
`emissivity(..., method=...)` separadamente e forneca os rasters prontos. Nao combinar as duas rotas. Kerr ainda exige
NDVI pronto ou vermelho/NIR superficiais para seu fator de vegetacao.

O exemplo le a cena inteira. Para uma demonstracao em recorte pequeno,
execute [os exemplos prontos](exemple/README.md); os detalhes de janelas ficam
nesses scripts. O [guia de uso](docs/usage.md) mostra as funcoes por etapa.

Para calcular PWV da propria imagem e usa-lo em Du, o
[workflow de cena](docs/du-pwv-workflow.md) permite escolher `wang-2015` ou
`ren-2015`, com modos geral, media e raster e exportacao com proveniencia.

## Calibracao radiometrica

As conversoes ficam agrupadas em `pylstemp/calibration/`, com um modulo por
operacao e selecao explicita por `method`:

```python
from pylstemp import calibrate

radiancia = calibrate(dn10, method="toa-radiance", metadata=metadata, band=10, mask=mascara)
reflectancia = calibrate(dn4, method="toa-reflectance", metadata=metadata, band=4, mask=mascara)
bt10 = calibrate(radiancia, method="brightness", metadata=metadata, band=10, mask=mascara)
```

Radiancia TOA e a entrada padrao de `brightness`; para DN, informe
`input_quantity="dn"`. As funcoes diretas `toa_radiance`, `toa_reflectance`
e `brightness` continuam disponiveis. Veja [calibracao](docs/calibration.md).

## Selecao de metodos

Todas as familias usam exclusivamente `method=`. Em uma cadeia composta,
cada etapa seleciona seu proprio metodo:

```python
e10 = emissivity(red=red, nir=nir, band=10, method="rongali-2018", mask=mascara)
e11 = emissivity(red=red, nir=nir, band=11, method="rongali-2018", mask=mascara)
lst = split_window(bt10, bt11, method="du-2015",
                   emissivity_10=e10, emissivity_11=e11, mask=mascara)
```

Veja [seletores e migracao](docs/method-selection.md).

## API publica

A entrada principal e uma funcao por familia. Todas as familias selecionam o
algoritmo com `method=`; a familia faz parte da identidade do metodo.

```python
from pylstemp import (
    calibrate, emissivity, single_window, split_window,
    water_vapor, optical_correction,
    read_mtl, quality_mask, list_algorithms,
)
```

### Familias de calculo

| Familia / funcao | Valores de `method` | Entrada e resultado |
|---|---|---|
| `calibrate` | `toa-radiance`, `toa-reflectance`, `brightness` | DN/MTL para radiancia ou reflectancia TOA; radiancia termica para BT em K |
| `emissivity` | `avdan-2016`, `rongali-2018` | Vermelho/NIR ou NDVI preparado para emissividade adimensional por banda |
| `single_window` | `avdan-2016`, `jimenez-munoz-2014` | BT10 e emissividade B10 para LST; Jimenez SC tambem exige radiancia10 e PWV |
| `split_window` | `du-2015`, `jimenez-munoz-2014`, `price-1984`, `kerr-1992`, `sobrino-1993` | BT10/BT11 e emissividades B10/B11 para LST; PWV/NDVI conforme o metodo |
| `water_vapor` | `wang-2015`, `ren-2015` | BT10/BT11 e vermelho/NIR ou NDVI preparado para PWV em g/cm2 |
| `optical_correction` | `chavez-dos-1996`, `chavez-cost-1996` | Reflectancia TOA e angulo solar/parametros de cena para reflectancia corrigida aproximada |

`calibrate` exige `method`; `split_window` tambem requer uma selecao explicita.
Os padroes das demais familias sao Avdan para emissividade/LST single-channel,
Wang para PWV e COST para correcao optica.
A rota LST por bandas usa Avdan fixo em single-channel e Rongali fixo em
split-window. Para escolher a emissividade, calcule-a com
`emissivity(..., method=...)` e forneca `emissivity_10`/`emissivity_11` prontas.
Kerr requer tambem NDVI preparado ou vermelho/NIR de reflectancia superficial.
A saida LST usa `unit="kelvin"` ou `unit="celsius"`.

### Metadados, qualidade e catalogo

Essas funcoes de apoio executam uma unica operacao e nao recebem `method=`.

| Funcao | Entrada | Saida |
|---|---|---|
| `read_mtl` | Caminho do MTL Landsat 8/9 correspondente | Dicionario de metadados e coeficientes |
| `quality_mask` | Caminhos de QA_PIXEL, QA_RADSAT e `reference_path`, obrigatorios e alinhados | Mascara booleana; True = invalido |
| `list_algorithms` | Sem imagens; `include_inactive` preservado para compatibilidade | Catalogo por familia e metodo, com referencias, entradas e limites |

Combine QA com nodata de todas as entradas e passe `mask=mascara` aos calculos.
O NDVI e calculado internamente quando vermelho/NIR sao fornecidos.
Veja o [exemplo de quality_mask](exemple/quality_mask.ipynb).

### Conversoes diretas de calibracao

As tres operacoes pertencem a familia `calibrate`; as chamadas diretas abaixo
continuam exportadas na raiz e em `pylstemp.calibration`, sem seletor adicional.

```python
from pylstemp import toa_radiance, toa_reflectance, brightness
```

| Funcao direta | Chamada agrupada equivalente | Saida |
|---|---|---|
| `toa_radiance` | `calibrate(dn, method="toa-radiance", ...)` | Radiancia TOA, W m-2 sr-1 um-1 |
| `toa_reflectance` | `calibrate(dn, method="toa-reflectance", ...)` | Reflectancia TOA, adimensional |
| `brightness` | `calibrate(radiancia, method="brightness", ...)` | Temperatura de brilho TOA, K |

`brightness` recebe radiancia por padrao; para DN, informe `input_quantity="dn"`.
Reflectancia TOA nao equivale a reflectancia superficial e BT nao equivale a LST.

Outros auxiliares sao importados de seu modulo:

```python
from pylstemp.calibration import (
    brightness_from_mtl, surface_reflectance, normalize_thermal_band,
)
```

| Funcao | Operacao |
|---|---|
| `brightness_from_mtl` | DN termico para BT, usando MTL; atalho de `brightness(..., input_quantity="dn")` |
| `surface_reflectance` | Escala DN de um produto SR Level-2 existente; nao corrige a atmosfera de DN Level-1 |
| `normalize_thermal_band` | Normaliza a identificacao de B10/B11 para `band_10`/`band_11` |

### Cenas e workflows

```python
from pylstemp.scene import LandsatScene
from pylstemp.workflows import du_from_scene, scene_ndvi_range, DuSceneResult
```

| Interface | Operacao |
|---|---|
| `LandsatScene` | Abre uma pasta Level-1 alinhada, com MTL e QA, e gerencia os arquivos |
| `LandsatScene.read` | Le uma banda/QA por identificador e janela opcional |
| `LandsatScene.quality_mask` | Retorna a mascara QA da cena, com exclusao opcional de agua |
| `LandsatScene.calibrated` | Retorna bandas opticas calibradas, BT10/BT11 e mascara QA |
| `LandsatScene.write_geotiff` | Exporta um raster preservando a grade da cena/janela |
| `LandsatScene.close` | Fecha os arquivos; `with LandsatScene(...)` faz isso automaticamente |
| `scene_ndvi_range` | Calcula os limites globais de NDVI terrestre usados no agrupamento Wang |
| `du_from_scene` | Compoe Du LST e Rongali com PWV geral, medio ou raster; `method` seleciona Wang/Ren |
| `DuSceneResult` | Reune resultados selecionados, brutos e filtrados de LST/PWV, flags, proveniencia e intermediarios opcionais |
| `DuSceneResult.export` | Exporta os produtos e a proveniencia do resultado |

As tabelas cobrem as 12 funcoes exportadas na raiz e os auxiliares publicos
de calibracao/cenas/workflows. `ORIGINAL_LIBRARY_CREDIT` tambem e exportado
na raiz: e uma constante de creditos, nao uma funcao.
Veja as assinaturas e os requisitos completos na [referencia da API](docs/api-reference.md).

## Algoritmos e artigos

O identificador deve ser lido junto com a familia. `avdan-2016` em emissividade
e em single-channel representa etapas diferentes; `jimenez-munoz-2014` usa a
formulacao SC em `single_window` e SW em `split_window`.


A tabela inclui os **14 métodos do fluxo principal** e as conversões de calibração TOA. Os links
apontam para os artigos originais ou para as equacoes oficiais do USGS.
O NDVI e calculado internamente pelos metodos que precisam dele, sem funcao
publica separada nem entrada propria no catalogo.

| Modulo | Metodo | Referencia |
|---|---|---|
| Calibracao | `toa-radiance` | [USGS: radiancia Level-1](https://www.usgs.gov/landsat-missions/using-usgs-landsat-level-1-data-product) |
| Calibracao | `toa-reflectance` | [USGS: reflectancia TOA Level-1](https://www.usgs.gov/landsat-missions/using-usgs-landsat-level-1-data-product) |
| Calibracao | `brightness` | [USGS: Landsat Level-1](https://www.usgs.gov/landsat-missions/using-usgs-landsat-level-1-data-product) |
| Emissividade | `avdan-2016` | [Avdan e Jovanovska (2016)](https://doi.org/10.1155/2016/1480307) |
| Emissividade | `rongali-2018` | [Rongali et al. (2018)](https://doi.org/10.1007/s41651-018-0021-y) |
| Single-channel | `avdan-2016` | [Avdan e Jovanovska (2016)](https://doi.org/10.1155/2016/1480307) |
| Single-channel | `jimenez-munoz-2014` | [Jimenez-Munoz et al. (2014)](https://doi.org/10.1109/LGRS.2014.2312032) |
| Split-window | `jimenez-munoz-2014` | [Jimenez-Munoz et al. (2014)](https://doi.org/10.1109/LGRS.2014.2312032) |
| Split-window | `du-2015` | [Du et al. (2015)](https://doi.org/10.3390/rs70100647) |
| Split-window | `sobrino-1993` | [Sobrino et al. (1993)](https://doi.org/10.1007/BF02524225) |
| Split-window | `kerr-1992` | [Kerr, Lagouarde e Imbernon (1992)](https://doi.org/10.1016/0034-4257(92)90078-X) |
| Split-window | `price-1984` | [Price (1984)](https://doi.org/10.1029/JD089iD05p07231) |
| Vapor d'agua | `ren-2015` | [Ren et al. (2015)](https://doi.org/10.1002/2014JD022619) |
| Vapor d'agua | `wang-2015` | [Wang et al. (2015)](https://doi.org/10.1080/2150704X.2015.1089363) |
| Correcao optica | `chavez-dos-1996` | [Chavez (1996)](https://static1.1.sqspcdn.com/static/f/891472/15133582/1321370214637/Chavez_P.S._1996.pdf) |
| Correcao optica | `chavez-cost-1996` | [Chavez (1996)](https://static1.1.sqspcdn.com/static/f/891472/15133582/1321370214637/Chavez_P.S._1996.pdf) |

Jimenez **SC** usa B10, sua radiancia e PWV; Jimenez **SW** usa B10/B11 e PWV.
No SC adotamos uma restricao operacional de **0..3 g/cm2**: escalar fora desse
intervalo gera erro; pixels de PWV raster invalidos ou fora dele produzem NaN.
Essa restricao responde a perda de precisao do ajuste polinomial descrita no artigo.
Com PWV estimado por Wang, o fluxo SC ainda utiliza B11 nessa etapa atmosferica.

Os [métodos adicionais](docs/image-only-methods.md) incluem Ren/MSWCVR e Chavez DOS/COST, com domínios e adaptações explícitos.
Ren/MSWCVR esta disponivel como `water_vapor(..., method="ren-2015")`.
O catálogo contém 14 métodos disponíveis. Todos estão ativos; include_inactive=True retorna o mesmo conjunto. Métodos removidos não possuem chamadas explícitas.
Chavez é selecionado em `optical_correction(..., method="chavez-cost-1996")`;
`return_diagnostics=True` retorna a reflectância corrigida e os parâmetros para reutilizar entre blocos.

`split_window` aceita bandas opticas ou emissividades prontas, na mesma funcao:

```python
lst = split_window(bt10, bt11, emissivity_10=e10, emissivity_11=e11,
                   method="du-2015")
```

## Exemplos por metodo

Escolha um dos [17 notebooks em `exemple/`](exemple/README.md).
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
pylstemp/
  algorithms/       # implementacoes por familia e metodo
  calibration/      # conversoes radiometricas e leitura MTL
  sensors/          # constantes de fallback
  api.py            # familias numericas e catalogo
  diagnostics.py    # identidade comum dos resultados
  quality.py        # flags e legenda
  inputs.py         # arquivos QA alinhados
  scene.py          # leitura de cenas e GeoTIFF
  workflows.py      # composicao de etapas
  provenance.py     # rastreabilidade
  method_cards.json # fichas por familia e metodo
tests/              # contratos e integracao sintetica
exemple/            # 17 notebooks
docs/               # documentacao vigente
.github/            # CI e publicacao
```

Ambientes, caches, pacotes gerados e materiais de pesquisas especificas nao
fazem parte da distribuicao. Veja [arquitetura](docs/architecture.md) e
[extensao](docs/extending.md).

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
python -m pytest tests -q
python -m build --outdir ../dist-pylstemp
```

A suite em `tests/` verifica equacoes, contratos, exportacoes e os 17 notebooks
com fixtures sinteticas. A CI a executa contra o wheel instalado em Windows
e Linux. As [fichas](docs/method-cards.md) documentam as fontes e limites;
[verificacao](docs/validation.md) descreve o alcance dos testes.

## Creditos

Biblioteca original: **pylandtemp**, de **Oladimeji Mudele**.
Repositorio original: <https://github.com/pylandtemp/pylandtemp>.
Veja [CREDITS.md](CREDITS.md) e [referencias](docs/references.md).

## Diagnosticos, qualidade e exportacao

Todas as seis familias aceitam `return_diagnostics=True`. O dicionario inclui
`result`, familia, metodo, unidades, mascara de invalidos e metadados JSON.
PWV/LST acrescentam `raw_result`, `screened_result` e flags. `quality_mode="screened"`
seleciona o filtrado; `"diagnostic"` seleciona o bruto. Os retornos padrao em
arrays e as equacoes sao preservados. Veja [contratos](docs/result-contracts.md)
e [diagnosticos](docs/diagnostic-quality.md).

`LandsatScene.write_geotiff` exporta mascaras como uint8 e flags como uint16,
com zero valido e sem nodata inteiro por padrao. Produtos incluem unidades e
versao; `metadata=` acrescenta a identificacao do processamento. Os resultados
de cena exportam as duas cadeias, flags e legenda JSON.

O [exemplo dedicado de quality_mask](exemple/quality_mask.ipynb) explica QA,
nodata, exclusao de agua e a exportacao da mascara.
