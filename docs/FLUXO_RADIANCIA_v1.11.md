> Atualizacao posterior: o dispatcher generico `reflectance()` foi removido; utilize `toa_reflectance()` diretamente. As estatisticas de imagens abaixo registram a rodada em radiancia e continuam aplicaveis, pois suas equacoes foram preservadas. Veja [a verificacao da simplificacao](REMOCAO_REFLECTANCE_v1.11.md).

# Fluxo em radiancia TOA e remocao do EVI - v1.11.0

Data: 2026-10-05. Projeto: `D:\Codex\pyLSTemp\v1.11`.

O EVI foi retirado da implementacao, descoberta, imports, catalogo, exemplos e referencias ativas. O NDVI permanece como unico indice espectral e alimenta emissividade e agrupamento do vapor d'agua. As equacoes dos metodos de emissividade e LST foram preservadas.

## Conversoes e fluxo padrao

| Funcao/etapa | Entrada | Saida |
|---|---|---|
| `toa_radiance` | DN Level-1 e coeficientes por banda do MTL | Radiancia TOA, W m-2 sr-1 um-1 |
| `toa_reflectance` | DN optico Level-1, MTL e elevacao solar | Reflectancia TOA adimensional |
| `brightness` | Radiancia TOA termal e K1/K2 do MTL | Temperatura de brilho TOA, K |
| `spectral_index("ndvi")` | B5/B4 em radiancia no fluxo padrao | NDVI adimensional |
| `emissivity` | NDVI | Emissividade adimensional |
| `water_vapor` | BT10/BT11 em K e NDVI | PWV, g/cm2 |
| `single_window` / `split_window` | BT em K, B4/B5 calibradas e parametros do metodo | LST em K ou graus C |

O modulo `calibration` concentra a calibracao; `brightness` continua disponivel no pacote e em `api`, apontando para a mesma funcao. A inversao de Planck e unica, compartilhada com os auxiliares termicos legados. `toa_radiance` aceita bandas 1..11 com coeficientes do MTL; TOA reflectance aceita bandas opticas 1..9.

`brightness` corresponde a Top of Atmosphere Brightness Temperature do USGS: `BT=K2/ln(1+K1/L)`. Esta grandeza nao e LST e nao inclui correcao de emissividade ou atmosfera. Radiancia: `L=M_L*DN+A_L`. Reflectancia: `rho=(M_rho*DN+A_rho)/sin(elevacao solar)`.

