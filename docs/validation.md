# Estado da verificacao - v1.11.0

## Escopo atual

O catalogo possui 17 seletores por familia, com 20 fichas de equacoes/variantes
e calibracoes auxiliares. As [fichas](method-cards.md) registram referencias,
coeficientes, unidades, dominios, sensores e adaptacoes. A conferencia numerica
nao estabelece acuracia de campo nem valida automaticamente transferencias
AVHRR/TM/Landsat8 para outro sensor.

## Exemplos por metodo

A pasta [exemple](../exemple/README.md) contem 17 notebooks independentes,
um por seletor. Cada notebook tem uma introducao breve, dados necessarios,
a funcao geral, o detalhamento dos parametros e uma aplicacao com imagens.
Cada arquivo tem dez celulas, quatro delas de codigo; nao ha guia agregado
ou scripts de comparacao concorrendo com esses exemplos.

Os 17 notebooks foram executados com imagens sinteticas alinhadas e MTL.
Seis configuracoes adicionais cobrem entrada DN/banda11, Sobrino2008 full,
Ren sem filtro NDVI e diagnosticos LST. Quatorze notebooks tambem foram
executados em recortes64x64 de duas cenas Landsat8/9. Kerr e Sobrino2004/2008
exigem reflectancia superficial apropriada e foram verificados com arquivos
sinteticos dedicados, sem atribuir dados de outro sensor a um produto real.
As 51 execucoes conferem forma, projecao, tipo, NoData e valores dos GeoTIFFs.

Essa rodada reorganiza exemplos/documentacao; as equacoes e a API nao foram
alteradas. O pacote opcional dos exemplos deixou de exigir matplotlib,
pois os notebooks atuais usam apenas leitura/calculo e exportacao de imagens.

## Regressao e distribuicao

Os 27 testes publicos essenciais usam referencias numericas sinteticas
independentes, sem artigos ou imagens privadas. A CI os executa contra o
wheel instalado. Build, twine, conteudo do wheel/sdist e instalacao isolada
sao verificados localmente; a matriz remota depende de publicacao autorizada.
A bateria completa, os produtos e os historicos detalhados continuam em
`Verificacao/`, fora do Git e dos pacotes. A rodada anterior de ajustes da API
passou 913 testes e 158 subtestes; nao e apresentada como uma validacao nova
de campo ou de cenas inteiras.

## Limites que permanecem explicitos

- Emissividades, extremos NDVI e perfis atmosfericos precisam representar a cena.
- PWV/perfis demonstrativos dos notebooks nao sao observacoes atmosfericas.
- Inconsistencias das fontes e escolhas de implementacao estao nas fichas.
- Parametros nao compativeis, extrapolacoes e pixels rejeitados nao sao corrigidos
  por clipping, preenchimento ou troca silenciosa de metodologia.

Veja [contratos cientificos](scientific-methods.md) e [API](api-reference.md).


## Seletores Jimenez-Munoz SC/SW (2026-10-23)

Os nomes canonicos sao `jimenez-munoz-2014-sc` e `jimenez-munoz-2014-sw`,
com a sigla depois do ano. Os nomes anteriores permanecem como aliases de
compatibilidade. Os outros cinco nomes split-window continuam inalterados.
A regressao verifica os nomes do catalogo e a equivalencia numerica entre
seletores novos e antigos.
