# Calibracao radiometrica

O pacote `pylstemp.calibration` agrupa as conversoes em modulos separados.
A funcao publica `calibrate(data, *, method, return_diagnostics=False, **kwargs)` seleciona a conversao;
o argumento `method` e obrigatorio.

| method | Entrada | Saida | Outros argumentos |
| --- | --- | --- | --- |
| `toa-radiance` | DN Level-1 | Radiancia TOA, W m-2 sr-1 um-1 | `metadata`, `band` (1..11), `mask` |
| `toa-reflectance` | DN optico Level-1 | Reflectancia TOA, adimensional | `metadata`, `band` (1..9), `mask`, `sun_elevation` opcional |
| `brightness` | Radiancia termica TOA | Temperatura de brilho TOA, K | `band` (10/11), `metadata` ou `sensor`, `mask` |

```python
from pylstemp import calibrate, read_mtl, quality_mask

metadata = read_mtl("cena_MTL.txt")
mascara = quality_mask("cena_QA_PIXEL.TIF", "cena_QA_RADSAT.TIF",
                            reference_path="cena_B10.TIF")
# dn10 e a banda B10 carregada na mesma grade; combinar nodata com mascara.
radiancia = calibrate(dn10, method="toa-radiance", metadata=metadata,
                      band=10, mask=mascara)
bt10 = calibrate(radiancia, method="brightness", metadata=metadata,
                 band=10, mask=mascara)
```

Para converter DN termico diretamente, use `method="brightness"` com
`input_quantity="dn"`. Radiancia e o padrao: nao aplicar ganho/offset novamente.
Reflectancia TOA nao equivale a reflectancia superficial; BT nao equivale a LST.
As convencoes e equacoes das funcoes diretas permanecem iguais.

## Compatibilidade e auxiliares

`from pylstemp import toa_radiance, toa_reflectance, brightness` e os imports
das conversoes numericas de `pylstemp.calibration` continuam funcionando. A pasta chama-se
`calibration`; a funcao chama-se `calibrate` para preservar o namespace do pacote.

`read_mtl` le os metadados. A funcao publica `quality_mask` le os arquivos QA;
a decodificacao de matrizes fica interna em `_quality_mask_from_arrays`. `surface_reflectance` apenas escala
produtos SR Level-2 ja existentes; esses auxiliares nao sao seletores de
calibracao Level-1. `brightness_from_mtl` preserva a chamada historica por DN.
O catalogo `list_algorithms()` mantem seus 14 seletores; a nova interface
agrupa conversoes ja existentes e nao acrescenta metodos cientificos.

## Exemplos executaveis

- [Radiancia TOA](../exemple/calibrate__toa-radiance.ipynb)
- [Reflectancia TOA](../exemple/calibrate__toa-reflectance.ipynb)
- [Temperatura de brilho](../exemple/calibrate__brightness.ipynb)

return_diagnostics=True inclui result, unidades, familia/metodo e metadados
do processamento. O retorno padrao continua sendo uma matriz.
