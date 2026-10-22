# Metodos adicionais baseados na imagem

Esta implementacao entrega Rozenstein (2014), funcoes de emissividade de
Sobrino (2004/2008) e correcao optica DOS/COST de Chavez (1996).
O catalogo passa a 13 algoritmos registrados: Rozenstein e a nova entrada de
LST. As funcoes parametrizadas de emissividade e correcao optica nao sao
contadas como algoritmos calibrados de Landsat 8/9 independentes.
Ren/MSWCVR continua pendente: o PDF e as imagens das equacoes nao puderam ser
obtidos do editor (HTTP 403), apesar do texto HTML acessivel. Nao ha chave
`ren-2015`, coeficientes inferidos nem substituicao oculta por Wang.

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

`sobrino_2004_tm6(ndvi, mask=...)` implementa a Eq.13 para a classe mista
0.2<=NDVI<=0.5: epsilon=0.004*Pv+0.986, com Pv quadratico (Eq.9).
Para NDVI>0.5, usa 0.99, conforme a classe de vegetacao descrita no artigo.
NDVI<0.2 fica NaN: nao foi inventada uma relacao solo/vermelho ausente na
Eq.13. A mascara deve excluir classes inadequadas, incluindo agua e neve.
Essas constantes sao especificas de TM6, sem calibracao para B10/B11.

### Sobrino 2008: funcoes por banda

`sobrino_2008(ndvi, soil_emissivity=..., vegetation_emissivity=...)` usa a
formulacao simplificada da Eq.9, pp.317--318. Os dois endmembers sao
obrigatorios, escalares ou rasters alinhados, e precisam de justificativa para
a banda. A FVC e quadratica entre 0.2 e 0.5 e limitada a 0/1 fora dos extremos.

`variant="full"` implementa Eqs.5--8 com relacao de solo `a+b*rho_red` e
cavidade na classe mista. Requer `red_surface` e
`soil_red_coefficients=(a,b)`, especificos da banda. **Nao fornecer radiancia
TOA ou reflectancia TOA no lugar de reflectancia de superficie.**
`cavity_factor=0.55` e a hipotese geometrica usada em Sobrino 2004;
`vegetation_cavity=0.005` segue o valor tipico discutido em 2008.
Valores fora do dominio fisico viram NaN; nao sao truncados.
A aplicabilidade a solos minerais, agua, neve e areas urbanas requer mascara
ou parametrizacao propria; NDVI nao identifica essas classes universalmente.

`split_window_from_emissivity(bt10, bt11, e10, e11, lst_method=..., ...)`
permite usar os pares preparados sem recalcular a emissividade dentro da API.
Para Kerr, fornecer `ndvi_image`; para Rozenstein, fornecer o perfil.
As quatro entradas devem ter a mesma forma e a mesma grade espacial.

## Chavez 1996: DOS e COST

`fit_chavez(rho_toa, sun_elevation=..., method="dos" ou "cost", mask=...)`
retorna parametros reutilizaveis. `chavez_reflectance(rho_toa,
parameters=parametros, mask=...)` aplica a correcao a imagem ou blocos.
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

## Exemplo e verificacao

```bash
python exemples/metodos_imagem.py CAMINHO_DA_CENA --perfil midlatitude-summer --saida resultados/metodos
```

O exemplo usa um recorte central 128x128, halo de Wang e limites NDVI globais.
Seu ajuste Chavez pertence ao **recorte**, sem ser apresentado como ajuste da
cena inteira. O PWV de Wang usa NDVI em radiancia, mantido fixo neste contraste.
Sobrino 2008 Eq.9 usa os endmembers TIRS da implementacao existente Rongali
2018, declarados como parametros: esta combinacao nao e calibracao nova nem
reproducao integral de um artigo. A funcao TM6 nao e aplicada a essas cenas.

A suite cientifica e os produtos ficam localmente em `Verificacao/`, fora do
Git. Veja [estado da validacao](validation.md) e [fontes](references.md).
