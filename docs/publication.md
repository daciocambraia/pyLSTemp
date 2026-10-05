# Preparacao para publicacao

## Conteudo da versao

v1.11.0 contem 12 algoritmos. RTE nao foi acrescentada.
[Arquitetura](architecture.md) lista arquivos, funcoes de calibracao e familias.

Git inclui biblioteca, documentacao, exemplos, testes, scripts, licenca,
creditos, contribuicao e workflows. Wheel instala apenas pylstemp e metadados
(incluindo a licenca). Sdist inclui ainda docs, exemplos, testes e scripts.
Imagens reais, artigos, resultados locais, .git, build e caches ficam fora.

## Verificacao local

```bash
python -m pip install -e ".[dev,examples]" twine
python -m pytest
python -m build
python -m twine check dist/*
git diff --check
git status --short
```

Confira que pyproject.toml e pylstemp.__version__ indicam 1.11.0 e que a tag
pretendida e v1.11.0. As dependencias de exemplos sao opcionais; os testes de
IO e documentacao precisam delas. A CI as instala explicitamente.

## Evidencias e limites

[Validacao atual](validation.md) resume formulas, testes e imagens. Relatorios
locais ficam em Verificacao/, que nao e enviada no Git. Esses resultados
verificam implementacao e funcionamento; nao certificam acuracia de campo.
Coeficientes Landsat 9 e adaptacoes AVHRR conservam os limites documentados.
A biblioteca permanece classificada como Beta.

## GitHub e PyPI

Revisar e integrar a branch preparada no branch de publicacao. A CI remota
precisa concluir seus jobs antes de criar a release. Uma release publicada
aciona publish.yml; esse workflow exige PYPI_API_TOKEN configurado no repositorio
com permissao para publicar o pacote pylstemp. A existencia e autorizacao desse
token nao podem ser inferidas da configuracao local.

O workflow compara a tag com a versao, roda testes e twine check antes do upload.
Antes da primeira publicacao, confirmar a disponibilidade/autorizacao do nome
do pacote e a configuracao do secret. Versoes ja existentes no PyPI nao podem
ser substituidas; o numero deve ser livre para a publicacao desejada.

Nenhum push, release, tag remota ou upload e executado durante esta revisao.
Os artefatos locais em dist/ ficam prontos para a etapa de publicacao.

Referencias oficiais: [publicacao de projetos Python](https://packaging.python.org/en/latest/tutorials/packaging-projects/),
[Twine](https://twine.readthedocs.io/en/stable/) e [ajuda do PyPI](https://pypi.org/help/).
