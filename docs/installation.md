# Installation

## Requirements

- Python 3.9+
- `pip`

## Install for usage

```bash
pip install pylstemp
```

## Install for local development

From the project root:

```bash
pip install -e .[dev]
```

Verify that Python is importing this checkout and not an older editable install:

```bash
python -c "import pylstemp; print(pylstemp.__file__)"
```

If the printed path points to another checkout such as `pylandtemp` or a different
`pylstemp` folder, remove the old editable install before continuing:

```bash
python -m pip uninstall pylandtemp pylstemp
python -m pip install -e .[dev]
```

## Run tests

```bash
pytest
```

## Windows example

```powershell
cd C:\Pyland\pyLSTemp
py -m pip install --upgrade pip
py -m pip install -e .[dev]
py -c "import pylstemp; print(pylstemp.__file__)"
py -m pytest
```
