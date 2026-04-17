"""Centralized validation helpers for numeric arrays and user inputs."""

from __future__ import annotations

import numpy as np

from .exceptions import InputShapesNotEqual, InvalidMaskError, assert_temperature_unit


def to_float_array(name: str, value) -> np.ndarray:
    """Convert any array-like input to a float numpy array."""
    array = np.asarray(value, dtype=float)
    if array.size == 0:
        raise ValueError(f"Input '{name}' cannot be empty.")
    return array


def ensure_same_shape(**named_arrays: np.ndarray) -> None:
    """Validate that all provided arrays share the same shape."""
    shapes = {name: array.shape for name, array in named_arrays.items() if array is not None}
    unique_shapes = set(shapes.values())
    if len(unique_shapes) > 1:
        raise InputShapesNotEqual(
            "Input arrays must have the same shape. "
            + ", ".join(f"{name}={shape}" for name, shape in shapes.items())
        )


def ensure_boolean_mask(mask, *, shape: tuple[int, ...]) -> np.ndarray:
    """Validate a user mask and return it as a numpy boolean array."""
    mask_array = np.asarray(mask)
    if mask_array.dtype != bool:
        raise InvalidMaskError("Mask must be a numpy array with boolean dtype.")
    if mask_array.shape != shape:
        raise InputShapesNotEqual(
            f"Mask shape {mask_array.shape} does not match expected shape {shape}."
        )
    return mask_array


def build_mask_from(*arrays: np.ndarray) -> np.ndarray:
    """Build a mask that marks zeros and NaNs as invalid pixels."""
    reference = next(array for array in arrays if array is not None)
    mask = np.zeros(reference.shape, dtype=bool)
    for array in arrays:
        if array is None:
            continue
        mask |= np.isnan(array) | (array == 0)
    return mask


def normalize_temperature_unit(unit: str) -> str:
    """Normalize the public API spelling while preserving backward compatibility."""
    assert_temperature_unit(unit)
    normalized = unit.lower()
    return "celsius" if normalized == "celcius" else normalized
