# Estado da validacao - v1.11.0

## NDVI interno e simplificacao da API - 22/10/2026

A suite local migrada passou 879 testes e 107 subtestes, incluindo 28 testes
novos das chamadas com bandas, ausencia da API de indices, entradas ambiguas,
mascaras e equivalencia com resultados salvos antes da alteracao. As referencias
numericas independentes dos metodos foram preservadas; os testes do dispatcher
retirado foram substituidos por verificacoes do contrato interno e da API nova.

Os 36 GeoTIFFs Ren/Du dos dois recortes Landsat 8/9 foram recalculados e
conferidos. Os rasters de PWV/LST permanecem identicos aos anteriores.
As mesmas verificacoes numericas anteriores foram repetidas para formulas,
qualidade, dominios e blocos. NDVI permanece necessario nas metodologias
correspondentes, mas e calculado internamente a partir de vermelho/NIR.
O catalogo tem 13 algoritmos e nao lista NDVI como metodo independente.

Esta verificacao nao estabelece acuracia externa de PWV/LST; os limites
cientificos e a transferencia experimental para Landsat 9 permanecem.
Os testes, resultados anteriores e modulos retirados estao no arquivo local
de verificacao, fora do Git e dos pacotes.

## Ren/MSWCVR e documentacao - 22/10/2026

As equacoes originais de Ren foram conferidas no PDF fornecido pelo usuario.
A suite local passou 851 testes e 109 subtestes, incluindo 26 testes Ren e
a execucao do exemplo simplificado do README e dos blocos do guia de uso.
Foram verificados regressao e referencia escalar independente, filtro NDVI
local, qualidade, dominios, mascaras, janelas, bordas, chunks e halo.
A configuracao numerica padrao de Wang permanece coberta pela regressao.

Nos recortes centrais 128x128 das cenas Landsat 8/9, foram reabertos e
conferidos 36 GeoTIFFs dos modos Ren raster, Ren media e Du geral: grade,
CRS, unidades, tipo, NoData e valores. Houve 72 comparacoes escalares de PWV,
com diferenca maxima inferior a 2e-10 g/cm2, alem de equivalencia entre
chunks e blocos com halo. O PWV aceito cobriu 15694 de 16384 pixels no
Landsat 8 e 14361 de 16384 no Landsat 9; as lacunas foram preservadas.
Essas contagens se referem aos recortes, nao as cenas inteiras.

O controle de qualidade 0.95, minimo de 10 amostras e janelas centradas
impares sao escolhas operacionais explicitas. O workflow usa 33 pixels
na grade usual de 30 m para aproximar 1 km; isso nao reproduz observacoes
termicas independentes nessa resolucao. O dominio e [0.06,6.3] g/cm2.
Veja [equacoes e adaptacoes](image-only-methods.md#ren-2015-mswcvr).

Esta rodada verifica implementacao e operacao; nao estabelece acuracia com
PWV/LST externos. A transferencia de coeficientes para Landsat 9 continua
experimental. Testes, PDF e produtos permanecem no arquivo local de verificacao.

## Rodada anterior: Rozenstein, Sobrino e Chavez - 22/10/2026

A rodada local passou 824 testes e 107 subtestes, incluindo 65 testes novos
para Rozenstein, Sobrino e Chavez. Foram conferidos tabelas, referencias
escalares independentes, dominios, mascaras, singularidade e blocos.

Em dois recortes 128x128 Landsat 8/9, foram reabertos 38 GeoTIFFs de
intermediarios e resultados. Houve 96 comparacoes escalares de LST, com
diferenca maxima de 2.28e-13 K e tolerancia de 2e-10 K. Os dois perfis
atmosfericos publicados foram tratados como cenarios experimentais.
Rozenstein com PWV Wang no dominio [0.5,3] apresentou 2023 pixels validos
no recorte Landsat 8 e 1156 no Landsat 9, sobre 16384 pixels por recorte.
A baixa cobertura foi preservada, sem clipping ou preenchimento de PWV.

O ajuste Chavez desta rodada pertence aos recortes, nao a cena completa.
A combinacao Sobrino 2008 usa endmembers Rongali declarados; nao e nova
calibracao espectral. Sobrino 2004 foi testado numericamente no dominio TM6,
sem aplicar seus coeficientes a B10/B11. Naquela rodada, Ren ainda nao havia sido implementado; a
pendencia de acesso ao artigo foi resolvida na rodada Ren descrita acima.

As fontes, a suite e os produtos ficam no arquivo local de verificacao.
Veja [metodos e escolhas de implementacao](image-only-methods.md).

## Rodada anterior: Du/Wang


A verificacao local de 22/10/2026 aprovou 759 testes e 106 subtestes.
O workflow Wang -> Du foi conferido em recortes de 128 x 128 pixels de duas
cenas Landsat 8/9, com 24 GeoTIFFs reabertos e verificados. A avaliacao incluiu
referencias numericas independentes, limites, mascaras, unidades e equivalencia
entre execucao inteira e blocos com halo.

Esses resultados verificam implementacao e funcionamento. Nao ha validacao
de acuracia absoluta com observacoes independentes de LST/PWV. Coeficientes
Landsat 8 aplicados ao Landsat 9 permanecem experimentais; Price, Kerr e Sobrino
sao adaptacoes historicas AVHRR. O estimador Ren, pendente naquela etapa, esta disponivel na rodada atual.

A suite completa, os verificadores, os dados e os relatorios detalhados sao
mantidos localmente em `Verificacao/`, fora do Git e dos pacotes. Uma clonagem
do repositorio publico nao inclui essa suite.

A CI do GitHub verifica instalacao, importacao e empacotamento em Windows/Linux.
Essas verificacoes automaticas nao substituem os testes cientificos locais.
Veja [metodos e limites](scientific-methods.md) e [workflow Du/PWV](du-pwv-workflow.md).
