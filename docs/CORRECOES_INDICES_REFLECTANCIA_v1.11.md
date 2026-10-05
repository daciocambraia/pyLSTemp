> Atualizacao posterior: EVI removido e fluxo padrao alterado para radiancia TOA. Este relatorio registra uma etapa anterior. Consulte [a verificacao atual](FLUXO_RADIANCIA_v1.11.md) para os contratos e resultados vigentes.

# Correcoes de indices, NDVI unico, reflectancia e mensagens

Atualizacao de escopo em 05/10/2026: Xiaolei foi removido da versao atual. Este documento preserva os resultados da rodada anterior, que incluia o metodo. Os 204 casos sem SR nao fazem parte do catalogo atual. Consulte docs/ESCOPO_LEVEL1_v1.11.md e Verificacao/v1.11.0/escopo_level1_sem_xiaolei_2026-10-05/RELATORIO_ESCOPO.md.

Data: 05/10/2026. Atualizacao da versao local 1.11.0.

## NDVI e EVI

NDVI usa agora a razao (NIR-RED)/(NIR+RED), sem somar epsilon ao denominador
valido. O parametro eps de compute_ndvi funciona como tolerancia absoluta:
|NIR+RED| <= eps gera NaN; o default continua 1e-15.
Entradas nao finitas e resultados fora de [-1,1] tambem geram NaN.

EVI invalida NIR, RED ou BLUE nao finitos antes da divisao. Denominador zero,
overflow e saidas nao finitas geram NaN. A politica existente |EVI|>1 foi
preservada; nao foi alterada a parametrizacao cientifica do indice.

Os dois casos anteriormente reproduzidos retornam agora NaN:

~~~python
from pylstemp import spectral_index
import numpy as np
spectral_index("ndvi", nir=[[0.]], red=[[0.]])
spectral_index("evi", nir=[[.6]], red=[[.2]], blue=[[np.inf]])
~~~

Indices tambem aceitam escalares e vetores; um escalar produz ndarray 0D.
Arrays de entrada nao sao modificados.

## Apenas uma entrada de NDVI

O catalogo tem NDVI apenas em spectral_index, junto a EVI.
A familia duplicada spectral_indices foi retirada da descoberta publica.
O catalogo passou de 14 para 13 entradas de algoritmos.

Os imports antigos spectral_indices ainda funcionam como aliases para a
mesma implementacao e o mesmo registro canonical, sem outro ALGORITHM_SPEC.
Os nomes band_5_nir/band_4_red antigos sao traduzidos para nir/red.
Isso preserva usuarios existentes sem manter dois algoritmos NDVI.

## Conversao para reflectancia

Foi adicionada a funcao publica reflectance, com nivel do produto explicito.

~~~python
from pylstemp import reflectance
from pylstemp.calibration import read_mtl

# Level-1: conversao radiometrica para TOA.
mtl_l1 = read_mtl("cena_L1_MTL.txt")
red_toa = reflectance(red_dn_l1, metadata=mtl_l1, band=4, kind="toa")
~~~