Fonte: [USGS Landsat Level-1](https://www.usgs.gov/landsat-missions/using-usgs-landsat-level-1-data-product).

## Migracao de chamadas

`brightness` agora recebe radiancia por padrao. Chamadas com DN devem indicar `input_quantity="dn"`. Ganho/offset sao rejeitados com radiancia para evitar dupla calibracao. Com MTL fornecido, os coeficientes do MTL sao autoritativos; sensores conflitantes sao rejeitados. Os auxiliares internos `brightness_band_10/11` conservam a convencao DN por compatibilidade, documentada.

`LandsatScene.calibrated()` usa radiancia optica por padrao. Para reflectancia TOA selecione `optical_quantity="reflectance"`. Sao necessarios B4/B5/B10/B11, MTL e QA; B2 e opcional. QA conserva a politica anterior de saturacao B2/B4/B5 e oclusao de terreno. A validade do SZA fornecido e aplicada em ambos os modos para comparacoes controladas; o angulo solar nao reescala radiancia.

DN <= 0, entradas nao finitas e mask=True propagam NaN. BT exige radiancia positiva. Radiancia optica e reflectancia nao sao silenciosamente recortadas. SR Level-2 permanece somente como auxiliar explicito de escala; nao e exigido por nenhum metodo disponivel.

## Verificacao executada

- Software: 621 testes e 105 subtestes aprovados. Cobertura combinada: 90.94%.
- Catalogo: 11 algoritmos; spectral_index contem apenas ndvi. Ausencia do modulo EVI e rejeicao de sua chave foram verificadas.
- Duas cenas completas: 116,381,412 pixels de entrada percorridos, inclusive pixels invalidos mascarados.
- Todos os LST sem PWV, emissividades e BT foram executados nas duas cenas completas. Wang/PWV e Jimenez foram executados em tres recortes 256x256 por cena, com halo de 10 pixels e extremos de NDVI calculados na cena inteira.
- Matriz: 498 casos; 294 aprovados, 204 rejeicoes esperadas e nenhum erro inesperado.
- Maior erro das comparacoes numericas registradas: 3.411e-13; valores comparados em precisao float64 antes da exportacao.
- PWV: janelas 3/5/21, grupos 1/3, valores escalares e raster; 144 amostras independentes de regressao local. Equivalencia de chunk_rows tambem conferida.
- Produtos: 120 GeoTIFFs aprovados, com tolerancia float32 de 2e-5, NoData, projecao, resolucao e origem dos recortes conferidos.
- Notebooks: seis exemplos executados em ambas as cenas, 12 execucoes aprovadas; dados reais carregados uma vez por cena e reutilizados entre exemplos.
- Hashes dos arquivos de entrada iguais aos da rodada anterior: imagens e MTL nao foram modificados.
- Sintaxe de 61 arquivos verificada para Python 3.9. Execucao local em Python 3.14; os demais ambientes ficam para a matriz CI. Pillow foi usado por restricao local de carregamento do DLL do rasterio.
- O aviso de Price sobre adaptacao AVHRR e esperado, nao uma falha de teste.

| Modulo | Casos reais |
|---|---:|
| spectral_index | 6 |
| brightness | 24 |
| water_vapor | 36 |
| emissivity | 24 |
| single_channel | 24 |
| split_window | 360 |
| calibration | 24 |

## Comparacao do NDVI nas mesmas cenas

Esta e uma comparacao controlada de grandezas: mesmos DN, mascara QA e formula exata de NDVI. Ganhos e offsets por banda nao cancelam em geral. Os valores nao devem ser tratados como equivalentes.

| Cena | NDVI medio, radiancia | NDVI medio, reflectancia | Diferenca media | Pixels validos |
|---|---:|---:|---:|---:|
| landsat_8 | 0.179375 | 0.394940 | -0.215566 | 39,939,067 |
| landsat_9 | 0.184130 | 0.398547 | -0.214417 | 39,632,897 |

![Comparacao do NDVI](comparacao_ndvi_v1.11.png)

## Temperaturas operacionais, sem validacao independente

| Cena | Mono Avdan: media (C) | Du: media (C) | Sobrino: maximo (C) |
|---|---:|---:|---:|
| landsat_8 | 33.539 | 38.351 | 73.926 |
| landsat_9 | 36.192 | 43.807 | 111.312 |

## Interpretacao cientifica e proxima melhoria

A calibracao corresponde as equacoes USGS e os modelos conferem numericamente com referencias independentes. Isso verifica a implementacao, nao a acuracia de temperatura ou PWV em campo.

A troca para radiancia altera NDVI, classes de emissividade e LST. Os limiares publicados de NDVI nao foram reajustados automaticamente. Antes de uma aplicacao cientifica, e necessario justificar que esses limiares e coeficientes sao adequados a convencao radiometrica escolhida, ou avaliar explicitamente o fluxo em reflectancia. Recomenda-se comparar emissividade/LST com observacoes independentes e documentar essa escolha nos produtos.

Landsat 9 usa transferencia experimental dos coeficientes de recuperacao Landsat 8; a calibracao radiometrica e especifica de seu MTL. Price/Kerr/Sobrino seguem adaptacoes historicas de AVHRR sem validacao de acuracia para Landsat. O maximo de Sobrino/Landsat 9 permanece acima de 100 C: foi preservado e reportado, sem corte arbitrario.

Wang gera PWV bruto e uma versao com dominio de referencia 0.066..7.833 g/cm2. Esse filtro identifica extrapolacao; nao substitui validacao atmosferica. Du rejeita raster PWV e Avdan e rejeitado para split-window conforme seu escopo.

## Arquivos para conferencia

- `software_tests.txt`, `software_validation.json`, `coverage.json`: resultados do software.
- `cenas_completas/all_models_results.json`: estatisticas completas, comparacao NDVI, metadados e hashes.
- `matriz_real/module_matrix_results.json`: cada combinacao, parametros, rejeicoes e erros numericos.
- `geotiff_validation.json`: conferencia dos 120 produtos e diferencas com a linha de base historica.
- `notebook_validation.json`: execucoes dos exemplos com ambas as cenas.
- `build_validation.json` e `release_preparation.json`: conferencias da distribuicao e estado de preparacao.
- Relatorios anteriores sao historicos; nao representam o catalogo e o fluxo padrao atuais.
