# Extending the Library

The project was reorganized so new algorithms can be added without changing the public API structure.

## Add a new emissivity algorithm

1. Create a new module in `src/pylstemp/emissivity/`
2. Implement a class that inherits from `BaseEmissivityAlgorithm`
3. Register it in `src/pylstemp/emissivity/registry.py`
4. Add metadata to `src/pylstemp/references.py`
5. Add tests in `tests/`

## Add a new split-window algorithm

1. Create a new module in `src/pylstemp/temperature/split_window/`
2. Implement a class that inherits from `SplitWindowParentLST`
3. Register it in `src/pylstemp/temperature/registry.py`
4. Add metadata to `src/pylstemp/references.py`
5. Add tests covering shape, masking and expected behavior

## Add a new domain later

The project now separates concerns by domain:

- `vegetation/`
- `thermal/`
- `emissivity/`
- `temperature/`
- `core/`

That makes it straightforward to add new groups like:

- `atmosphere/`
- `radiance/`
- `indices/`
- `io/`