TOA usa os fatores por banda do MTL e correcao pela elevacao solar.
sun_elevation pode ser um valor ou um raster alinhado em graus.
DN nao positivo, QA e angulos invalidos sao mascarados.
Fonte: [USGS Level-1](https://www.usgs.gov/landsat-missions/using-usgs-landsat-level-1-data-product).

Para produtos SR Level-2 ja corrigidos atmosfericamente:

~~~python
mtl_l2 = read_mtl("cena_L2_MTL.txt")
red_sr = reflectance(red_dn_l2, metadata=mtl_l2, band=4, kind="surface")
nir_sr = reflectance(nir_dn_l2, metadata=mtl_l2, band=5, kind="surface")
~~~

A funcao verifica Landsat 8/9, Collection 2, L2SP/L2SR e banda SR_B1..SR_B7.
Aplica SR=DN*0.0000275-0.2 e nao aplica uma segunda correcao solar.
Nao recorta silenciosamente valores negativos ou maiores que um.
Fonte: [USGS SR Collection 2](https://www.usgs.gov/landsat-missions/landsat-collection-2-surface-reflectance).

Essa escala converte um produto SR existente; ela nao transforma DN Level-1
ou TOA em reflectancia de superficie. Pedir kind="surface" com MTL Level-1
gera uma mensagem explicativa, indicando correcao atmosferica ou produto Level-2.

### Situacao das duas imagens

As pastas locais continuam contendo somente Level-1, sem SR_B*.
E possivel obter TOA com os insumos atuais, e essa conversao foi revalidada.
SR precisa de correcao atmosferica como LaSRC e insumos auxiliares, ou de
Level-2 correspondente. PWV Wang sozinho nao fornece todos esses insumos.

Para complementar Xiaolei com dados reais, buscar Level-2 das aquisicoes:

| Sensor | Path/row | Data |
|---|---|---|
| Landsat 8 | 221/071 | 19/09/2026 |
| Landsat 9 | 221/071 | 27/09/2026 |

Usar SR_B4/SR_B5 para NDVI, SR_B4 para Xiaolei e SR_B2 para EVI.
Combinar com BT10/BT11 Level-1 da mesma aquisicao, conferindo grade, sensor,
data e QA. Para Xiaolei, mascarar explicitamente pixels fora do dominio
[0,1] antes da recuperacao; manter as bandas originais e contar a exclusao.

Nenhuma reflectancia TOA foi apresentada como SR. Xiaolei permanece testado
com SR sintetica enquanto esses arquivos reais nao estiverem disponiveis.

## Mensagens de todos os metodos

Erros dos fluxos publicos agora informam funcao, seletores de metodo/banda/sensor,
parametro invalido e a acao esperada. As classes existentes de excecao foram
preservadas; causas originais ficam disponiveis no encadeamento.

- Forma: mostra os nomes e shapes; recomenda alinhamento explicito.
- Mascara: informa booleano e True=invalid; nao aceita mascara inteira.
- Metodo/sensor/unidade: informa os valores aceitos; None e tipos incorretos
  recebem mensagens de validacao, em vez de AttributeError.
- Bandas: aliases como B10 e BAND_11 sao aceitos com maiusculas e espacos.
- Xiaolei: explica SR_B4, escala fisica e incompatibilidade com DN/TOA.
- Wang: contexto de metodo e exigencias de janela impar, grupos, blocos e NDVI.
- Du: raster PWV gera ValueError explicativo, em vez de TypeError NumPy.
  O erro recomenda Jimenez para PWV por pixel ou uma media espacial explicita.
- Price/Kerr/Sobrino: fornecer PWV gera RuntimeWarning informando que o
  argumento sera ignorado, sem mudar o resultado numerico.
- Calibracao: distingue Level-1/Level-2 e explica requisitos de MTL/angulos.

list_algorithms() passou a incluir input_requirements e water_vapor_support
para cada algoritmo. Mensagens permanecem em ingles para consistencia com
a API e documentacao tecnica existente; este guia apresenta a explicacao em portugues.

## Verificacao

A suite ampliada inclui regressao dos dois defeitos, propagacao de NaN/+inf/-inf
em todas as bandas dos indices, denominadores quase nulos, overflow, escalares,
compatibilidade dos imports antigos, catalogo unico e mensagens de todos os fluxos.

Tambem verifica conversao TOA, escala SR Level-2 com QA, rejeicao de Level-1
como SR, colecao/sensor/banda errados e dupla correcao solar.

Os resultados finais, efeitos nas duas cenas, produtos e mensagens de exemplo
estao em Verificacao/v1.11.0/correcoes_indices_mensagens_2026-10-05/.
Resultados anteriores foram preservados. Nao houve push nem publicacao.

## Resultados finais desta rodada

- 813 testes e 106 subtestes aprovados, sem falha inesperada.
- Cobertura conjunta de linhas/ramos: 92.32%; linhas: 94.36%; ramos: 84.25%.
- Duas cenas completas reprocessadas; tres ROIs 256x256 por sensor com halo.
- 690 casos reais: 282 aprovados, 204 rejeicoes previstas e 204 bloqueados por
  falta de SR real. Os bloqueados nao contam como aprovacao cientifica de Xiaolei.
- 120 GeoTIFFs conferidos: 18 da rodada de cenas e 102 da matriz, com referencias
  numericas independentes, float32/NaN, tamanho, grade, tags e hashes.
- Hashes dos insumos iguais aos anteriores; contagens de pixels validos das
  metricas de cenas completas inalteradas; BT10 e BT11 exatamente reproduzidos
  nas contagens e medias verificadas. Originais nao foram alterados.
- As sondas NDVI 0/0 e EVI com BLUE infinito passaram; escalares e alias B10 aceitos.

Comparacao com a rodada anterior (diferenca da media, novo menos anterior):

| Metrica | Landsat 8 | Landsat 9 |
|---|---:|---:|
| NDVI | +9.44e-16 | +9.99e-16 |
| EVI | -5.55e-17 | 0 |
| Emissividade Avdan B10/B11 | +5.33e-8 | +3.04e-8 |
| LST mono + Avdan, K ou graus C | -4.22e-6 | -2.58e-6 |
| BT10/BT11 e medias demais LST | 0 | 0 |

A retirada do epsilon pode mudar a classificacao em limites exatos de NDVI de
uma parametrizacao por partes, como Avdan. As pequenas diferencas das medias
foram registradas, sem exigir igualdade artificial com a formula antiga.
Efeitos pixel a pixel podem ser maiores nos limites das classes; a tabela
nao e um limite de erro por pixel. geotiff_validation.json contem os deltas completos.

Artefatos para revisao:

- RELATORIO_CORRECOES.md: copia local deste guia.
- validation_summary.json e software_tests.txt: contagens e log final.
- coverage.json: cobertura detalhada por modulo.
- catalog.json: uma entrada NDVI e requisitos dos 13 algoritmos.
- method_messages.json: exemplos de erros e avisos.
- reflectance_assessment.json: nivel e disponibilidade real de SR por cena.
- cenas_completas/all_models_results.json: estatisticas, insumos e produtos completos.
- matriz_real/module_matrix_results.json: resultados por metodo, emissividade e PWV.
- geotiff_validation.json: verificacao dos 120 produtos e comparacao anterior.
- source_sha256.json: snapshot do codigo e testes.

Os testes comprovam implementacao, consistencia e execucao; nao estabelecem
acuracia LST/PWV contra observacoes de campo. A transferencia dos coeficientes
para Landsat 9 continua experimental. SR sintetica valida a conversao numerica,
mas ainda faltam SR_B* reais para a etapa Xiaolei com essas aquisicoes.
