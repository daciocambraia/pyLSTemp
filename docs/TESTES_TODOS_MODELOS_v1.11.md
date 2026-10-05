# Testes de todos os modelos - pyLSTemp v1.11.0

Atualizacao de escopo em 05/10/2026: Xiaolei foi removido da versao atual. Este documento preserva os resultados da rodada anterior, que incluia o metodo. Os 204 casos sem SR nao fazem parte do catalogo atual. Consulte docs/ESCOPO_LEVEL1_v1.11.md e Verificacao/v1.11.0/escopo_level1_sem_xiaolei_2026-10-05/RELATORIO_ESCOPO.md.

Complemento da validacao anterior, realizado em 04/10/2026.

## Resultado

**96 testes aprovados**, incluindo 19 novos testes e subcasos para todos os modelos.
Cobertura combinada de instrucoes e ramificacoes: 89.46%.
As 14 entradas do catalogo foram cobertas por testes de software. NDVI aparece em duas familias, incluindo a API legada.
A familia radiative_transfer esta vazia; nao existe um algoritmo implementado para executar.

Os testes numericos usam valores de referencia independentes dos helpers do pacote.
Incluem Price e Sobrino com diferentes emissividades; Kerr nos extremos e na mistura;
Du em todos os intervalos de coeficientes; as quatro conversoes termicas Landsat 8/9;
Avdan nos limites de classes; Gopinadh e Xiaolei nas duas bandas; NDVI/EVI e NDVI legado;
Wang nos dois ramos de transmitancia. Mono-window e Jimenez mantem as regressoes independentes anteriores.
Tambem foram testados mascaras, valores nao finitos, superficies quentes e todas as combinacoes
suportadas de emissividade/LST. Avdan permanece bloqueado para split-window.

## Matriz de cobertura

| Familia | Modelo | Software | Imagens Landsat 8 e 9 |
|---|---|---|---|
| emissivity | avdan-2016 | Aprovado | cenas completas |
| emissivity | gopinadh-2018 | Aprovado | cenas completas |
| emissivity | xiaolei-2014 | Aprovado | nao executado nas cenas: falta refletancia de superficie |
| single_channel | mono-window-2016 | Aprovado | cenas completas |
| spectral_index | evi | Aprovado | cenas completas |
| spectral_index | ndvi | Aprovado | cenas completas |
| spectral_indices | ndvi | Aprovado | cenas completas |
| split_window | du-2015 | Aprovado | cenas completas |
| split_window | jimenez-munoz-2014 | Aprovado | tres recortes por cena, halo 10, grupos NDVI globais |
| split_window | kerr-1992 | Aprovado | cenas completas |
| split_window | price-1984 | Aprovado | cenas completas |
| split_window | sobrino-1993 | Aprovado | cenas completas |
| thermal | brightness | Aprovado | cenas completas |
| water_vapor | wang-2015 | Aprovado | tres recortes por cena, halo 10, grupos NDVI globais |

**Xiaolei foi executado com refletancia de superficie sintetica**, cobrindo solo, mistura, vegetacao
e os limites das classes nas duas bandas. Tambem participou dos testes sinteticos das combinacoes LST.
Nao foi executado como recuperacao cientifica nas cenas Level-1: a pasta Imagens nao contem SR_B*.
Refletancia TOA nao foi apresentada como refletancia de superficie.

## Resultados nas cenas completas

Todos os modelos que dispensam PWV e refletancia de superficie foram reexecutados nas cenas completas.
Price, Kerr e Sobrino foram incluidos nesta rodada. Os metodos mono-window, Du, NDVI e EVI
reproduziram a contagem de pixels e a media da rodada anterior, com tolerancia de 1e-9.

| Sensor | Modelo | Pixels validos | Media (C) | Minimo (C) | Maximo (C) |
|---|---|---:|---:|---:|---:|
| landsat_8 | mono_avdan_k | 39939067 | 33.588 | 12.636 | 48.401 |
| landsat_8 | mono_gopinadh_k | 39939067 | 32.971 | 13.904 | 47.927 |
| landsat_8 | du-2015_k | 39939067 | 37.970 | 12.525 | 68.553 |
| landsat_8 | price-1984_k | 39939067 | 38.878 | 3.883 | 68.180 |
| landsat_8 | kerr-1992_k | 39939067 | 36.828 | 9.703 | 62.048 |
| landsat_8 | sobrino-1993_k | 39939067 | 36.943 | 13.875 | 73.556 |
| landsat_9 | mono_avdan_k | 39632897 | 36.242 | 18.902 | 54.325 |
| landsat_9 | mono_gopinadh_k | 39632897 | 35.607 | 18.549 | 53.722 |
| landsat_9 | du-2015_k | 39632897 | 43.431 | 17.873 | 88.464 |
| landsat_9 | price-1984_k | 39632897 | 44.900 | 0.117 | 81.778 |
| landsat_9 | kerr-1992_k | 39632897 | 41.784 | 5.406 | 72.176 |
| landsat_9 | sobrino-1993_k | 39632897 | 43.075 | 18.452 | 111.312 |

## PWV e comparacoes espaciais

Wang e Jimenez foram reexecutados em tres recortes 256x256 por cena, com halo de 10 pixels
e limites de grupos NDVI da cena inteira. A mascara de extrapolacao TIGR3 foi aplicada
aos produtos desta rodada. Du tambem foi testado com a media de PWV do recorte quando
ela estava dentro de 0..6.3 g/cm2. Esse PWV vem de Wang, nao de uma referencia externa.
Os mapas com seis metodos usam a mesma escala de cores para permitir comparacao.

## Produtos e verificacoes

- 18 novos GeoTIFFs conferidos quanto a modo float32, escala espacial, projecao e NoData.
- Price/Kerr/Sobrino exportados comparados ao recalculo de recortes 64x64 em cada cena; tolerancia 2e-5.
- all_models_results.json: estatisticas completas, parametros, avisos e hashes dos insumos.
- model_test_matrix.json: matriz de cobertura por entrada do catalogo.
- software_validation.json e tests_and_coverage.txt: resultado da suite.
- geotiff_validation.json: verificacoes dos arquivos.
- Cada pasta de cena: results.json, tres mapas comparativos, rasters completos dos metodos historicos e PWV/Jimenez dos recortes.

## Limites cientificos

Passar nestes testes comprova execucao e consistencia com a parametrizacao adotada.
Nao comprova acuracia absoluta nem calibracao dos coeficientes para o sensor.
Price/Kerr/Sobrino permanecem adaptacoes AVHRR/Landsat sem validacao independente.
A transferencia dos coeficientes de recuperacao para Landsat 9 permanece experimental.
As cenas sao Level-1 TOA; faltam refletancia de superficie e referencia de campo para uma validacao cientifica completa.
Nenhuma diferenca entre metodos foi interpretada como RMSE contra uma verdade de campo.
Os arquivos das imagens e da v1.10 historica foram preservados. Nao houve push ou publicacao.

## Reproducao

python -m unittest discover -s tests -v

python scripts/validate_all_models.py --input ../Imagens --output Verificacao/nova_rodada_todos_modelos

O executor requer as dependencias de exemplos. A pasta de saida deve ser nova.
O backend Pillow foi usado nesta maquina, pois o Controle de Aplicativos bloqueou a DLL do rasterio.
