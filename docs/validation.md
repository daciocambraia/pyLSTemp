# Verificacao atual

## Escopo

A versao 2.0.0 fornece seis familias de calculo. O catalogo de metodos tem
14 entradas identificadas por familia e metodo, com 16 fichas cientificas.
Os 17 notebooks incluem as conversoes de calibracao e o exemplo de mascara QA.
Dados de campo, manuscritos e cenarios de pesquisas especificas nao integram
a biblioteca, seus testes ou os pacotes.

## Ultima verificacao local

Em 2026-11-05 passaram 91 testes e 134 subtestes, incluindo os 17 notebooks.
Wheel/sdist passaram em build e Twine; a suite completa passou tambem contra
o wheel instalado em ambiente separado. Equacoes, coeficientes e hashes das
16 fontes permaneceram iguais aos registros anteriores da implementacao.
A matriz remota de CI deve estar aprovada no commit/tag publicado.

## O que a suite verifica

- Equacoes e coeficientes contra referencias numericas sinteticas independentes.
- Contratos de entrada: formas, mascaras booleanas, bandas, unidades declaradas,
  parametros incompat?veis e valores ausentes/nao finitos.
- Nomes de metodos e correspondencia das fichas por `(family, method)`.
- Preservacao dos resultados filtrados padrao e separacao dos resultados brutos.
- Propagacao de flags PWV/LST, dominios e medias espaciais explicitas.
- Encadeamento por cenas e igualdade de resultados por blocos com halo.
- Exportacao Rasterio/Pillow, origem de recortes, uint8/uint16, nodata e metadados.
- Execucao dos 17 notebooks com pequenos GeoTIFFs, MTL e QA sinteticos.
- Imports, cobertura da API no README, chamadas documentadas e links locais.

A CI executa esses testes contra o wheel instalado em Windows e Linux, com
Python 3.9, 3.11 e 3.14. Os testes de GeoTIFF exigem o extra `dev`.

```bash
python -m pip install -e ".[dev]"
python -m pytest tests -q
python -m build --outdir ../dist-pylstemp
python -m twine check ../dist-pylstemp/*
```

Os pacotes devem ser instalados em ambiente separado e testados com
`python -I -m pytest --import-mode=importlib tests -q`, evitando importar
acidentalmente a arvore de fontes em vez do wheel.

## Limites da verificacao

Passar nos testes comprova os contratos numericos exercitados; nao comprova
acuracia de campo, equivalencia entre convencoes opticas ou validade de
transferir coeficientes entre sensores. As fichas registram as fontes,
hipoteses e limites de cada metodo. Valores brutos extrapolados exigem
interpretacao das flags, mesmo quando finitos.

Veja [contratos de resultados](result-contracts.md), [diagnosticos](diagnostic-quality.md)
e [fichas cientificas](method-cards.md). O historico de desenvolvimento e
identificado pelo Git e pelo [changelog](../CHANGELOG.md), sem substituir
esta descricao vigente.
