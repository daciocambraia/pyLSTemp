"""Shared base class for split-window algorithms."""

from __future__ import annotations

import numpy as np

from ..base_temperature import BaseTemperatureAlgorithm


class SplitWindowParentLST(BaseTemperatureAlgorithm):
    """Common interface for split-window methods."""

    def __call__(self, **kwargs) -> np.ndarray:
        result, mask = self._compute_lst(**kwargs)
        return self._finalize(result, mask=mask)

    def _compute_lst(self, **kwargs):
        raise NotImplementedError
