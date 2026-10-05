> Atualizacao posterior: EVI removido e fluxo padrao alterado para radiancia TOA. Este relatorio registra uma etapa anterior. Consulte [a verificacao atual](FLUXO_RADIANCIA_v1.11.md) para os contratos e resultados vigentes.

# Avaliacao profunda dos modulos - pyLSTemp v1.11.0

Atualizacao de escopo em 05/10/2026: Xiaolei foi removido da versao atual. Este documento preserva os resultados da rodada anterior, que incluia o metodo. Os 204 casos sem SR nao fazem parte do catalogo atual. Consulte docs/ESCOPO_LEVEL1_v1.11.md e Verificacao/v1.11.0/escopo_level1_sem_xiaolei_2026-10-05/RELATORIO_ESCOPO.md.

Data: 05/10/2026. Rodada nova; resultados anteriores preservados.

Foram reprocessadas as duas cenas completas e executada a matriz de combinacoes
em tres recortes por cena. Os algoritmos de producao nao foram modificados.
Os testes confirmam implementacao numerica e contratos da API; nao comprovam
acuracia contra temperatura ou PWV medidos em campo.

## Resultado da execucao

| Verificacao | Resultado |
|---|---:|
| Testes de software | 793 aprovados |
| Subtestes adicionais | 66 aprovados |
| Novos testes de software | 697 |
| Cobertura combinada de instrucoes e ramos | 91,65% |
| Cobertura de instrucoes | 93,95% |
| Cobertura de ramos | 81,67% |
| Pixels percorridos nas cenas completas | 116.381.412 |
| Recortes da matriz | 6 de 256x256, com halo de 10 pixels |
| Casos registrados na matriz real | 690 |
| Execucoes numericas aprovadas | 282 |
| Rejeicoes esperadas do contrato | 204 |
| Casos bloqueados pela falta de SR | 204 |
| Falhas inesperadas da matriz | 0 |
| GeoTIFFs novos verificados | 120 |
| Comparacoes independentes de PWV em pixels | 144 |

Nenhuma das 282 execucoes aprovadas produziu uma saida inteiramente NaN.
As 204 rejeicoes representam contratos existentes da API, nao falhas de teste.
Os 204 casos sem SR nao foram executados nas imagens. Seu software foi testado
com dados sinteticos de reflectancia de superficie.

## Possibilidade de usar Landsat 8 e 9

Landsat 8: LC08_L1TP_221071_20260919_20260925_02_T1, 7691x7571.
Landsat 9: LC09_L1TP_221071_20260927_20260927_02_T1, 7681x7571.

Ambas contem MTL, B2/B4/B5/B10/B11, QA_PIXEL, QA_RADSAT e SZA.
Os hashes dos insumos coincidiram com a rodada anterior. Foram usados
os coeficientes MTL de cada sensor, QA, valores NoData e a grade original.
A leitura utilizou Pillow porque a DLL rasterio permanece bloqueada nesta maquina.

