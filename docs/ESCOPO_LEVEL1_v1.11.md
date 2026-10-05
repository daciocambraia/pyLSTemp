> Atualizacao posterior: EVI removido e fluxo padrao alterado para radiancia TOA. Este relatorio registra uma etapa anterior. Consulte [a verificacao atual](FLUXO_RADIANCIA_v1.11.md) para os contratos e resultados vigentes.

# Escopo Level-1 e retirada de Xiaolei - v1.11.0

Data: 05/10/2026. Alteracao de escopo solicitada pelo usuario.

## Resultado

Xiaolei (xiaolei-2014) foi removido da implementacao, dos imports e da
descoberta automatica. O catalogo tem 12 algoritmos, com uma unica entrada NDVI.
Os metodos de emissividade disponiveis sao avdan-2016 e gopinadh-2018.

A decisao reduz a necessidade de insumos externos: nenhum metodo de recuperacao
atualmente disponivel exige uma banda SR adicional. A retirada nao estabelece
que o metodo Xiaolei esteja incorreto; sua exigencia de reflectancia de superficie
fica fora do escopo selecionado para esta versao.

| Fluxo | Emissividade disponivel |
|---|---|
| Emissividade isolada B10/B11 | Avdan e Gopinadh |
| Single-channel B10 | Avdan e Gopinadh |
| Split-window B10/B11 | Gopinadh |

A restricao Avdan/split-window continua, conforme a parametrizacao cientifica
ja documentada. Os cinco metodos LST split-window continuam disponiveis, assim
como mono-window, Wang, brightness B10/B11 e NDVI/EVI.

## Compatibilidade e mensagens

Selecionar emissivity_method="xiaolei-2014" gera InvalidMethodRequested com
os metodos disponiveis. Nao ocorre substituicao silenciosa por outro metodo.
O import direto do modulo removido deixa de existir.

band_4_red na API de emissividade isolada foi preservado como argumento
opcional por compatibilidade. Avdan/Gopinadh calculam emissividade a partir de
NDVI e nao precisam desse argumento. Nos fluxos LST, red/nir continuam
necessarios para o NDVI calculado internamente.

## Calibracao e NDVI

reflectance(), toa_reflectance() e surface_reflectance() continuam como
utilitarios de calibracao. A escala SR segue opcional; os exemplos usam TOA
calculada a partir de DN e MTL Level-1. Nao foi adicionada correcao atmosferica.

Mensagens e documentacao do NDVI foram corrigidas: aceita radiancia calibrada
ou reflectancia, com a grandeza de entrada registrada. Um fator multiplicativo
comum cancela; ganhos diferentes por banda e offsets geralmente alteram o
resultado. A compatibilidade com limiares de emissividade precisa ser avaliada
para a grandeza usada. EVI continua exigindo reflectancia fisica por causa de
sua constante aditiva.

Referencia original: [Rouse et al., NASA](https://ntrs.nasa.gov/citations/19740022614).
Os testes reais continuam usando a calibracao TOA existente; as equacoes e
resultados numericos dos metodos mantidos nao foram alterados nesta rodada.

## Verificacao executada

- 619 testes e 106 subtestes aprovados; um aviso cientifico previsto de Price.
- Cobertura conjunta: 91.89%; linhas: 93.92%; ramos: 83.92%.
- Matriz real nas duas cenas Landsat 8/9: tres ROIs 256x256 por cena, com halo.
- 486 casos: 282 aprovados e 204 rejeicoes previstas, sem falha inesperada.
- Nenhum caso bloqueado por falta de SR no catalogo atual.
- 144 amostras PWV comparadas a referencias numericas independentes.
- 102 GeoTIFFs verificados numericamente/geometricamente e por SHA256.
- Produtos identicos aos da rodada anterior para os metodos mantidos.
- Estatisticas, status e referencias dos 486 casos mantidos identicos aos
  anteriores; as mensagens das 204 rejeicoes foram atualizadas.
- Regressoes especificas verificam catalogo, retirada do modulo, rejeicao nas
  APIs, emissividade sem banda vermelha e NDVI com radiancia/escala comum.

A quantidade de testes mudou pela retirada das combinacoes e regressoes de
Xiaolei. Os testes dos metodos mantidos e a verificacao de suas rejeicoes continuam.
As cenas completas nao foram reprocessadas nesta rodada, pois suas equacoes
nao mudaram. Os resultados completos anteriores foram preservados; a matriz
real foi repetida e confirmou igualdade dos produtos mantidos.

## Relatorios e publicacao

Artefatos locais em:
Verificacao/v1.11.0/escopo_level1_sem_xiaolei_2026-10-05/

- RELATORIO_ESCOPO.md: copia deste documento.
- software_tests.txt, software_validation.json e coverage.json.
- matriz_real/module_matrix_results.json e GeoTIFFs por sensor/ROI.
- geotiff_validation.json e validation_summary.json.
- catalog.json, source_sha256.json, build_validation.json e release_preparation.json.

Os relatorios anteriores receberam uma nota de escopo e conservam seus dados
historicos. A implementacao anterior continua acessivel no historico Git e os
artigos originais foram preservados. Os pacotes wheel/sdist sao atualizados e
verificados para nao incluir o modulo Xiaolei.

Os testes demonstram consistencia de software; acuracia LST/PWV contra dados
independentes e transferencia dos coeficientes para Landsat 9 continuam
pendentes de validacao cientifica. Nenhum push/publicacao foi realizado.
