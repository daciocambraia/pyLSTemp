# Arquitetura

A biblioteca tem 13 algoritmos registrados, separados por familia. Calibracao,
leitura de cenas e workflows sao funcoes auxiliares, sem duplicar o catalogo.

| Pasta | Conteudo | Distribuicao |
|---|---|---|
| `pylstemp/` | API, calibracao, cenas, workflows e algoritmos | Git, wheel e sdist |
| `docs/` | Uso, API, contratos cientificos e referencias | Git e sdist |
| `exemples/` | Notebooks e script de uso com imagens | Git e sdist |
| `.github/` | CI, publicacao e templates de contribuicao | Git |
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

## Responsabilidades

`api.py` expoe as funcoes publicas. `calibration.py` converte DN usando o MTL
da cena. `scene.py` le bandas alinhadas, aplica QA e exporta GeoTIFFs.
`workflows.py` conecta essas etapas para Du com modos PWV explicitos e estimadores Wang/Ren.

Cada algoritmo declara `ALGORITHM_SPEC`; o registro descobre os modulos por
familia e alimenta `list_algorithms()`. NDVI e um calculo interno compartilhado
em `utils.py`, sem dispatcher publico, familia ou entrada no catalogo.
`radiative_transfer` reserva a familia RTE, ainda sem algoritmo implementado.
Esses modulos fazem parte dos contratos da biblioteca.

A CI publica verifica instalacao, importacao e empacotamento. A suite cientifica
completa e os verificadores de cenas sao executados no ambiente local.

Veja [API](api-reference.md), [extensao](extending.md),
[workflow Du/PWV](du-pwv-workflow.md) e [estado da validacao](validation.md).

`emissivity_models.py` expoe Sobrino 2004/2008 sem atribuir constantes
espectrais nao verificadas a TIRS. `optical.py` separa ajuste de haze e
aplicacao DOS/COST, permitindo reutilizar parametros entre blocos.
