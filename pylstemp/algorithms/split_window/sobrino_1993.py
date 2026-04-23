"""Sobrino 1993 split-window temperature algorithm."""

from __future__ import annotations

from ...exceptions import assert_required_keywords_provided
from ...metadata import AlgorithmSpec
from .base import SplitWindowParentLST


class SplitWindowSobrino1993LST(SplitWindowParentLST):
    """
    Compute theoretical split-window LST from Sobrino et al. (1993).

    The method uses Band 10 and Band 11 brightness temperatures together with
    separate emissivity estimates for both bands.

    Notes
    -----
    - Brightness temperature and emissivity must be computed before calling
      this method.
    - The implementation follows the Sobrino split-window equation currently
      documented by the package.
    """

    def _compute_lst(self, **kwargs):
        """
        Compute raw Sobrino et al. split-window LST.

        Parameters
        ----------
        brightness_temperature_10 : array-like
            Band 10 brightness temperature in Kelvin.
        brightness_temperature_11 : array-like
            Band 11 brightness temperature in Kelvin.
        emissivity_10 : array-like
            Band 10 land-surface emissivity.
        emissivity_11 : array-like
            Band 11 land-surface emissivity.
        mask : array-like of bool or None
            Boolean mask where True values indicate invalid pixels.

        Returns
        -------
        tuple
            Raw LST image in Kelvin and validated mask.
        """
        required_keywords = [
            "emissivity_10",
            "emissivity_11",
            "brightness_temperature_10",
            "brightness_temperature_11",
            "mask",
        ]
        assert_required_keywords_provided(required_keywords, **kwargs)

        tb_10 = kwargs["brightness_temperature_10"]
        tb_11 = kwargs["brightness_temperature_11"]
        emissivity_10 = kwargs["emissivity_10"]
        emissivity_11 = kwargs["emissivity_11"]
        mask = self._validate_inputs(
            mask=kwargs["mask"],
            brightness_temperature_10=tb_10,
            brightness_temperature_11=tb_11,
            emissivity_10=emissivity_10,
            emissivity_11=emissivity_11,
        )

        diff_tb = tb_10 - tb_11
        diff_e = emissivity_10 - emissivity_11
        result = (
            tb_10
            + (1.06 * diff_tb)
            + (0.46 * diff_tb**2)
            + (53 * (1 - emissivity_10))
            - (53 * diff_e)
        )
        return result, mask


ALGORITHM_SPEC = AlgorithmSpec(
    key="sobrino-1993",
    factory=SplitWindowSobrino1993LST,
    name="Sobrino 1993 split-window LST",
    reference="Sobrino et al. (1993)",
    citation=(
        "Sobrino, J. A., Caselles, V., and Coll, C. Theoretical split window "
        "algorithms for determining the actual surface temperature. Il Nuovo "
        "Cimento, 1993."
    ),
)
