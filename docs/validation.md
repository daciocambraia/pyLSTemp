# Validacao atual - v1.11.0

## Escopo

O catalogo tem 12 algoritmos, incluindo Jimenez-Munoz single-channel e
split-window com nomes distintos. NDVI e o unico indice; emissividade usa
Avdan e Gopinadh. O fluxo padrao usa radiancia TOA, BT em K e QA.
TOA reflectance e uma alternativa explicita; EVI, Xiaolei e reflectance()
nao fazem parte do escopo atual.

## Novo Jimenez single-channel

Foram conferidas visualmente as Eqs. 1, 2, 4 e 6 no artigo original.
O metodo usa radiancia/BT da B10, emissividade e PWV. A restricao operacional
[0,3] g/cm2 decorre da perda de precisao do ajuste polinomial acima de 3
relatada pelo artigo. Escalares invalidos geram erro; pixels raster fora do
intervalo ou invalidos produzem NaN. A restricao nao garante acuracia.

A nova matriz em recortes centrais das duas cenas registrou 24 casos aprovados
(duas emissividades, duas unidades e tres modos de PWV) e 16 rejeicoes
esperadas, sem falhas inesperadas. Os 24 GeoTIFFs foram conferidos.
PWV escalar de 1/2 g/cm2 foi usado como entrada controlada, nao como observacao
meteorologica. O terceiro modo utilizou o raster calculado por Wang.
Resultados comparados com uma referencia algebrica independente, tolerancia
absoluta 2e-10 K. Landsat 9 continua sendo transferencia experimental.

## Software e exemplos

Passaram 716 testes e 108 subtestes; cobertura de linhas: 94.03%.
README, guia, script e seis notebooks foram executados nas duas cenas reais:
18 execucoes e 68 exportacoes GeoTIFF verificadas, sem falhas inesperadas.
As verificacoes incluem tipo float32, NoData NaN, coordenadas, unidades e
pixels finitos. O script oferece dez produtos; o guia inclui reflectancia
opcional. Nao ha bandas sinteticas nem imports NumPy nos exemplos de uso.

Evidencias da rodada:
`Verificacao/v1.11.0/jimenez_single_documentacao_2026-10-05/`.

## Evidencia anterior dos modelos existentes

A rodada em radiancia anterior percorreu 116.381.412 pixels nas duas cenas.
Metodos sem PWV foram executados nas cenas completas; Wang e Jimenez SW
foram avaliados em tres recortes por cena, com halo e extremos globais de NDVI.
A matriz anterior, com 11 algoritmos, registrou 498 casos: 294 aprovados e
204 rejeicoes esperadas, sem falhas inesperadas. Foram conferidos 120 GeoTIFFs.
Essa matriz foi preservada; nao foi reexecutada integralmente nesta adicao.

| Cena | NDVI medio em radiancia | NDVI medio em reflectancia TOA |
|---|---:|---:|
| Landsat 8 | 0.179375 | 0.394940 |
| Landsat 9 | 0.184130 | 0.398547 |

![NDVI nas duas convencoes](comparacao_ndvi_v1.11.png)

Nao ha observacoes independentes de LST/PWV para medir acuracia. Os limiares
de emissividade, transferencia de sensores e adaptacoes AVHRR requerem
avaliacao cientifica propria. Veja [contratos cientificos](scientific-methods.md).

## Historico local

Relatorios, hashes e resultados unicos ficam em Verificacao/v1.11.0/.
Copias antigas da documentacao ficam em arquivo_documentacao/.
A limpeza anterior consolidou arquivos identicos por SHA-256;
limpeza_exemplos_2026-10-05/limpeza_manifest.json mapeia as copias preservadas.
