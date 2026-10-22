# Exemplos com imagens Landsat

Instale na raiz: `pip install -e ".[examples]"`.

Use uma pasta Landsat 8 ou 9 Collection 2 Level-1 com **B4, B5, B10, B11,
MTL.txt, QA_PIXEL e QA_RADSAT**. Preserve os nomes originais. B2 e opcional;
SZA e utilizado quando presente. Todas as bandas precisam estar alinhadas.

## Executar o fluxo completo

```bash
python exemples/fluxo_completo.py "D:/dados/LC08_CENA" --saida resultados
```

Substitua o caminho pela pasta da imagem. Nove GeoTIFFs sao salvos: BT10,
BT11, emissividade10/11, LST Avdan, LST Du, PWV Wang, LST Jimenez SC e
LST Jimenez SW.
Os nomes incluem o identificador da cena para separar Landsat 8 e Landsat 9.

## Notebooks

Abra o notebook desejado, altere `pasta` na primeira celula e execute:

- `brightness.ipynb`: DN B10/B11 -> radiancia TOA -> BT em K.
- `emissivity.ipynb`: B4/B5 -> NDVI interno -> emissividade B10/B11.
- `single_window.ipynb`: BT10 + B4/B5 -> LST em C.
- `split_window.ipynb`: Du e Jimenez; Jimenez recebe PWV calculado por Wang.
- `water_vapor.ipynb`: BT10/BT11 + B4/B5 -> PWV bruto em g/cm2.

Os exemplos leem arquivos de imagem e nao criam matrizes artificiais. O recorte
central de ate 256 x 256 pixels e tratado como uma imagem de demonstracao.
Em um mosaico, Wang precisa de halo e grupos globais de NDVI. Confira limites
cientificos em [scientific-methods.md](../docs/scientific-methods.md).

O notebook single_window compara Avdan e Jimenez-Munoz SC. O SC usa radiancia10
e PWV, com restricao operacional 0..3 g/cm2.


## Rozenstein, Sobrino e Chavez

```bash
python exemples/metodos_imagem.py CAMINHO_DA_CENA --perfil midlatitude-summer --saida resultados/metodos
```

O exemplo usa imagens reais em um recorte central controlado, com halo de Wang,
COST e emissividade Sobrino 2008 com endmembers declarados. O perfil e escolhido
explicitamente e a parametrizacao Chavez pertence ao recorte. Veja
[dominios e adaptacoes](../docs/image-only-methods.md).

Para Ren, use `water_vapor(..., method="ren-2015")` ou o
[workflow Du com Wang/Ren](../docs/du-pwv-workflow.md). O fluxo completo
acima continua usando Wang explicitamente; selecionar outro metodo exige
registrar a configuracao e aplicar o dominio da equacao LST.
