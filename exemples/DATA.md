# Exemplos com imagens Landsat

Instale na raiz: `pip install -e ".[examples]"`.

Use uma pasta Landsat 8 ou 9 Collection 2 Level-1 com **B4, B5, B10, B11,
MTL.txt, QA_PIXEL e QA_RADSAT**. Preserve os nomes originais. B2 e opcional;
SZA e utilizado quando presente. Todas as bandas precisam estar alinhadas.

## Executar o fluxo completo

```bash
python exemples/fluxo_completo.py "D:/dados/LC08_CENA" --saida resultados
```

Substitua o caminho pela pasta da imagem. Nove GeoTIFFs sao salvos: NDVI, BT10,
BT11, emissividade10/11, LST single-channel, LST Du, PWV e LST Jimenez.
Os nomes incluem o identificador da cena para separar Landsat 8 e Landsat 9.

## Notebooks

Abra o notebook desejado, altere `pasta` na primeira celula e execute:

- `spectral_index.ipynb`: imagens B4/B5 -> NDVI.
- `brightness.ipynb`: DN B10/B11 -> radiancia TOA -> BT em K.
- `emissivity.ipynb`: NDVI -> emissividade B10/B11.
- `single_window.ipynb`: BT10 + B4/B5 -> LST em C.
- `split_window.ipynb`: Du e Jimenez; Jimenez recebe PWV calculado por Wang.
- `water_vapor.ipynb`: BT10/BT11 + NDVI -> PWV bruto em g/cm2.

Os exemplos leem arquivos de imagem e nao criam matrizes artificiais. O recorte
central de ate 256 x 256 pixels e tratado como uma imagem de demonstracao.
Em um mosaico, Wang precisa de halo e grupos globais de NDVI. Confira limites
cientificos em [scientific-methods.md](../docs/scientific-methods.md).
