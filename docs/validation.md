# Estado da validacao - v1.11.0

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
