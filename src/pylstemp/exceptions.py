"""Shared exception types used across the package."""


class PyLandTempError(Exception):
    """Base exception for the package."""


class InvalidMaskError(PyLandTempError):
    """Raised when a mask is missing the expected boolean dtype or shape."""


class KeywordArgumentError(PyLandTempError):
    """Raised when an algorithm-specific keyword argument is missing."""


class InputShapesNotEqual(PyLandTempError):
    """Raised when arrays that should match in shape do not match."""


class InvalidMethodRequested(PyLandTempError):
    """Raised when a registry key does not point to a registered algorithm."""


class InvalidTemperatureUnitError(PyLandTempError):
    """Raised when the output unit is not kelvin or celsius."""


def assert_required_keywords_provided(keywords, **kwargs):
    """Compatibility helper kept for algorithm classes."""
    for keyword in keywords:
        if keyword not in kwargs or kwargs[keyword] is None:
            raise KeywordArgumentError(
                f"Keyword argument '{keyword}' must be provided for this computation."
            )


def assert_temperature_unit(unit: str) -> None:
    """Compatibility helper that validates temperature units."""
    normalized = unit.lower()
    if normalized not in {"kelvin", "celsius", "celcius"}:
        raise InvalidTemperatureUnitError(
            "Temperature unit should be either 'kelvin' or 'celsius'."
        )

