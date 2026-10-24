# Du com PWV raster e workflow de cena

O workflow conecta calibracao, PWV e Du sem duplicar entradas do catalogo.
Aceita Wang e Ren/MSWCVR, com escolha explicita do estimador.

`split_window(..., lst_method="du-2015", water_vapor=None)` preserva os
coeficientes gerais. PWV escalar exige valor finito em [0,6.3] g/cm2. Raster
exige exatamente a mesma forma e grade das BT e emissividades; nao ha
broadcasting. Valores nao finitos ou fora do dominio ficam NaN, sem clipping
ou substituicao pelo conjunto geral. Os limites das faixas sao inclusivos;
as sobreposicoes usam a media das LSTs dos conjuntos aplicaveis.

## Execucao a partir de uma cena

```python
from pylstemp.scene import LandsatScene
from pylstemp.workflows import du_from_scene

with LandsatScene("caminho/para/cena") as cena:
    resultado = du_from_scene(
        cena, pwv_mode="raster", pwv_method="ren-2015", unit="celsius",
    )
    resultado.export(cena, "resultados/du_ren")
```

A chamada cobre a cena inteira. Para limitar tempo e memoria, `window`
aceita um recorte `(linha_inicial, linha_final, coluna_inicial, coluna_final)`,
com limites finais exclusivos. O workflow calcula o halo automaticamente.
`chunk_rows` limita temporarios dos estimadores, mas os arrays de entrada
e saida ainda ocupam memoria proporcional a area solicitada. O README usa
a chamada Du geral mais simples, que nao calcula PWV.

Modos `pwv_mode`:

- `general`: nao calcula PWV; usa o conjunto geral de Du e QA convencional.
- `mean`: estima PWV, conserva pixels aceitos e calcula a media **da janela
  de saida**. Essa media seleciona os coeficientes para todos os pixels com
  entradas validas. Sem amostras, gera erro.
- `raster`: estima PWV e seleciona os coeficientes localmente, preservando
  lacunas de PWV como lacunas de LST.

Os modos atmosfericos excluem agua por QA, alem das exclusoes convencionais.
O modo geral pode incluir agua; compare os resultados sobre suporte comum.
Media e raster nao sao numericamente equivalentes. As medias dos dois
estimadores usam seus proprios pixels aceitos; uma comparacao controlada
sobre suporte identico exige preparar esse suporte explicitamente.

## Estimadores e parametros

O padrao continua `pwv_method="wang-2015"`. A escolha Ren e explicita:

| Escolha | Janela padrao no workflow | Selecao NDVI | PWV aceito no workflow |
|---|---|---|---|
| `wang-2015` | 21 pixels | 3 grupos globais | [0.066,6.3] g/cm2 |
| `ren-2015` | 33 pixels | filtro local +/-1.5 sigma | [0.06,6.3] g/cm2 |

O limite inferior de Wang vem do TIGR3 adotado nas verificacoes e o superior
de Du. O dominio Ren vem dos perfis de calibracao do proprio estimador.
Os 33 pixels Ren aproximam 1 km na grade usual de entrega de 30 m; nao
criam observacoes termicas independentes de 30 m. O artigo usa n=10 no
suporte TIRS nativo de 100 m. As janelas centradas impares e sua transferencia
para a grade de entrega sao adaptacoes declaradas. Em outra grade, ajuste
`window_size`. A API isolada `water_vapor` usa 11 para Ren quando a janela
nao e fornecida; o workflow usa 33 por conhecer o contexto Landsat.

