# Instalacao

## Requisitos

Python 3.9+ e pip. Os exemplos de imagens usam rasterio e Pillow.

## Instalar esta versao local

Na raiz da v1.11:

```bash
python -m pip install -e ".[examples]"
python -c "import pylstemp; print(pylstemp.__file__)"
```

Confira se o caminho impresso aponta para esta copia. A v1.11.0 esta em
preparacao; uma instalacao pelo indice de pacotes pode nao conter este codigo.
Os pacotes locais preparados ficam em dist/.

## Instalar para desenvolvimento

```bash
python -m pip install -e ".[dev,examples]"
python -m build
```

## Preparar as imagens

Use uma pasta Landsat 8/9 Level-1 por cena com B4, B5, B10, B11, MTL,
QA_PIXEL e QA_RADSAT, mantendo os nomes originais e a mesma grade.
Veja [dados dos exemplos](../exemple/README.md) e [guia de uso](usage.md).
