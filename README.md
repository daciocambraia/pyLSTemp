# pyLSTemp

[![CI](https://github.com/daciocambraia/pyLSTemp/actions/workflows/ci.yml/badge.svg)](https://github.com/daciocambraia/pyLSTemp/actions/workflows/ci.yml)
[![License](https://img.shields.io/badge/license-Apache%202.0-blue.svg)](LICENSE)

Biblioteca Python para calcular temperatura da superficie com imagens
**Landsat 8 e Landsat 9 Level-1**. Versao em preparacao: **1.11.0**.

## Instalar

```bash
pip install -e ".[examples]"
```

## Abrir a imagem e calcular LST

A pasta deve conter B4, B5, B10, B11, MTL.txt, QA_PIXEL e QA_RADSAT,
com os nomes originais do produto. B2 e opcional.

```python
from pylstemp.scene import LandsatScene
from pylstemp import single_window

with LandsatScene("caminho/para/cena_landsat") as cena:
    janela = (3000, 3256, 3000, 3256)  # recorte; ajuste a sua imagem
    bandas, temperatura, mascara = cena.calibrated(janela)
    lst = single_window(temperatura[10], bandas[4], bandas[5],
                        unit="celsius", mask=mascara)
    cena.write_geotiff("lst_single.tif", lst, window=janela, units="celsius")
```

`calibrated` le as bandas, converte DN usando o MTL e aplica QA.
B4/B5 saem em **radiancia TOA**; B10/B11 saem em **temperatura de brilho TOA (K)**.
`single_window` calcula a emissividade a partir do NDVI e entrega **LST em C**.
O GeoTIFF conserva as coordenadas do recorte.

## Fluxo completo e exemplos

```bash
python exemples/fluxo_completo.py CAMINHO_DA_CENA --saida resultados
```

Esse exemplo conecta imagens, NDVI, emissividade, BT, LST single-channel,
LST split-window e vapor d'agua, salvando nove GeoTIFFs de um recorte central.
Ha tambem seis notebooks, um por modulo. Altere o caminho da pasta e execute.

- [Guia de uso com imagens](docs/usage.md)
- [Dados e notebooks](exemples/DATA.md)
- [Referencia da API](docs/api-reference.md)

## Modulos e grandezas

| Etapa | Funcoes | Resultado |
|---|---|---|
| Calibracao | `toa_radiance`, `toa_reflectance`, `brightness` | Radiancia, reflectancia ou BT |
| Indice espectral | `spectral_index("ndvi")` | NDVI |
| Emissividade | `emissivity` | Emissividade B10/B11 |
| Temperatura da superficie | `single_window`, `split_window` | LST em K ou C |
| Vapor d'agua | `water_vapor` | PWV em g/cm2 |
| Catalogo | `list_algorithms` | Metodos e requisitos |

O padrao e radiancia TOA em W m-2 sr-1 um-1. `brightness` recebe radiancia e
retorna BT em K; entradas DN exigem `input_quantity="dn"`. Reflectancia TOA
fica disponivel explicitamente por `toa_reflectance` ou
`calibrated(optical_quantity="reflectance")`.

## Validacao e limites cientificos

Os metodos foram exercitados nas duas cenas fornecidas, com referencias
numericas independentes. Calibracao radiometrica usa o MTL de cada sensor;
transferencia dos coeficientes de recuperacao para Landsat 9 e experimental.
NDVI em radiancia e reflectancia pode diferir; os limiares de emissividade
precisam ser justificados para a convencao usada. Nao ha validacao independente
de acuracia de LST/PWV. Price/Kerr/Sobrino sao adaptacoes historicas de AVHRR.

- [Validacao atual](docs/validation.md)
- [Metodos cientificos e migracao](docs/scientific-methods.md)
- [Melhorias ainda relevantes](docs/MELHORIAS_MODULOS_v1.11.md)
- [Indice da documentacao](docs/index.md)

## Desenvolvimento

```bash
pip install -e ".[dev,examples]"
python -m pytest
python -m build
```

Codigo em `pylstemp/`, testes em `tests/` e verificadores em `scripts/`.
Resultados e historico local ficam em `Verificacao/`; imagens e historico
nao sao distribuidos com a biblioteca.

## Creditos

Projeto: <https://github.com/daciocambraia/pyLSTemp>.
Biblioteca original: **pylandtemp**, de **Oladimeji Mudele**.
Veja [CREDITS.md](CREDITS.md) e [referencias](docs/references.md).
