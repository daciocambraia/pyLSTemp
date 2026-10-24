# Contributing

Thanks for considering a contribution to `pyLSTemp`.

## Development setup

```bash
python -m pip install -e ".[dev,examples]"
python -m unittest discover -s tests -v
python -m build
python -m twine check dist/*
```

## Project principles

- keep bibliographic references explicit when implementing or modifying formulas
- prefer one algorithm per file for clarity and maintainability
- verify functional changes locally and summarize the validation in the pull request
- preserve visible credit to the original `pylandtemp` project

## Pull requests

Before opening a pull request:

1. run the essential scientific regression suite, installation/import checks and package builds; run applicable local scene checks
2. update docs when behavior or public API changes
3. explain the scientific or technical rationale for formula changes
4. keep changes focused and reviewable

## Code style

- use clear names over clever names
- add concise comments where scientific logic would otherwise be hard to review
- keep public APIs stable unless there is a strong reason to change them


The essential `tests/` suite uses independent synthetic equations without private
articles or imagery. CI executes it against the installed wheel using
`python -I -m unittest discover -s tests -v`. The full local scientific suite,
scene validators, datasets and reports stay under `Verificacao/` outside Git
and distributions. Source changes require updating the reviewed method cards.
