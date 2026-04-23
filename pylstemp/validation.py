"""Centralized validation helpers for numeric arrays and user inputs."""

from __future__ import annotations

import numpy as np

from .exceptions import InputShapesNotEqual, InvalidMaskError, assert_temperature_unit


def to_float_array(name: str, value) -> np.ndarray:
    """
    Convert an array-like input to a float NumPy array.

    Parameters
    ----------
    name : str
        Human-readable input name used in error messages.
    value : array-like
        Input value to convert.

    Returns
    -------
    ndarray
        Float array.

    Raises
    ------
    ValueError
        If the input is empty.
    """
    array = np.asarray(value, dtype=float)
    if array.size == 0:
        raise ValueError(f"Input '{name}' cannot be empty.")
    return array


def ensure_same_shape(**named_arrays: np.ndarray) -> None:
    """
    Validate that all provided arrays share the same shape.

    Parameters
    ----------
    **named_arrays : ndarray
        Named arrays to compare. Values set to None are ignored.

    Raises
    ------
    InputShapesNotEqual
        If two or more provided arrays have different shapes.
    """
    shapes = {name: array.shape for name, array in named_arrays.items() if array is not None}
    unique_shapes = set(shapes.values())
    if len(unique_shapes) > 1:
        raise InputShapesNotEqual(
            "Input arrays must have the same shape. "
            + ", ".join(f"{name}={shape}" for name, shape in shapes.items())
        )


def ensure_boolean_mask(mask, *, shape: tuple[int, ...]) -> np.ndarray:
    """
    Validate a user-provided boolean mask.

    Parameters
    ----------
    mask : array-like
        Mask to validate.
    shape : tuple of int
        Expected mask shape.

    Returns
    -------
    ndarray of bool
        Validated boolean mask.

    Raises
    ------
    InvalidMaskError
        If the mask dtype is not boolean.
    InputShapesNotEqual
        If the mask shape does not match the expected shape.
    """
    mask_array = np.asarray(mask)
    if mask_array.dtype != bool:
        raise InvalidMaskError("Mask must be a numpy array with boolean dtype.")
    if mask_array.shape != shape:
        raise InputShapesNotEqual(
            f"Mask shape {mask_array.shape} does not match expected shape {shape}."
        )
    return mask_array


def build_mask_from(*arrays: np.ndarray) -> np.ndarray:
    """
    Build a mask that marks zeros and NaNs as invalid pixels.

    Parameters
    ----------
    *arrays : ndarray
        Input arrays used to build the combined mask.

    Returns
    -------
    ndarray of bool
        Mask where True indicates invalid pixels.
    """
    reference = next(array for array in arrays if array is not None)
    mask = np.zeros(reference.shape, dtype=bool)
    for array in arrays:
        if array is None:
            continue
        mask |= np.isnan(array) | (array == 0)
    return mask


def normalize_temperature_unit(unit: str) -> str:
    """
    Normalize accepted temperature-unit spellings.

    Parameters
    ----------
    unit : str
        Requested output unit.

    Returns
    -------
    str
        Normalized unit, either ``"kelvin"`` or ``"celsius"``.

    """
    assert_temperature_unit(unit)
    return unit.lower()
