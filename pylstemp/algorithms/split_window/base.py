"""Shared base class for split-window algorithms."""

from __future__ import annotations

import numpy as np

from ..base_temperature import BaseTemperatureAlgorithm


class SplitWindowParentLST(BaseTemperatureAlgorithm):
    """
    Base class for split-window land-surface temperature methods.

    Subclasses implement ``_compute_lst`` and return both the raw LST result
    and the validated mask. This parent class then applies the shared final
    filtering from ``BaseTemperatureAlgorithm``.
    """

    def __call__(self, **kwargs) -> np.ndarray:
        """
        Compute split-window land-surface temperature.

        Parameters
        ----------
        **kwargs
            Method-specific inputs such as brightness temperatures,
            emissivities, NDVI, water vapor, and mask.

        Returns
        -------
        ndarray
            Land-surface temperature in Kelvin.
        """
        result, mask = self._compute_lst(**kwargs)
        return self._finalize(result, mask=mask)

    def _compute_lst(self, **kwargs):
        """
        Compute a raw split-window LST result for a concrete method.

        Returns
        -------
        tuple
            Raw LST image and validated mask.
        """
        raise NotImplementedError
