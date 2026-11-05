# Contratos cientificos e limites

A biblioteca implementa equacoes publicadas e registra sua origem nas
[fichas cientificas](method-cards.md). Esses registros descrevem coeficientes,
sensores de origem, dominios e decisoes de implementacao. Eles nao certificam
acuracia empirica e nao definem um plano de pesquisa ou uma amostra de campo.

## Grandezas e preparacao

DN Level-1, radiancia TOA, reflectancia TOA e reflectancia superficial sao
grandezas distintas. Radiancia termica usa W m-2 sr-1 um-1; BT entra nas
familias de temperatura/PWV em kelvin. PWV usa g/cm2. Emissividade e
adimensional e deve corresponder a banda e ao sensor. A saida LST pode ser
kelvin ou celsius, explicitamente declarados.

Use coeficientes MTL da propria cena. Constantes do sensor sao fallback,
nao substituem a verificacao da calibracao real. QA_PIXEL e QA_RADSAT devem
ser alinhadas aos dados. NaN/nodata e a mascara de entrada sao preservados;
sem mask, funcoes numericas nao fazem selecao QA por conta propria.

## Calibracao e correcao optica

calibrate agrupa radiancia, reflectancia TOA e temperatura de brilho.
BT nao e LST; reflectancia TOA nao e reflectancia superficial.
surface_reflectance apenas escala um produto SR Level-2 ja existente.

Chavez DOS/COST sao aproximacoes derivadas de estudos TM. A implementacao
recebe reflectancia TOA corrigida pelo angulo solar e ajusta haze em pixels
validos. Ajustar uma vez na cena e reutilizar os parametros nos blocos evita
mudar a metodologia em cada bloco. Essa correcao nao estabelece equivalencia
com produtos SR oficiais nem validade empirica para outro sensor.

## NDVI e emissividade

O NDVI e calculado internamente quando vermelho/NIR sao fornecidos. A
convencao radiometrica precisa ser coerente com a fonte e com os limiares:
radiancia, TOA e SR nao sao intercambiaveis apenas porque compartilham grade.
Declarar optical_quantity descreve a escolha, sem converter as entradas.

Avdan e Rongali preservam suas equacoes e endmembers documentados.
Transferir limiares ou endmembers exige justificativa para a cena/sensor.
A selecao da emissividade e independente da equacao LST; use emissivity
separadamente para fornecer emissividades prontas. A rota automatica por
bandas usa Avdan em single_window e Rongali em split_window.

## PWV, janelas e suporte espacial

Wang usa agrupamento NDVI com limites globais da cena, filtro termico e
regressao por grupos. Reutilize os mesmos limites em recortes/blocos.
Ren usa o estimador de covariancia/variancia e a equacao documentada
PWV = -9.674*Rji**2 + 0.653*Rji + 9.087. Nao reordenar coeficientes para
acomodar outra descricao. O filtro NDVI Ren pode ser desligado explicitamente.

Janelas impares e sua transferencia para uma grade reamostrada sao escolhas
registradas. Uma grade de 30 m nao cria observacoes termicas independentes
de 30 m. Declare janela e criterios operacionais. Medias espaciais devem
preservar quantidade de contribuintes e motivos de rejeicao.

## Temperatura e dominios

| Familia e metodo | Condicoes |
| --- | --- |
| single_window / avdan-2016 | BT10 e emissividade B10; correcao de emissividade, sem estimativa atmosferica explicita |
| single_window / jimenez-munoz-2014 | Radiancia B10 e PWV; intervalo operacional 0..3 g/cm2 |
| split_window / du-2015 | BT10/BT11, emissividades; PWV por faixa em 0..6.3 ou coeficientes gerais sem PWV |
| split_window / jimenez-munoz-2014 | PWV nao negativo; fonte avaliada em 0..6 g/cm2, acima disso extrapolacao sinalizada |
| split_window / price-1984, kerr-1992, sobrino-1993 | Coeficientes AVHRR adaptados; validade Landsat exige verificacao independente |

Kerr utiliza NDVI com convencao superficial coerente com seus limiares;
na interface comum, emissividades continuam exigidas, mas nao entram na sua
equacao. Parametros atmosfericos fornecidos a metodos que nao os utilizam
produzem aviso de parametro ignorado.

Coeficientes de recuperacao Landsat 8 aplicados a Landsat 9 permanecem uma
transferencia experimental. Nomes de metodos repetidos sao resolvidos pela
familia: Avdan emissividade difere de Avdan LST; Jimenez SC difere de SW.

## Interpretacao dos diagnosticos

Resultados brutos podem ser finitos fora dos criterios operacionais e devem
ser interpretados com suas flags. O modo diagnostico preserva as equacoes;
fora das faixas PWV de Du, sinaliza o uso dos coeficientes gerais, sem
escolher silenciosamente a faixa mais proxima. Valores ausentes e expressoes
indefinidas continuam NaN. Flags nao sao probabilidades de acuracia.

Os [contratos de resultados](result-contracts.md), a [legenda de flags](diagnostic-quality.md)
e o [estado de verificacao](validation.md) descrevem o comportamento vigente.
Referencias completas estao em [references.md](references.md).
