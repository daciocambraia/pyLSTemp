# Estado da validacao - v1.11.0

## Metodos adicionais - 22/10/2026

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
sem aplicar seus coeficientes a B10/B11. Ren nao foi implementado nem testado:
o PDF e as equacoes primarias continuam inacessiveis no editor.

As fontes, a suite e os produtos ficam no arquivo local de verificacao.
Veja [metodos e escolhas de implementacao](image-only-methods.md).

## Rodada anterior


A verificacao local de 22/10/2026 aprovou 759 testes e 106 subtestes.
O workflow Wang -> Du foi conferido em recortes de 128 x 128 pixels de duas
cenas Landsat 8/9, com 24 GeoTIFFs reabertos e verificados. A avaliacao incluiu
referencias numericas independentes, limites, mascaras, unidades e equivalencia
entre execucao inteira e blocos com halo.

Esses resultados verificam implementacao e funcionamento. Nao ha validacao
de acuracia absoluta com observacoes independentes de LST/PWV. Coeficientes
Landsat 8 aplicados ao Landsat 9 permanecem experimentais; Price, Kerr e Sobrino
sao adaptacoes historicas AVHRR. O estimador atmosferico original Du/Ren ainda
requer auditoria das equacoes e nao esta implementado.

A suite completa, os verificadores, os dados e os relatorios detalhados sao
mantidos localmente em `Verificacao/`, fora do Git e dos pacotes. Uma clonagem
do repositorio publico nao inclui essa suite.

A CI do GitHub verifica instalacao, importacao e empacotamento em Windows/Linux.
Essas verificacoes automaticas nao substituem os testes cientificos locais.
Veja [metodos e limites](scientific-methods.md) e [workflow Du/PWV](du-pwv-workflow.md).