As cenas sao Level-1. Nao foram encontradas bandas SR_B* ou ST_B*.
Reflectancia TOA foi calculada, mas nao foi convertida artificialmente em SR.
Produtos Level-2 empregam correcao atmosferica e insumos auxiliares;
apenas aplicar uma escala nao realiza essa correcao.
Fonte: [USGS Level-2](https://www.usgs.gov/landsat-missions/landsat-collection-2-level-2-science-products).

As datas de aquisicao sao diferentes; diferencas entre L8 e L9 nao representam
isoladamente erro de sensor. Os coeficientes de recuperacao transferidos para
Landsat 9 e as adaptacoes AVHRR permanecem sem validacao independente.

## Cobertura por modulo

| Modulo | Executado e verificado |
|---|---|
| spectral_index | NDVI e EVI nas cenas completas e recortes; equacoes independentes, mascaras, float32/float64 e API NDVI legada |
| brightness | Bandas 10 e 11, ambos os sensores; K1/K2/gain/bias MTL, defaults, overrides e quatro aliases por banda |
| emissivity | Avdan, Gopinadh e Xiaolei nas bandas 10 e 11; limites das classes e equacoes. Avdan/Gopinadh nas cenas; Xiaolei com SR sintetica |
| single_channel | 1 lst_method x 3 emissivity_method, Kelvin/Celsius, mascaras e tipos numericos. Avdan/Gopinadh nas duas cenas |
| split_window | 5 lst_method x 3 emissivity_method; sem PWV, media Wang e raster Wang; Kelvin/Celsius, mascaras e tipos numericos |
| water_vapor | Wang calculado pela API publica; janelas 3/5/21, grupos 1/3, blocos diferentes, grupos globais NDVI e halo |
| calibration e scene | Reflectancia TOA independente, grade, GeoTIFF float32, origem dos recortes, NoData e hashes |
| Demais modulos | API, validacao, excecoes, registro, descoberta, constantes e creditos abrangidos pela suite anterior e ampliada |

A familia radiative_transfer esta vazia. Nenhum algoritmo inexistente foi contado
como executado. O catalogo tem 14 entradas, incluindo NDVI na familia legada.

## Matriz LST x emissividade

| LST | Avdan | Gopinadh | Xiaolei |
|---|---|---|---|
| mono-window-2016 | Aceito | Aceito | Aceito com SR |
| du-2015 | Rejeitado pela API | Aceito | Aceito com SR |
| jimenez-munoz-2014 | Rejeitado pela API | Aceito com PWV | Aceito com SR e PWV |
| price-1984 | Rejeitado pela API | Aceito | Aceito com SR |
| kerr-1992 | Rejeitado pela API | Aceito | Aceito com SR |
| sobrino-1993 | Rejeitado pela API | Aceito | Aceito com SR |

As 18 combinacoes basicas foram exercitadas no software, incluindo rejeicoes.
A matriz sintetica soma 36 casos single-channel e 540 split-window quando se
cruzam unidades, PWV, mascaras e float32/float64.
Avdan retorna emissividade igual nas duas bandas por compatibilidade da API;
isso nao constitui uma estimativa espectral independente para banda 11.

## PWV calculado e efetivamente utilizado

O executor importa water_vapor de pylstemp e calcula Wang a partir de BT10,
BT11 e NDVI. Nenhum PWV externo foi apresentado como recuperacao Wang.

| Metodo split-window | Sem PWV | Media do Wang | Raster Wang |
|---|---|---|---|
| Du | Coeficientes gerais | Seleciona intervalos CWV | Rejeitado: API aceita escalar |
| Jimenez | Rejeitado | Utilizado | Utilizado por pixel |
| Price / Kerr / Sobrino | Aceito | Ignorado pelo algoritmo | Ignorado pelo algoritmo |

PWV bruto foi preservado. Para a recuperacao LST com Wang, valores fora
de 0,066..7,833 g/cm2 foram mascarados conforme o dominio TIGR3 previamente
documentado. A media por recorte foi declarada explicitamente; nao foi
apresentada como recuperacao Du por pixel. A media usada em Du estava no
intervalo 0..6,3 g/cm2. O dominio TIGR3 nao comprova validade externa de Jimenez.

PWV medio nos recortes: L8 = 2,927 / 3,216 / 3,364 g/cm2;
L9 = 3,185 / 3,370 / 3,750 g/cm2.
Foram encontrados 4/28/50 pixels extrapolados no L8 e 3/11/163 no L9.
Wang e as combinacoes que usam PWV foram executados em recortes,
nao sobre cada pixel das cenas completas.

## Combinacoes adicionais

Foram verificados invariancia numerica de chunk_rows, fronteira de 128 colunas,
halos, grupos NDVI globais, regressao escalar independente, temperaturas quentes,
entradas nao finitas, cenas sem pixels validos, nao alteracao dos arrays de
entrada, conversao Kelvin/Celsius, aliases, chaves maiusculas e formato legado.

Tambem foram testados parametros e metodos inexistentes, formas incompatíveis,
mascaras nao booleanas, PWV ausente, negativo, infinito, NaN e fora do dominio
Du, alem da igualdade entre PWV escalar e raster constante em Jimenez.

NDVI, EVI, calibracao e LST foram comparados a equacoes independentes dos helpers
de producao. As decisoes de coeficientes seguem scientific-methods.md;
a concordancia nao valida transferencia de coeficientes entre sensores.

## Diagnosticos e limites

Dois defeitos adicionais foram reproduzidos fora dos cenarios normais:

- NDVI de NIR=RED=0 retorna 0, embora a divisao 0/0 seja indefinida.
- EVI com banda azul infinita retorna -0, em vez de NaN.

Esses diagnosticos sao registrados como finding, nao como testes aprovados.
Indices escalares e o alias B10 maiusculo tambem nao sao suportados.
A avaliacao posterior prioriza essas melhorias em MELHORIAS_MODULOS_v1.11.md.

As estatisticas completas reproduziram a rodada anterior com tolerancia
1e-9 para medias. Sobrino atingiu 111,31 C no L9; coerencia com a formula nao
justifica interpretar esses valores como temperatura validada.
Nao foi imposto corte arbitrario de temperatura para esconder extremos.

## Artefatos e reproducao

Resultados locais: Verificacao/v1.11.0/matriz_profunda_2026-10-05/.

- combination_matrix.csv: todos os 690 casos e seus estados.
- module_coverage.csv e coverage.json: cobertura por arquivo.
- software_tests.txt e software_validation.json: suite.
- validation_summary.json: contagens e diagnosticos.
- matriz_real/module_matrix_results.json: equacoes, parametros, estatisticas e erros.
- geotiff_validation.json: 120 produtos verificados.
- source_snapshot_sha256.json: fontes usados.
- cenas_completas/: estatisticas completas, 18 GeoTIFFs e seis mapas.
- matriz_real/: 102 GeoTIFFs de combinacoes LST e PWV.

Executar a partir da raiz v1.11; usar pastas de saida novas:

~~~powershell
python -m pytest
python scripts/validate_all_models.py --input ../Imagens --output Verificacao/nova_matriz/cenas_completas
python scripts/validate_module_matrix.py --input ../Imagens --full-summary Verificacao/nova_matriz/cenas_completas/all_models_results.json --output Verificacao/nova_matriz/matriz_real
python scripts/validate_matrix_products.py --input ../Imagens --results Verificacao/nova_matriz
~~~

A execucao local foi feita em Python 3.14. A sintaxe dos novos fontes foi
verificada para Python 3.9, mas os testes nessa versao dependem da CI.
Nao houve envio ao GitHub nem alteracao dos arquivos das imagens.
