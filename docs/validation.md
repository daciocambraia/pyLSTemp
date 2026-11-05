# Estado atual — 27/10/2026

A versão atual tem 14 seletores disponíveis, todos ativos, e 16 fichas científicas. Rozenstein2014 e Sobrino2004 TM6 foram removidos integralmente; Sobrino2008 permanece removido. Não há chamadas explícitas para esses métodos. Os registros abaixo descrevem versões anteriores e não definem o catálogo atual.

# Estado da verificacao - v1.11.0

## Escopo atual

O catálogo padrão possui 14 seletores (tambem 14 com `include_inactive=True`), com 16 fichas de equacoes/variantes
e calibracoes auxiliares. As [fichas](method-cards.md) registram referencias,
coeficientes, unidades, dominios, sensores e adaptacoes. A conferencia numerica
nao estabelece acuracia de campo nem valida automaticamente transferencias
AVHRR/TM/Landsat8 para outro sensor.

## Exemplos por metodo

Estado da verificação histórica: 18 notebooks. As rodadas com 19/17 notebooks descritas abaixo antecedem a remoção integral de Sobrino 2008.

A pasta [exemple](../exemple/README.md) contém 16 notebooks do fluxo principal:
14 exemplos de métodos e dois exemplos de calibração, `toa_radiance` e
`toa_reflectance`. Os arquivos com seletor usam `funcao__metodo.ipynb`;
funcoes sem seletor usam seu proprio nome. Cada notebook apresenta introducao,
entradas com unidades, funcao geral, tabela ordenada de parametros e aplicacao.
Todos os notebooks seguem a organização aprovada no piloto Jiménez SC:
entradas e unidades, chamada mínima, exemplo executável, preparação, alternativas,
referência completa e limites. O caminho executável lê imagens preparadas sem
exigir uma cena completa; nos oito exemplos de LST, emissividade pronta é a
rota recomendada e a entrada por bandas aparece como alternativa.

Na revisao de 2026-10-25, os 19 notebooks foram executados com pequenos GeoTIFFs
sinteticos 40x40 e MTL. As duas rotas dos oito notebooks de LST produziram os
mesmos resultados; os metodos padrao omitidos coincidiram com a selecao explicita.
As novas conversoes TOA foram comparadas com suas equacoes de calibracao,
incluindo elevacao solar escalar/raster e padrao MTL. Tambem foram conferidos
nomes dos argumentos, ordem das tabelas, links e cobertura dos 17 seletores.
Após a aplicação do formato a todos os exemplos, os 19 foram executados novamente
com GeoTIFFs sintéticos preparados, verificando grade, unidade, NoData, valores,
referência de parâmetros e alternativas aplicáveis. Sobrino 2008 full não foi
executado com coeficientes hipotéticos; seu código foi conferido apenas em sintaxe.
O verificador e os relatorios ficam em `Verificacao/revisao_exemplos_2026-10-25/`,
fora do repositorio publico. Sao verificacoes de execucao, nao acuracia de campo.

Na rodada anterior, os 17 notebooks foram executados com imagens sinteticas alinhadas e MTL.
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

Os 50 testes publicos essenciais usam referencias numericas sinteticas
independentes, sem artigos ou imagens privadas. A CI os executa contra o
wheel instalado. Build, twine, conteudo do wheel/sdist e instalacao isolada
sao verificados localmente; a matriz remota e executada no GitHub Actions.
Na verificacao de 2026-11-05, passaram 50 testes e 68 subtestes, com
Rasterio instalado. O aviso de Kerr registra o limite da adaptacao para Landsat.
Essa verificacao confirma execucao e regressao numerica; nao mede acuracia de campo.
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


## Revisão dos pontos metodológicos (2026-10-24)

A revisão acrescentou quatro regressões de domínio/aviso/evidência; passaram
31 testes e 71 subtestes. As 51 execuções dos notebooks foram repetidas.
As equações, coeficientes e hashes das fontes das 20 fichas permaneceram iguais;
os seis resultados de referência split-window preservaram igualdade exata.

O catálogo passou a distinguir evidência numérica de aplicabilidade por sensor
e acurácia empírica. Os avisos de Price/Kerr/Sobrino1993 explicitam a adaptação
AVHRR → Landsat. Jiménez-Muñoz SW avisa sobre extrapolação de PWV >6 g/cm²
somente nos pixels válidos, preservando a saída calculada.

