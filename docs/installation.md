# Installation

## Requirements

- Python 3.9+
- `pip`

## Install for usage

```bash
pip install pylstemp
```

## Install for development

From the project root:

```bash
pip install -e .[dev]
```

## Verify the import path

```bash
python -c "import pylstemp; print(pylstemp.__file__)"
```

If Python points to another checkout, uninstall the old editable install and reinstall this repository:

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
