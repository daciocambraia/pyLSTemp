# Arquitetura

A biblioteca tem 12 algoritmos registrados, separados por familia. Calibracao,
leitura de cenas e workflows sao funcoes auxiliares, sem duplicar o catalogo.

| Pasta | Conteudo | Distribuicao |
|---|---|---|
| `pylstemp/` | API, calibracao, cenas, workflows e algoritmos | Git, wheel e sdist |
| `docs/` | Uso, API, contratos cientificos e referencias | Git e sdist |
| `exemples/` | Notebooks e script de uso com imagens | Git e sdist |
| `.github/` | CI, publicacao e templates de contribuicao | Git |
| `Verificacao/` | Testes, verificadores, dados e relatorios locais | Fora do Git e dos pacotes |

## Estrutura publica

```text
.gitattributes
.github/
  ISSUE_TEMPLATE/
    bug_report.md
    feature_request.md
  pull_request_template.md
  workflows/
    ci.yml
    publish.yml
.gitignore
CHANGELOG.md
CODE_OF_CONDUCT.md
CONTRIBUTING.md
CREDITS.md
LICENSE
MANIFEST.in
README.md
docs/
  api-reference.md
  architecture.md
  du-pwv-workflow.md
  extending.md
  index.md
  installation.md
  references.md
  scientific-methods.md
  usage.md
  validation.md
exemples/
  DATA.md
  brightness.ipynb
  emissivity.ipynb
  fluxo_completo.py
  single_window.ipynb
  spectral_index.ipynb
  split_window.ipynb
  water_vapor.ipynb
pylstemp/
  __init__.py
  algorithms/
    __init__.py
    base_temperature.py
    emissivity/
      __init__.py
      avdan_2016.py
      base.py
      gopinadh_2018.py
    radiative_transfer/
      __init__.py
    single_channel/
      __init__.py
      base.py
      jimenez_munoz_2014.py
      mono_window_2016.py
    spectral_index/
      __init__.py
      ndvi.py
    spectral_indices/
      __init__.py
      ndvi.py
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
      wang_2015.py
  api.py
  calibration.py
  exceptions.py
  messages.py
  metadata.py
  references.py
  registry.py
  requirements.py
  scene.py
  sensors/
    __init__.py
    landsat.py
  utils.py
  validation.py
  workflows.py
pyproject.toml
```

## Responsabilidades

`api.py` expoe as funcoes publicas. `calibration.py` converte DN usando o MTL
da cena. `scene.py` le bandas alinhadas, aplica QA e exporta GeoTIFFs.
`workflows.py` conecta essas etapas para Du com modos PWV explicitos.

Cada algoritmo declara `ALGORITHM_SPEC`; o registro descobre os modulos por
familia e alimenta `list_algorithms()`. A pasta `spectral_indices` preserva
compatibilidade de imports com o mesmo NDVI, sem duplicar o catalogo.
`radiative_transfer` reserva a familia RTE, ainda sem algoritmo implementado.
Esses modulos fazem parte dos contratos da biblioteca.

A CI publica verifica instalacao, importacao e empacotamento. A suite cientifica
completa e os verificadores de cenas sao executados no ambiente local.

Veja [API](api-reference.md), [extensao](extending.md),
[workflow Du/PWV](du-pwv-workflow.md) e [estado da validacao](validation.md).