`pwv_options`, apenas para Ren, permite `min_samples` (padrao 10),
`quality_threshold` (0.95) e `ndvi_filter` (True). Estes limiares sao escolhas
operacionais. Os demais controles sao `window_size`, `chunk_rows`, `mask`,
`emissivity_method`, `optical_quantity` e `unit`. Ren rejeita `ndvi_range`
e `group_count` diferente de 3, pois nao usa agrupamento global. Wang rejeita
`pwv_options`. Veja [formulas e criterios](image-only-methods.md#ren-2015-mswcvr).

## Blocos e mascara do usuario

Wang depende de limites NDVI da cena, que podem ser calculados uma vez:

```python
from pylstemp.workflows import scene_ndvi_range

with LandsatScene("caminho/para/cena") as cena:
    limites = scene_ndvi_range(cena, optical_quantity="radiance")
    resultado = du_from_scene(cena, window=(3000, 3128, 3000, 3128),
                             pwv_mode="raster", pwv_method="wang-2015",
                             ndvi_range=limites)
```

Sem `ndvi_range`, Wang calcula os extremos dos pixels de terra validos da
cena em faixas de 256 linhas. O scan usa QA/BT validas; a mascara do usuario
remove amostras depois da definicao global dos grupos. Reutilize limites da
mesma cena e convencao optica. Limites fornecidos sao registrados como
declaracao do chamador; a API nao comprova que representam a cena inteira.
Ren usa apenas a vizinhanca local e nao faz esse scan.

`mask` deve ser booleana e cobrir a cena inteira; True remove o pixel
central e sua contribuicao a janelas vizinhas. O halo tem
`window_size // 2` pixels, limitado pelas bordas reais. Nao se criam
amostras artificiais nas bordas. Raster com mesmo suporte e parametros
reproduz o processamento inteiro; para Wang, mantenha tambem os mesmos
limites globais. O modo media varia com a area escolhida para a media.

## Produtos e proveniencia

`DuSceneResult` contem `lst`, `pwv` (raster aceito), `pwv_raw`,
`invalid_mask`, `window`, `provenance` e `pwv_diagnostics` (Ren).
No modo media, `pwv` ainda e o raster que originou a media; o valor aplicado
esta em `provenance["mean_pwv"]`. No modo geral os campos PWV sao None.
O PWV bruto preserva valores calculaveis antes dos filtros de qualidade e
dominio; ele nao deve substituir automaticamente o PWV aceito na LST.

`export()` grava `lst_du.tif`, `lst_invalid.tif` (1=invalido), `pwv.tif`,
`pwv_raw.tif`, `pwv_invalid.tif` e `provenance.json`.
Ren acrescenta `pwv_ratio.tif`, `pwv_chi_squared.tif` e
`pwv_sample_count.tif`; o modo geral exporta somente LST, mascara e JSON.
Os GeoTIFFs preservam grade, unidades e NoData NaN. O JSON registra cena,
sensor, versao, modo, estimador, selecao de coeficientes, convencao optica,
janela/halo, limites globais de Wang ou controles locais de Ren e rejeicoes.
Use a mesma cena aberta que originou o resultado para exportar.

## Equacoes verificadas e alcance da cadeia

O PDF original de Ren foi conferido, incluindo Eqs.1b/1c/2. A Eq.2 fixa
`PWV = -9.674*Rji**2 + 0.653*Rji + 9.087`. Ela e a fonte da regressao,
sem copiar a ordem contraditoria dos coeficientes no texto de Du.
Ren/MSWCVR -> Du fica disponivel, mantendo Wang -> Du como alternativa.

Isso verifica as equacoes e o funcionamento; nao demonstra acuracia absoluta
com observacoes externas. Janela reamostrada, controles operacionais e
emissividade Rongali sao escolhas registradas, sem alegar reproducao integral
do experimento original. Transferir coeficientes Landsat 8 para Landsat 9
permanece experimental. Veja [validacao](validation.md) e [fontes](references.md).

## Intermediarios e rastreabilidade opcionais

Use `du_from_scene(scene, diagnostics=True)` para manter as bandas opticas
calibradas, BT10/BT11, NDVI interno e emissividades em `result.intermediates`.
`result.export(scene, pasta)` grava esses sete GeoTIFFs com a mesma janela,
projecao e origem da LST. Sem essa opcao, os produtos anteriores sao preservados.
O JSON inclui coeficientes MTL, grade, versoes, hash do codigo e das fichas,
politica QA, mascara e condicoes dos metodos selecionados. `hash_inputs=True`
registra tambem SHA256 de todas as imagens; por padrao, tamanho/data identificam
os arquivos de imagem sem comprovar identidade do conteudo. A conferencia do
MTL por SHA256 e sempre feita. Artigos e dados locais nao sao publicados.
