# Contratos de entrada e resultado

## Entradas

As funcoes numericas recebem matrizes reais alinhadas. Arrays complexos sao
rejeitados e valores ocultos em `numpy.ma.MaskedArray` tornam-se NaN.
Uma matriz nao transporta CRS: o chamador deve conferir a grade; os leitores
GeoTIFF fazem essa verificacao. Mascaras usam `True = invalido` e devem ter
a mesma forma; numeros e strings nao substituem parametros booleanos.

| Etapa | Grandeza esperada |
| --- | --- |
| Radiancia TOA | DN Level-1 + coeficientes da propria banda no MTL |
| Reflectancia TOA | DN optico Level-1 + MTL + elevacao solar em graus |
| BT | Radiancia termica em W m-2 sr-1 um-1; DN somente com input_quantity="dn" |
| Emissividade | Vermelho/NIR com convencao optica justificada, ou NDVI preparado |
| PWV | BT10/BT11 em K; saida em g/cm2 |
| LST | BT em K, emissividade em (0,1], PWV em g/cm2 quando aplicavel |

A API nao tenta adivinhar unidades pelos valores. Declare `optical_quantity`
quando aplicavel e mantenha a origem das emissividades prontas. Metadados MTL
da cena sao preferidos aos valores de fallback do sensor.

## Diagnosticos das seis familias

`return_diagnostics=True` retorna um dicionario em `calibrate`, `emissivity`,
`single_window`, `split_window`, `water_vapor` e `optical_correction`.
Sem essa opcao, os retornos numericos padrao continuam sendo arrays.

Campos comuns: `result`, `family`, `method`, `units`, `quality_mode`,
`invalid_mask` e `metadata`. `metadata` e serializavel em JSON e identifica
versao, parametros efetivos e convencoes declaradas. Matrizes de parametros
sao descritas por forma/tipo; os valores completos nao sao copiados para JSON.
As chaves especificas, como `lst`, `water_vapor` e `reflectance`, continuam
apontando para o mesmo resultado selecionado.

## Bruto, filtrado e selecionado

PWV/LST acrescentam `raw_result`, `screened_result`, `quality_flags` e a legenda.
Os aliases especificos sao `raw_water_vapor`/`screened_water_vapor` e
`raw_lst`/`screened_lst`. O bruto conserva estimativas matematicamente
calculaveis, com flags para condicoes operacionais. Nao cria valores para
entradas ausentes, mascaradas ou expressoes indefinidas.

- `quality_mode="screened"`: `result` seleciona o filtrado.
- `quality_mode="diagnostic"`: `result` seleciona o bruto e sempre retorna diagnosticos.

Calibracao, emissividade e correcao optica nao inventam um resultado bruto
fora dos contratos de entrada; seus diagnosticos descrevem o resultado obtido.
`quality_acceptable` e uma politica operacional, nao uma probabilidade de acuracia.
Um valor finito tambem pode carregar limitacoes de aplicabilidade.

## Cadeias e medias

O filtrado de uma funcao LST usa o mesmo PWV fornecido a essa chamada.
Uma cadeia completamente filtrada exige usar tambem o PWV filtrado e sua
propria agregacao espacial. `du_from_scene` conserva ambas as cadeias:
`lst`, `lst_raw`, `lst_screened`, `pwv`, `pwv_raw`, `pwv_screened`.
`pwv_raw` e o estimador antes dos filtros operacionais, em Wang e Ren.
Medias informam a quantidade de contribuintes, propagam OR das flags desses
contribuintes e acrescentam `SPATIAL_MEAN_PWV`.

## Erros, avisos e exportacao

Entradas incompat?veis geram excecoes com contexto da funcao e proxima acao.
As categorias de aviso, em `pylstemp.exceptions`, distinguem:
`ApplicabilityWarning`, `DomainWarning` e `UnusedParameterWarning`.
Todas herdam de RuntimeWarning.

`LandsatScene.write_geotiff` usa uint8 para bool, preserva inteiros suportados
e usa float32 para medidas de ponto flutuante por padrao. `dtype` explicito
permite outros tipos suportados; conversoes inteiras com perda sao rejeitadas.
Inteiros usam nodata=None por padrao: zero permanece um valor valido.
Floats usam NaN. O backend Pillow suporta uint8/uint16/int32/float32;
para float64 ou uint32, use Rasterio. `metadata` grava a identificacao do
processamento junto de unidades, produto e versao.

`DuSceneResult.export` grava resultados selecionados, brutos e filtrados,
mascaras uint8, flags uint16 e JSONs de proveniencia e legenda. A proveniencia
usa schema 2 e fichas em `source_method_cards[family][method]`.
