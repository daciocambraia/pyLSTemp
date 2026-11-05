# Arquitetura

## Estrutura da distribuicao

| Caminho | Responsabilidade |
| --- | --- |
| `pylstemp/api.py` | Familias numericas de emissividade, PWV e LST; catalogo |
| `pylstemp/calibration/` | Conversoes radiometricas, leitura MTL e dispatcher calibrate |
| `pylstemp/algorithms/` | Uma implementacao por metodo, organizada por familia |
| `pylstemp/optical.py` | Ajuste de parametros e aplicacao DOS/COST |
| `pylstemp/inputs.py` | Leitura de arquivos QA e verificacao da grade |
| `pylstemp/scene.py` | Leitura de cenas, QA, calibracao e GeoTIFF |
| `pylstemp/workflows.py` | Composicao Du/Rongali com Wang/Ren e exportacao |
| `pylstemp/diagnostics.py` | Identidade de processamento e aliases dos resultados |
| `pylstemp/quality.py` | Flags, legenda e propagacao de qualidade |
| `pylstemp/validation.py` | Contratos de matrizes, mascaras, unidades e booleanos |
| `pylstemp/messages.py` | Contexto de erros e orientacoes de correcao |
| `pylstemp/provenance.py` | Identificacao de fontes, coeficientes e arquivos |
| `pylstemp/method_cards.json` | 16 fichas identificadas por familia + metodo |
| `pylstemp/sensors/` | Constantes de fallback explicitamente identificadas |
| `tests/` | Referencias numericas e integracao sintetica, sem dados privados |
| `exemple/` | 17 notebooks executaveis e indice de uso |
| `docs/` | Documentacao vigente, contratos, referencias e migracao |
| `.github/` | CI, publicacao e modelos de contribuicao |

Cada algoritmo declara ALGORITHM_SPEC. O registro descobre os modulos por
familia e alimenta list_algorithms; as correcoes opticas usam as mesmas fichas.
O NDVI e compartilhado internamente, sem familia publica propria.
`read_mtl` e `quality_mask` sao funcoes de apoio, sem seletor method.

Versao e identificacao de resultados devem acompanhar a API. A CI executa o
wheel instalado; os notebooks usam apenas fixtures sinteticas nos testes.
Ambientes virtuais, caches, builds e pacotes gerados nao integram a arvore de
fontes distribuida. Dados e materiais de pesquisas especificas permanecem
fora da biblioteca.

Veja [API](api-reference.md), [contratos](result-contracts.md),
[extensao](extending.md) e [verificacao](validation.md).
