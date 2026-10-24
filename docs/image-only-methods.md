# Metodos adicionais baseados na imagem

Esta implementacao entrega Ren/MSWCVR (2015), Rozenstein (2014), funcoes de
emissividade de Sobrino (2004/2008) e correcao optica DOS/COST de Chavez (1996).
O catalogo tem 17 seletores por familia. Os metodos parametrizados de
emissividade e correcao optica nao contam como algoritmos calibrados
independentes de Landsat 8/9.

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
`du_from_scene(..., pwv_method="ren-2015")` usa 33 pixels por padrao,
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

## Rozenstein 2014

`split_window(..., lst_method="rozenstein-2014", water_vapor=pwv,
atmospheric_profile="midlatitude-summer", temperature_range="0-60")`.

Reproduz Eqs.3--10, p.5771, e Tabelas 1--2 do artigo. Usa BT em kelvin,
emissividades distintas B10/B11 e PWV em g/cm2. O perfil deve ser escolhido
explicitamente: `us-standard-1976` ou `midlatitude-summer`. Nenhum e assumido
como representativo de uma atmosfera tropical umida. Os dois podem ser
comparados como cenarios de sensibilidade previamente definidos.

PWV escalar deve ser finito em [0.5,3]; escalar fora do intervalo gera erro.
Raster exige a mesma forma das entradas; pixels fora do dominio ou nao finitos
viram NaN. Transmitancias devem estar em (0,1]. O denominador da Eq.10 e
rejeitado se nao for distinguivel de zero a 64 eps relativos a escala dos seus
termos: esta tolerancia e uma decisao numerica, nao um limiar publicado.

Faixas de linearizacao: `0-60` (texto p.5770), `0-30`, `0-40`, `10-40` e
`10-50` (Tabela 1). A faixa e escolhida antes do calculo. Resultados fora dela
ficam NaN; nao se escolhe outra faixa retrospectivamente para recuperar pixels.
A conversao opcional para Celsius ocorre depois da equacao em kelvin.

## Emissividade Sobrino

### Sobrino 2004: TM5 banda 6

`emissivity(red=red, nir=nir, method="sobrino-2004-tm6", band=6, mask=...)` implementa a Eq.13 para a classe mista
0.2<=NDVI<=0.5: epsilon=0.004*Pv+0.986, com Pv quadratico (Eq.9).
Para NDVI>0.5, usa 0.99, conforme a classe de vegetacao descrita no artigo.
NDVI<0.2 fica NaN: nao foi inventada uma relacao solo/vermelho ausente na
Eq.13. A mascara deve excluir classes inadequadas, incluindo agua e neve.
Essas constantes sao especificas de TM6, sem calibracao para B10/B11.
A secao 4, p.436, calcula NDVI de reflectividades TOA ou de superficie,
preferindo superficie. Radiancia nao e uma entrada equivalente estabelecida.

### Sobrino 2008: funcoes por banda

`emissivity(red=red, nir=nir, method="sobrino-2008", soil_emissivity=..., vegetation_emissivity=...)` usa a
formulacao simplificada da Eq.9, pp.317--318. Os dois endmembers sao
obrigatorios, escalares ou rasters alinhados, e precisam de justificativa para
a banda. A convencao optica e os limiares usados no NDVI tambem precisam de
justificativa; a variante simplificada nao estabelece equivalencia entre
radiancia e reflectancia. A FVC e quadratica entre 0.2 e 0.5 e limitada a 0/1 fora dos extremos.

`variant="full"` implementa Eqs.5--8 com relacao de solo `a+b*rho_red` e
cavidade na classe mista. Requer `red_surface` e
`soil_red_coefficients=(a,b)`, especificos da banda. **Nao fornecer radiancia
TOA ou reflectancia TOA no lugar de reflectancia de superficie.**
`cavity_factor=0.55` e a hipotese geometrica usada em Sobrino 2004;
`vegetation_cavity=0.005` segue o valor tipico discutido em 2008.
Valores fora do dominio fisico viram NaN; nao sao truncados.
A aplicabilidade a solos minerais, agua, neve e areas urbanas requer mascara
ou parametrizacao propria; NDVI nao identifica essas classes universalmente.

`split_window(bt10, bt11, emissivity_10=e10, emissivity_11=e11, lst_method=..., ...)`
permite usar os pares preparados sem recalcular a emissividade dentro da API.
Para Kerr, fornecer `band_4_red`/`band_5_nir` para NDVI interno (ou NDVI preparado); para Rozenstein, fornecer o perfil.
As quatro entradas devem ter a mesma forma e a mesma grade espacial.

## Chavez 1996: DOS e COST

`optical_correction(rho_toa, sun_elevation=..., method="chavez-dos" ou
"chavez-cost", mask=..., return_diagnostics=True)` retorna a reflectancia
corrigida e parametros reutilizaveis. A mesma funcao com `parameters=parametros`
reaplica o ajuste a blocos, omitindo as opcoes de ajuste e mantendo o metodo.
A entrada e reflectancia TOA ja corrigida pelo angulo solar, com um unico
angulo solar da cena, e nao DN/radiancia ou um produto SR.

A partir da Eq.2, pp.1027--1029, usando a mesma selecao de haze no DOS/COST:
`rho_DOS = rho_TOA - (rho_dark - 0.01)`;
`rho_COST = rho_DOS / sin(elevacao_solar)`.
As hipoteses sao TAUv=1, Edown=0 e, para COST, TAUz=cos(zenite).
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

A pasta [exemple](../exemple/README.md) separa Ren, Rozenstein, Sobrino2004,
Sobrino2008, Chavez DOS e Chavez COST em notebooks independentes. Cada um
explica as entradas, a funcao geral, os parametros e os limites do metodo.
Os antigos scripts de comparacao e seus resultados continuam no arquivo
local de verificacao. Veja [validacao](validation.md) e [fontes](references.md).
