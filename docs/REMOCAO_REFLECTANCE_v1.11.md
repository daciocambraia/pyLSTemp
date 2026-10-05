# Remocao de reflectance() - v1.11.0

Data: 2026-10-05.

No escopo Level-1, reflectance(kind="toa") apenas chamava toa_reflectance().
O dispatcher tambem selecionava escala de SR Level-2, que nenhum modelo atual
utiliza. Sua funcao, exportacao publica, mensagem de help e exemplos de API foram
removidos. A conversao direta toa_reflectance() permanece disponivel no pacote
e em calibration. O auxiliar interno surface_reflectance() foi preservado para
escala explicita de produtos SR existentes; nao realiza correcao atmosferica.

Migracao:

```python
from pylstemp import toa_reflectance, read_mtl
red_toa = toa_reflectance(red_dn, metadata=read_mtl("SCENE_MTL.txt"), band=4)
```

## Conferencias

- 619 testes e 105 subtestes aprovados. Dois testes de validacao exclusiva do
  dispatcher removido foram retirados; os testes numericos de TOA/SR foram mantidos.
- Ausencia de reflectance em pylstemp, calibration e __all__ conferida.
- Funcao publica toa_reflectance continua apontando para a implementacao canonica.
- Comparacao AST com o commit b2ed1b4 confirma que todas as funcoes de calibracao
  retidas estao inalteradas. Emissividade, NDVI, BT, PWV e LST tambem nao mudaram.
- Catalogo permanece com 11 algoritmos e apenas NDVI na familia de indices.
- As imagens nao foram reprocessadas nesta rodada: os resultados Landsat 8/9,
  498 casos e 120 GeoTIFFs da rodada em radiancia continuam sendo a evidencia
  numerica anterior. A simplificacao remove uma entrada que esses fluxos nao usam.
- Wheel/sdist reconstruidos e conferidos quanto a ausencia do dispatcher e a
  identidade de seu codigo com o projeto; detalhes em build_validation.json.

Verificacao anterior: [fluxo em radiancia](FLUXO_RADIANCIA_v1.11.md).

Arquivos locais: software_tests.txt, software_validation.json, coverage.json,
retained_equations_validation.json, build_validation.json e release_preparation.json.
