# Contributing

Thanks for considering a contribution to `pyLSTemp`.

## Development setup

```bash
pip install -e .[dev]
pytest
```

## Project principles

- keep bibliographic references explicit when implementing or modifying formulas
- prefer one algorithm per file for clarity and maintainability
- add or update tests for every functional change
- preserve visible credit to the original `pylandtemp` project

## Pull requests

Before opening a pull request:

1. run the test suite
2. update docs when behavior or public API changes
3. explain the scientific or technical rationale for formula changes
4. keep changes focused and reviewable

## Code style

- use clear names over clever names
- add concise comments where scientific logic would otherwise be hard to review
- keep public APIs stable unless there is a strong reason to change them

