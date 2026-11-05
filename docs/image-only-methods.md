# Metodos adicionais baseados na imagem

Esta implementacao entrega Ren/MSWCVR (2015) e correcao optica DOS/COST de Chavez (1996). O catalogo tem 14 seletores disponiveis, todos ativos.

## Ren 2015 MSWCVR

`water_vapor(bt10, bt11, red=red, nir=nir, method="ren-2015", window_size=33)` estima
PWV em g/cm2. As Eqs.1b/1c (p.1724) e 2 (p.1726) foram conferidas no PDF
original fornecido pelo usuario. Para i=B10 e j=B11, usando medias locais:

```text
Rji = sum((BT10 - media10)*(BT11 - media11)) / sum((BT10 - media10)^2)
Rij = sum((BT10 - media10)*(BT11 - media11)) / sum((BT11 - media11)^2)
chi_squared = Rji * Rij
PWV = -9.674 * Rji^2 + 0.653 * Rji + 9.087
```

Adota-se a aproximacao de razao de emissividades igual a 1. A Eq.2 determina
a ordem dos coeficientes; nao se usa a ordem contraditoria do texto de Du
para reconstruir essa regressao. O intercepto e 9.087, conforme a equacao,
mesmo que a anotacao da Figura 2 o apresente arredondado como 9.088.

O filtro da secao 4.2 exclui amostras fora da media NDVI local +/-1.5 desvios
padrao populacionais. As medias termicas sao calculadas sobre as amostras
retidas. Nao ha grupos NDVI globais, filtro termico de Wang ou media simetrica
das duas regressoes. O uso de medias, entre as alternativas discutidas no
artigo, e fixo nesta implementacao. NDVI precisa estar finito em [-1,1].
`ndvi_filter=False` permite explicitamente o nucleo apenas termico; nesse
caso NDVI nao e exigido nem participa da selecao.

O artigo recomenda n=10 no suporte TIRS nativo de 100 m, aproximadamente
1 km. A API isolada usa janela centrada impar de 11 pixels por padrao.
`du_from_scene(..., method="ren-2015")` usa 33 pixels por padrao,
aproximadamente 1 km na grade usual de entrega Landsat de 30 m. Sao
adaptacoes explicitas, sem reconstituir o suporte nativo: pixels termicos
reamostrados nao sao observacoes atmosfericas independentes de 30 m.
Para outras grades, forneca `window_size` de acordo com o suporte desejado.

Escolhas operacionais adicionais: `min_samples=10`, `quality_threshold=0.95`
e rejeicao de variancia nao distinguivel de zero a 64 eps, relativos ao
quadrado da media termica. O artigo cita 0.95 na discussao de ATSR2 e observa
valores altos em seus resultados; isso nao estabelece um limiar universal
obrigatorio para TIRS. Esses controles sao declarados, sem atribui-los como
prescricao de Ren. As duas variancias precisam ser positivas e a covariancia
positiva. PWV aceito deve estar em [0.06,6.3] g/cm2, dominio dos 946 perfis
TIGR usados na calibracao. Sem suporte, baixa qualidade, dominio excedido ou
pixel central invalido, a saida fica NaN, sem clipping nem preenchimento.
Nas bordas, apenas amostras existentes sao utilizadas.

`return_diagnostics=True` retorna um dicionario de arrays alinhados:
`water_vapor` (aceito), `raw_water_vapor` (antes dos filtros de qualidade e
dominio, mas depois dos requisitos de calculabilidade), `ratio`,
`chi_squared`, `sample_count` (apos filtro NDVI) e `invalid_mask`.
`chunk_rows` limita temporarios; blocos espaciais precisam de halo de
`window_size // 2`. A configuracao padrao de Wang permanece inalterada.

Ren fornece PWV, nao LST. Sua combinacao com Du e emissividade Rongali e uma
cadeia declarada; estas escolhas de suporte e emissividade nao representam
reproducao integral de todas as etapas experimentais de um unico artigo.
As verificacoes numericas nao substituem validacao com observacoes externas.

## Chavez 1996: DOS e COST

`optical_correction(rho_toa, sun_elevation=..., method="chavez-dos-1996" ou
"chavez-cost-1996", mask=..., return_diagnostics=True)` retorna a reflectancia
corrigida e parametros reutilizaveis. A mesma funcao com `parameters=parametros`
reaplica o ajuste a blocos, omitindo as opcoes de ajuste e mantendo o metodo.
A entrada e reflectancia TOA ja corrigida pelo angulo solar, com um unico
angulo solar da cena, e nao DN/radiancia ou um produto SR.

A partir da Eq.2, pp.1027--1029, usando a mesma selecao de haze no DOS/COST:
`rho_DOS = rho_TOA - (rho_dark - 0.01)`;
`rho_COST = rho_DOS / sin(elevacao_solar)`.
As hipoteses sao TAUv=1, Edown=0 e, para COST, TAUz=cos(zenite).

Chavez (1996), p.1029, declara o mesmo Lhaze para DOS e COST nesta
comparacao. O fator COST e independente da banda: as reflectancias mudam,
mas NDVI_COST = NDVI_DOS onde ambas as bandas sao validas e a soma nao e
zero. Isto nao torna as correcoes equivalentes para reflectancia absoluta.
A rejeicao de valores acima de 1 pode tornar as mascaras diferentes.
Nao recalcular o objeto escuro com uma transmitancia diferente apenas para
forcar diferenca de NDVI: isso mudaria a convencao de Lhaze aqui declarada.
Conferencia independente em radiancia: tests/test_optical_chavez_reference.py.

O termo de distancia Terra-Sol ja esta incorporado na reflectancia TOA do MTL.

O percentil padrao e **0.01**, isto e, percentil 0.01 e nao 1%.
Esta regra de selecao e uma adaptacao computacional explicita, nao um percentil
universal prescrito por Chavez. Ajustar o haze sobre a area declarada de
calibracao e reutilizar os mesmos parametros em todos os blocos; ajustar por
bloco altera o metodo. A existencia de alvos escuros nao e garantida pela API.
Se o percentil ficar abaixo da reflectancia escura assumida, o ajuste gera
erro e precisa ser revisto, em vez de truncar haze negativo.

A correcao preserva NaN e mascaras, rejeitando resultados fora de [0,1].
Chavez avaliou imagens TM; o uso OLI/OLI-2 aqui e um cenario experimental,
sem importar seus coeficientes TM de transmitancia por banda. A aproximacao
COST nao equivale a LaSRC/SR operacional nem corrige a atmosfera termica.

## Exemplos por metodo

A pasta [exemple](../exemple/README.md) apresenta os metodos disponiveis em notebooks independentes.
