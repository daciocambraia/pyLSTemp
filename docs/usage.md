# Uso com imagens Landsat

Instale a biblioteca com `pip install -e ".[examples]"`. Os exemplos usam uma
pasta Landsat 8 ou 9 Collection 2 Level-1, com os nomes originais dos arquivos:
B4, B5, B10, B11, MTL.txt, QA_PIXEL e QA_RADSAT. B2 e opcional; SZA e usado
quando esta presente. As imagens devem ter a mesma grade.

## 1. Escolha a pasta e o destino

```python
from pathlib import Path
from pylstemp.scene import LandsatScene
from pylstemp import spectral_index, emissivity, single_window, split_window, water_vapor

pasta = Path("caminho/para/cena_landsat")
saida = Path("resultados")
saida.mkdir(parents=True, exist_ok=True)
```

Troque somente `pasta` pelo caminho da cena baixada. O mesmo codigo funciona
com Landsat 8 e Landsat 9; o sensor e os coeficientes sao lidos do MTL.

## 2. Abra as imagens e associe as funcoes

O recorte central de ate 256 x 256 pixels deixa o exemplo rapido. `calibrated`
le as bandas, usa os coeficientes do MTL, aplica QA e entrega radiancia TOA e
BT em kelvin. Aqui a mascara tambem exclui agua, pois Wang e aplicado sobre terra.

```python
with LandsatScene(pasta) as cena:
    altura, largura = cena.shape
    linha = max(0, altura // 2 - 128)
    coluna = max(0, largura // 2 - 128)
    janela = (linha, min(altura, linha + 256), coluna, min(largura, coluna + 256))
    bandas, temperatura, mascara = cena.calibrated(janela, exclude_water=True)
    vermelho, infravermelho = bandas[4], bandas[5]
    bt10, bt11 = temperatura[10], temperatura[11]

    ndvi = spectral_index("ndvi", nir=infravermelho, red=vermelho, mask=mascara)
    emissividade = emissivity(ndvi, band=10, emissivity_method="gopinadh-2018")
    lst_single = single_window(bt10, vermelho, infravermelho,
                               unit="celsius", mask=mascara)
    lst_du = split_window(bt10, bt11, vermelho, infravermelho,
                          lst_method="du-2015", unit="celsius", mask=mascara)
    pwv = water_vapor(bt10, bt11, ndvi, mask=mascara)
    mascara_pwv = mascara | (pwv < 0.066) | (pwv > 7.833)
    lst_jimenez = split_window(bt10, bt11, vermelho, infravermelho,
                               lst_method="jimenez-munoz-2014", water_vapor=pwv,
                               unit="celsius", mask=mascara_pwv)

    cena.write_geotiff(saida / "ndvi.tif", ndvi, window=janela, units="dimensionless")
    cena.write_geotiff(saida / "emissividade.tif", emissividade, window=janela, units="dimensionless")
    cena.write_geotiff(saida / "lst_single.tif", lst_single, window=janela, units="celsius")
    cena.write_geotiff(saida / "lst_du.tif", lst_du, window=janela, units="celsius")
    cena.write_geotiff(saida / "pwv.tif", pwv, window=janela, units="g/cm2")
    cena.write_geotiff(saida / "lst_jimenez.tif", lst_jimenez, window=janela, units="celsius")
```

As funcoes LST calculam a emissividade internamente a partir do NDVI. O exemplo
separado de `emissivity` serve para visualizar ou exportar essa grandeza.
Du funciona sem PWV; Jimenez recebe o raster calculado por Wang. O PWV bruto e
salvo, e a mascara de referencia 0.066..7.833 g/cm2 e aplicada apenas ao LST Jimenez.

## 3. Calibracao explicita de uma banda

Para acompanhar DN -> radiancia TOA -> temperatura de brilho, abra a banda 10:

```python
from pylstemp import toa_radiance, brightness

with LandsatScene(pasta) as cena:
    _, _, mascara = cena.calibrated(janela)
    dn10 = cena.read("B10", janela)
    radiancia10 = toa_radiance(dn10, metadata=cena.metadata, band=10, mask=mascara)
    bt10 = brightness(radiancia10, band=10, metadata=cena.metadata, mask=mascara)
    cena.write_geotiff(saida / "bt10.tif", bt10, window=janela, units="kelvin")
```

A banda 11 segue os mesmos passos, com `B11` e `band=11`.
Radiancia usa W m-2 sr-1 um-1; BT usa K. BT e temperatura de brilho TOA.
`single_window` e `split_window` recebem BT em K e devolvem LST na unidade escolhida.

## 4. Reflectancia TOA opcional

```python
with LandsatScene(pasta) as cena:
    reflectancia, _, _ = cena.calibrated(janela, optical_quantity="reflectance")
    cena.write_geotiff(saida / "reflectancia_b4.tif", reflectancia[4],
                       window=janela, units="dimensionless")
```

Esse modo utiliza `toa_reflectance` com correcao solar por SZA ou pelo MTL.
O fluxo principal acima continua em radiancia. Reflectancia TOA e SR Level-2
sao grandezas distintas; NDVI e limiares de emissividade dependem da convencao adotada.

## 5. Executar o exemplo pronto

Na raiz do projeto:

```bash
python exemples/fluxo_completo.py CAMINHO_DA_CENA --saida resultados
```

O script salva nove GeoTIFFs com coordenadas, unidade e NoData. Os seis
notebooks em [exemples](../exemples/DATA.md) mostram cada modulo individualmente.
Ajuste a pasta na primeira celula e execute; nenhum exemplo cria bandas artificiais.

O recorte e tratado como a imagem de demonstracao. PWV em mosaicos ou tiles de
uma cena maior requer halo e grupos globais de NDVI, conforme
[scientific-methods.md](scientific-methods.md). Os resultados nao representam
validacao independente de acuracia; coeficientes de recuperacao Landsat 9 seguem experimentais.
