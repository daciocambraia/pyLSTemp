# Selecao uniforme por method

Cada familia possui um unico seletor de algoritmo: `method=`.

| Familia | Exemplos de method | Padrao |
| --- | --- | --- |
| `calibrate` | `toa-radiance`, `toa-reflectance`, `brightness` | Obrigatorio |
| `emissivity` | `avdan-2016`, `rongali-2018` | Avdan |
| `single_window` | `avdan-2016`, `jimenez-munoz-2014` | Avdan |
| `split_window` | `du-2015`, `jimenez-munoz-2014`, `price-1984`, `kerr-1992`, `sobrino-1993` | Obrigatorio |
| `water_vapor` | `wang-2015`, `ren-2015` | Wang |
| `optical_correction` | `chavez-dos-1996`, `chavez-cost-1996` | COST |

## Cadeias com varios metodos

Selecione cada metodo em sua propria familia; passe os resultados a proxima etapa.

```python
from pylstemp import calibrate, emissivity, single_window

radiancia10 = calibrate(dn10, method="toa-radiance", metadata=metadata,
                        band=10, mask=mascara)
bt10 = calibrate(radiancia10, method="brightness", metadata=metadata,
                 band=10, mask=mascara)
e10 = emissivity(red=red, nir=nir, method="rongali-2018", band=10, mask=mascara)
lst = single_window(bt10, method="jimenez-munoz-2014", emissivity_10=e10,
                     radiance_band_10=radiancia10, water_vapor=1.5, mask=mascara)
```

As variaveis representam matrizes na mesma grade. Metadados, unidades,
mascaras QA e a convencao radiometrica de red/nir devem corresponder aos dados.
O PWV 1.5 g/cm2 acima e apenas ilustrativo: usar uma estimativa justificada.
A rota LST por bandas continua disponivel: Avdan fixo em `single_window`,
Rongali fixo em `split_window`. Para mudar a emissividade, use a etapa separada.

## Migracao

- Trocar `lst_method=` por `method=` nas funcoes LST.
- Trocar `emissivity_method=` por `method=` na funcao `emissivity`.
- Retirar `emissivity_method=` das funcoes LST. Se era diferente do modelo
  automatico, calcular a emissividade separadamente e fornecer `emissivity_10`
  e, no split-window, `emissivity_11`.
- No workflow `du_from_scene`, trocar `pwv_method=` por `method=`. Esse seletor
  escolhe Wang/Ren para PWV; a composicao usa Du e Rongali fixos. Outras
  composicoes devem chamar as familias diretamente.

Os nomes antigos nao sao aliases: chamadas com esses argumentos geram TypeError.
Os campos descritivos de proveniencia continuam identificando os metodos de cada
etapa; nao sao argumentos alternativos da API. As funcoes diretas de calibracao
continuam disponiveis como conversoes individuais.

## Identidade por familia e metodo

A funcao informa a operacao: `emissivity(method="avdan-2016")` calcula
emissividade; `single_window(method="avdan-2016")` calcula LST.
`single_window(method="jimenez-munoz-2014")` usa SC e
`split_window(method="jimenez-munoz-2014")` usa SW. Dos dois modelos Chavez
na mesma familia, DOS/COST permanece no seletor: `chavez-dos-1996` e
`chavez-cost-1996`.

| Seletor anterior | Familia | Seletor atual |
| --- | --- | --- |
| `mono-window-2016` | `single_window` | `avdan-2016` |
| `jimenez-munoz-2014-sc` / `jimenez-munoz-sc-2014` | `single_window` | `jimenez-munoz-2014` |
| `jimenez-munoz-2014-sw` | `split_window` | `jimenez-munoz-2014` |
| `chavez-dos` | `optical_correction` | `chavez-dos-1996` |
| `chavez-cost` | `optical_correction` | `chavez-cost-1996` |

Os seletores antigos foram retirados. O catalogo continua com 14 entradas
por familia/metodo; alguns seletores textuais aparecem em mais de uma familia.
As 16 fichas cientificas sao identificadas por `(family, method)`.
A proveniencia de cenas usa schema 2 e `source_method_cards[family][method]`.

## Migracao para 2.0.0

As mudancas de seletores e nomes sao incompat?veis; a versao 2.0.0 as identifica
explicitamente. return_diagnostics=True agora e aceito nas seis familias.
Wang e Ren fornecem os mesmos campos comuns de identidade e bruto/filtrado.
No workflow, pwv_raw conserva o estimador matematico, e pwv_screened aplica
o filtro completo da cadeia. Exportacoes de flags/mascaras usam tipos inteiros.
Veja [contratos](result-contracts.md) para migrar leitores dos dicionarios e arquivos.
