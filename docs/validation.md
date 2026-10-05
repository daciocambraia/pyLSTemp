# Validacao atual - v1.11.0

## Escopo

O catalogo tem 11 algoritmos. NDVI e o unico indice; emissividade utiliza
Avdan e Gopinadh. O fluxo padrao usa radiancia TOA, BT em K e QA do produto.
EVI, Xiaolei e reflectance() foram removidos. toa_reflectance() e a conversao
explicita de reflectancia TOA. As equacoes retidas foram preservadas na limpeza.

## Cenas e modelos

A rodada em radiancia percorreu 116.381.412 pixels nas duas cenas Landsat 8/9.
Os metodos sem PWV foram executados nas cenas completas; Wang e Jimenez foram
avaliados em tres recortes 256 x 256 por cena, com halo e extremos globais de NDVI.
A matriz registrou 498 casos: 294 aprovados e 204 rejeicoes esperadas, sem
falha inesperada. Foram conferidos 120 GeoTIFFs e a integridade dos dados originais.

| Cena | NDVI medio em radiancia | NDVI medio em reflectancia TOA |
|---|---:|---:|
| Landsat 8 | 0.179375 | 0.394940 |
| Landsat 9 | 0.184130 | 0.398547 |

![NDVI nas duas convencoes](comparacao_ndvi_v1.11.png)

Os dados de campo necessarios para validacao independente de acuracia nao
estao disponiveis. A convencao radiometrica e seus limiares de emissividade
precisam de justificativa. Landsat 9 e as adaptacoes AVHRR mantem os limites
experimentais descritos em [scientific-methods.md](scientific-methods.md).

## Software e exemplos

Na verificacao atual passaram 620 testes e 99 subtestes, com 93.83% de cobertura de linhas.
O README, o script e os seis notebooks foram executados em ambas as cenas reais:
16 execucoes e 38 exportacoes GeoTIFF conferidas, com unidades e coordenadas.
A verificacao dos novos exemplos e a limpeza local sao registradas em
`Verificacao/v1.11.0/limpeza_exemplos_2026-10-05/`.
Os exemplos utilizam GeoTIFFs e MTL reais; as matrizes sinteticas ficam restritas
aos testes numericos da biblioteca. O fluxo de imagens foi preservado.

## Historico local

Relatorios, estatisticas, hashes e resultados unicos ficam em
`Verificacao/v1.11.0/`. Copias antigas da documentacao ficam em
`arquivo_documentacao/`. Arquivos de resultados identicos foram consolidados
por SHA-256; `limpeza_exemplos_2026-10-05/limpeza_manifest.json` informa onde
esta cada copia preservada. Consultas a um produto antigo podem usar esse indice.

A limpeza nao reprocessa as cenas antigas. A nova verificacao exercita os
exemplos atualizados; nao repete a matriz inteira de modelos inalterados.
