# Instalacao

## Requisitos

Python 3.9+ e pip. Os exemplos de imagens usam rasterio e Pillow.

## Instalar esta versao local

Na raiz do repositorio:

```bash
python -m pip install -e ".[examples]"
python -c "import pylstemp; print(pylstemp.__file__)"
```

Confira se o caminho impresso aponta para esta copia e se `pylstemp.__version__`
corresponde a 2.0.0. Um commit/tag no GitHub nao publica automaticamente no PyPI.
Mantenha ambientes virtuais e distribuicoes geradas fora da pasta de fontes.

## Instalar para desenvolvimento

```bash
python -m pip install -e ".[dev,examples]"
python -m pytest tests -q
python -m build --outdir ../dist-pylstemp
```

## Preparar as imagens

Use uma pasta Landsat 8/9 Level-1 por cena com B4, B5, B10, B11, MTL,
QA_PIXEL e QA_RADSAT, mantendo os nomes originais e a mesma grade.
Veja [dados dos exemplos](../exemple/README.md) e [guia de uso](usage.md).


QA_PIXEL e QA_RADSAT são obrigatórias no leitor por pasta: a cena não abre sem elas. Os arquivos devem pertencer ao mesmo produto e manter a grade e os nomes originais. As funções com matrizes já carregadas não leem QA automaticamente; o chamador prepara e fornece mask quando aplica essa seleção.

Nos exemplos por arquivos preparados, informe também `qa_pixel_path` e `qa_radsat_path`. A função pública `quality_mask(..., reference_path=...)` exige as duas QA e verifica a grade. Consulte [onde aplicar QA em cada método](quality-inputs.md).