Uma busca dirigida identificou a aplicação externa dos métodos históricos
em Landsat 8, com limites descritos em scientific-methods.md. Isso não foi
registrado como uma nova calibração para TIRS nem como validação desta biblioteca.

O arquivo local contém um protocolo, uma planilha e um avaliador de pareamentos
LST/PWV/reflectância. Ele foi conferido com dados explicitamente sintéticos,
separando proxies e intercomparações e rejeitando mistura de grupos de ajuste e
avaliação. A proposta inicial de um piloto público foi retirada do plano ativo por orientação
do usuário. A avaliação está restrita às duas cenas existentes em `Imagens/`, de
19/09/2026 (Landsat8) e 27/09/2026 (Landsat9). Sem referência independente nessas
pastas, os resultados permitem consistência operacional e comparação entre métodos,
não acurácia de campo ou recalibração comprovada. Não serão coletadas novas cenas
neste escopo.

## Matriz com recortes reais (2026-10-24)

A bateria local avaliou 34.416 configurações-base em 18 recortes de 64 × 64
pixels das duas cenas Landsat 8/9 já disponíveis, usando halos de 16 pixels
nos estimadores locais de PWV. Foram cruzadas quatro preparações ópticas,
nove configurações de PWV (raster e média do recorte), emissividades e as
opções implementadas de perfil/faixa de Rozenstein.

Foram 19.892 configurações com pixels válidos, 3.392 chamadas sem pixels
aceitos e 11.132 casos com PWV escalar fora do domínio. Não houve falhas
inesperadas. Passaram 31 testes públicos de regressão, 32 controles negativos
e as verificações de unidades, rotas equivalentes, processamento em blocos e
leitura dos GeoTIFFs. Nenhuma equação ou coeficiente precisou ser alterado.

Esses números incluem cenários de sensibilidade com transferência explícita
de convenção óptica/endmembers; não tornam todas as combinações calibrações
validadas. Sobrino 2004 TM6 foi corretamente rejeitado para TIRS e a variante
completa de Sobrino 2008 não recebeu coeficientes de solo inventados.

Os resultados evidenciam forte dependência da cobertura em relação ao domínio
de PWV e diferenças sistemáticas entre a correção apenas por emissividade e
os métodos com parametrização atmosférica. Diferenças entre métodos não são
erros contra referência independente. A evidência é de consistência operacional
nos recortes, sem estimativa de acurácia de campo ou garantia para outros ambientes.

Scripts, recortes, rasters, estatísticas, gráficos e proveniência permanecem
somente em `Verificacao/matriz_real_2026-10-24/`, fora da distribuição. O relatório
local distingue a matriz nos recortes dos mapas-base completos complementares.


## Remoção de Sobrino 2008 completo — 25/10/2026

A variante completa foi removida da API, implementação, catálogo e exemplos. Os registros acima descrevem verificações históricas anteriores à remoção. A variante simplificada conserva a equação e exige endmembers fundamentados por banda. Chamadas com `variant="full"` são rejeitadas; os parâmetros exclusivos da variante completa não integram mais a assinatura pública. Naquela etapa, o catálogo tinha 19 fichas; a remoção integral posterior reduziu para 18.


## Remoção integral de Sobrino 2008 — 25/10/2026

As duas variantes foram retiradas. O estado atual tem 16 seletores, 18 fichas e 18 notebooks. Registros anteriores são históricos. O notebook removido foi arquivado localmente em `Verificacao/remocao_sobrino_2008_2026-10-25/`. Avdan, Rongali e Sobrino 2004 TM6 permanecem nas suas condições de aplicação.


## Fluxo principal — 26/10/2026

O catálogo padrão tem 14 seletores e a pasta principal de exemplos tem 16 notebooks. Rozenstein 2014 e Sobrino 2004 TM6 ficam fora do fluxo principal, com implementações e testes numéricos preservados. O catálogo completo com `include_inactive=True` mantém 16 seletores e as 18 fichas científicas continuam registradas. Resultados anteriores, incluindo a bateria de 54.828 casos, permanecem históricos e não foram recalculados nem reclassificados por essa alteração de escopo.
