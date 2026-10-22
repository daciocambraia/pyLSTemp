# Contributing

Thanks for considering a contribution to `pyLSTemp`.

## Development setup

```bash
python -m pip install -e ".[dev,examples]"
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

1. check installation, imports and package builds; run the scientific suite when available locally
2. update docs when behavior or public API changes
3. explain the scientific or technical rationale for formula changes
4. keep changes focused and reviewable

## Code style

- use clear names over clever names
- add concise comments where scientific logic would otherwise be hard to review
- keep public APIs stable unless there is a strong reason to change them


The full scientific test suite and scene validators are maintained locally under
`Verificacao/` and are not included in public clones or distributions. Public CI
checks installation, imports and packaging; it does not run the local suite.
