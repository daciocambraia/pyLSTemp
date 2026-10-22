# Du com PWV raster e workflow de cena

Entrega de 22/10/2026 para v1.11.0. Este workflow nao acrescenta uma entrada independente ao catalogo.

`split_window(..., lst_method="du-2015", water_vapor=None)` preserva os
coeficientes gerais. PWV escalar continua exigindo valor finito em [0,6.3]
g/cm2. Raster exige exatamente a mesma forma das BT e emissividades; nao ha
broadcasting. Valores nao finitos ou fora do dominio ficam NaN, sem clipping
ou substituicao pelo conjunto geral. Os limites das faixas sao inclusivos;
as sobreposicoes usam a media das LSTs calculadas pelos conjuntos aplicaveis.
Arrays iguais em forma ainda precisam representar a mesma grade espacial.

## Execucao a partir de uma cena

```python
from pylstemp.scene import LandsatScene
from pylstemp.workflows import du_from_scene

with LandsatScene("caminho/para/cena") as cena:
    resultado = du_from_scene(
        cena, window=(3000, 3128, 3000, 3128),
        pwv_mode="raster", pwv_method="wang-2015", unit="celsius",
    )
    resultado.export(cena, "resultados/du_wang")
```

A janela deve estar dentro da cena. Sem `window`, o processamento cobre a
cena inteira; a estimativa local pode exigir bastante tempo e memoria.
`chunk_rows` limita as janelas temporarias de Wang, mas os arrays de entrada
e saida ainda ocupam memoria proporcional ao tamanho da area solicitada.
Para grandes cenas, processe janelas menores e reutilize `ndvi_range`.

Modos `pwv_mode`:

- `general`: nao calcula PWV, usa o conjunto geral de Du e QA convencional.
- `mean`: estima Wang, conserva PWV no dominio comum [0.066,6.3] e calcula
  uma media dos pixels validos **da janela de saida**. A media seleciona os
  coeficientes para todos os pixels com entradas validas. Sem amostras, gera erro.
- `raster`: estima Wang e seleciona os coeficientes localmente, preservando
  lacunas de PWV como lacunas de LST.

Os modos atmosfericos excluem agua por QA, alem das exclusoes convencionais.
O modo geral pode incluir agua; use as mascaras de cada resultado e o suporte
comum nas comparacoes. Media e raster nao sao numericamente equivalentes.
O limite inferior 0.066 vem do intervalo TIGR3 adotado para Wang nas verificacoes
existentes; o limite superior 6.3 vem de Du. O PWV bruto e preservado para auditoria.

## Blocos e mascara do usuario

```python
from pylstemp.workflows import scene_ndvi_range

with LandsatScene("caminho/para/cena") as cena:
    limites = scene_ndvi_range(cena, optical_quantity="radiance")
    resultado = du_from_scene(cena, window=(3000, 3128, 3000, 3128),
                             pwv_mode="raster", ndvi_range=limites)
```

Sem `ndvi_range`, o workflow calcula extremos de NDVI dos pixels de terra
validos da cena completa em faixas de 256 linhas. O scan usa QA/BT validas;
a mascara opcional do usuario remove amostras depois dessa definicao global
dos grupos. Reutilize limites da mesma cena e convencao optica.
Limites fornecidos sao registrados como declaracao do chamador e precisam
conter o NDVI local. O workflow nao consegue demonstrar que representam toda
a cena. `mask`, quando fornecida, deve ser booleana e cobrir a cena inteira;
True remove o pixel central e sua contribuicao a janelas vizinhas.

O halo automatico tem `window_size // 2` pixels, limitado pelas bordas reais
da cena. Ausencia de amostras externas nas bordas nao cria dados artificiais.
O modo raster com os mesmos limites globais reproduz o processamento inteiro;
o modo media varia com a area escolhida para a media.

## Produtos e proveniencia

`DuSceneResult` contem `lst`, `pwv` (raster aceito), `pwv_raw`, `invalid_mask`,
`window` e `provenance`. No modo media, `pwv` ainda e o raster que originou a
media; o valor efetivamente utilizado esta em `provenance["mean_pwv"]`.
No modo geral os dois campos PWV sao None.

`export()` grava LST, mascara LST (1=invalido), PWV bruto/aceito, mascara PWV
e `provenance.json`. Os rasters preservam grade, unidades e NoData NaN.
O JSON registra cena, sensor, versao, modo, estimador, selecao de coeficientes,
convencao optica, janela/halo, grupos NDVI e contagens de rejeicao. Exportar
usando a mesma cena aberta que originou o resultado.

## Pendencia cientifica da cadeia original

Esta entrega implementa **Wang -> Du**, uma cadeia alternativa. Ela nao
reproduz integralmente o procedimento atmosferico do artigo de Du.

Du, secao 3.3, p.655, Eq.3a, imprime `c0 + c1*r + c2*r^2` e atribui no texto
`c0=-9.674`, `c1=0.653`, `c2=9.087`. Para `r=0.8`, a leitura literal resulta
em PWV negativo. A discussao de Ren, secao 2, apresenta termo quadratico
negativo na analise de diferencas; portanto, a ordem nao pode ser copiada
silenciosamente nem corrigida por plausibilidade numerica.

O texto completo HTML de [Ren (2015)](https://agupubs.onlinelibrary.wiley.com/doi/10.1002/2014JD022619)
foi consultado, mas as imagens das Eqs.1b/1c/2 e o PDF nao ficaram acessiveis
nesta rodada (HTTP 403/erro de acesso). A pagina de Du retornou HTTP 429;
a secao relevante foi conferida no PDF local, inclusive visualmente.
Nao foi localizada correcao especifica para essa ordem na pesquisa efetuada;
isso nao prova a inexistencia de errata.

Ren recomenda janela 10 no suporte TIRS nativo e descreve filtro NDVI local
na aplicacao (secao 4.2); isso exige decidir explicitamente como tratar a
reamostragem termica a 30 m dos produtos Landsat e como transferir o suporte
espacial. Esses procedimentos nao foram substituidos pelos parametros de Wang.

Para concluir a entrega B, ainda e necessario conferir visualmente as equacoes
originais de Ren, resolver a ordem dos coeficientes e registrar janela/suporte,
filtros, limiar de qualidade e dominio adotados. Nao existe chave `ren-2015`
nesta versao. A entrega C esta disponivel para Wang; a selecao do estimador
original depende dessa auditoria. A versao permanece 1.11.0 em preparacao.

Veja [verificacoes desta alteracao](validation.md).
