# Arquitetura

O catalogo apresenta 17 seletores por familia, incluindo Sobrino e Chavez. Calibracao,
leitura de cenas e workflows sao funcoes auxiliares, sem duplicar o catalogo.

| Pasta | Conteudo | Distribuicao |
|---|---|---|
| `pylstemp/` | API, calibracao, cenas, workflows e algoritmos | Git, wheel e sdist |
| `docs/` | Uso, API, contratos cientificos e referencias | Git e sdist |
| `exemple/` | Um notebook por metodo e um indice de entradas/uso | Git e sdist |
| `.github/` | CI, publicacao e templates de contribuicao | Git |
| `tests/` | Regressao essencial sintetica e independente | Git e sdist; CI contra o wheel |
| `Verificacao/` | Testes, verificadores, dados e relatorios locais | Fora do Git e dos pacotes |

## Estrutura publica

Mapa completo dos arquivos publicos presentes em `v1.11/`. Ambiente virtual,
caches, builds e dados/testes locais nao fazem parte desta distribuicao.

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
    avdan_2016_emissivity.ipynb
    avdan_2016_lst.ipynb
    brightness.ipynb
    chavez_cost.ipynb
    chavez_dos.ipynb
    du_2015.ipynb
    gopinadh_2018.ipynb
    jimenez_munoz_2014_sc.ipynb
    jimenez_munoz_2014_sw.ipynb
    kerr_1992.ipynb
    price_1984.ipynb
    README.md
    ren_2015.ipynb
    rozenstein_2014.ipynb
    sobrino_1993.ipynb
    sobrino_2004_tm6.ipynb
    sobrino_2008.ipynb
    wang_2015.ipynb
  pylstemp/
    algorithms/
      emissivity/
        __init__.py
        avdan_2016.py
        base.py
        gopinadh_2018.py
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

## Responsabilidades

`api.py` expoe as funcoes publicas. `calibration.py` converte DN usando o MTL
da cena. `scene.py` le bandas alinhadas, aplica QA e exporta GeoTIFFs.
`workflows.py` conecta essas etapas para Du com modos PWV explicitos e estimadores Wang/Ren.

Cada algoritmo declara `ALGORITHM_SPEC`; o registro descobre os modulos por
familia e alimenta `list_algorithms()`, complementado pelos seletores Sobrino/Chavez
com metadados das mesmas fichas cientificas. NDVI e um calculo interno compartilhado
em `utils.py`, sem dispatcher publico, familia ou entrada no catalogo.
Esses modulos fazem parte dos contratos da biblioteca.

A CI publica verifica instalacao, importacao, empacotamento e regressao cientifica
essencial contra o wheel instalado. A suite completa e os verificadores de cenas
sao executados no ambiente local. `provenance.py` registra a execucao e os
contratos de `method_cards.json`, sem expor uma nova funcao publica para NDVI.

Veja [API](api-reference.md), [extensao](extending.md),
[workflow Du/PWV](du-pwv-workflow.md) e [estado da validacao](validation.md).

`emissivity_models.py` implementa internamente Sobrino 2004/2008 sem atribuir constantes
espectrais nao verificadas a TIRS. `optical.py` separa ajuste de haze e
aplicacao DOS/COST, permitindo reutilizar parametros entre blocos.
