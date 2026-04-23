# Extending the Library

The project was reorganized so new methods can be added with minimal changes outside their own folder.

## Add a new algorithm to an existing family

Example families:

- `pylstemp/algorithms/emissivity/`
- `pylstemp/algorithms/single_channel/`
- `pylstemp/algorithms/split_window/`
- `pylstemp/algorithms/thermal/`
- `pylstemp/algorithms/spectral_index/`
- `pylstemp/algorithms/radiative_transfer/`

### Steps

1. Create a new module in the correct family folder.
2. Implement the algorithm class or callable.
3. Expose `ALGORITHM_SPEC = AlgorithmSpec(...)` in that module.
4. Add tests for the new behavior.

If the family already uses shared base classes, reuse them:

- `BaseEmissivityAlgorithm`
- `BaseTemperatureAlgorithm`
- `SplitWindowParentLST`

## Minimal example

```python
from ...metadata import AlgorithmSpec


class MyAlgorithm:
    def __call__(self, **kwargs):
        ...


ALGORITHM_SPEC = AlgorithmSpec(
    key="my-method",
    factory=MyAlgorithm,
    name="My method",
    reference="Author (Year)",
    citation="Full citation here.",
)
```

Once that file exists in the family folder, the family registry can discover it automatically.

## Add a brand-new family

1. Create a new package under `pylstemp/algorithms/`.
2. In its `__init__.py`, expose `<family_name>_registry`.
3. Use `discover_algorithms(__name__, "<family_name>")`.
4. Add one or more algorithm modules with `ALGORITHM_SPEC`.
5. Add tests.

### Minimal family `__init__.py`

```python
from ...registry import discover_algorithms

my_family_registry = discover_algorithms(__name__, "my_family")
default_algorithms = my_family_registry.as_mapping()
```

Because `pylstemp/algorithms/__init__.py` discovers families automatically, the new family can appear in `list_algorithms()` without a manual central update.

## When the public API should change

You only need to touch `pylstemp/api.py` if the new family needs a dedicated top-level public function such as:

- `spectral_index(...)`
- `brightness(...)`
- `emissivity(...)`
- `single_window(...)`
- `split_window(...)`

If the family only needs to be discoverable and listed, the registry layer already handles that.

Sensor-specific constants that should not be duplicated across algorithms can live under `pylstemp/sensors/`.

For the current thermal workflow, keep the radiometric conversion concentrated in `brightness(...)`.
The `single_window(...)` and `split_window(...)` public functions should stay focused on LST computation from precomputed brightness temperature arrays.
