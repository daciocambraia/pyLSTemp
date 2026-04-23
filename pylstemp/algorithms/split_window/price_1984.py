"""Price 1984 split-window temperature algorithm."""

from __future__ import annotations

from ...exceptions import assert_required_keywords_provided
from ...metadata import AlgorithmSpec
from .base import SplitWindowParentLST


class SplitWindowPrice1984LST(SplitWindowParentLST):
    """
    Compute split-window LST adapted from Price (1984).

    The original Price formulation was developed for AVHRR split-window
    channels. This implementation keeps the split-window structure as a
    Landsat Band 10/11 adaptation.

    Notes
    -----
    - This method requires separate emissivity inputs for Band 10 and Band 11.
    - The adaptation should be documented when used in scientific workflows.
    """

    def _compute_lst(self, **kwargs):
        """
        Compute raw Price split-window LST.

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

        result = (tb_10 + 3.33 * (tb_10 - tb_11)) * ((5.5 - emissivity_10) / 4.5) + (
            0.75 * tb_11 * (emissivity_10 - emissivity_11)
        )
        return result, mask


ALGORITHM_SPEC = AlgorithmSpec(
    key="price-1984",
    factory=SplitWindowPrice1984LST,
    name="Price 1984 split-window LST",
    reference="Price (1984)",
    citation=(
        "Price, J. C. Land surface temperature measurements from the split "
        "window channels of the NOAA advanced very high-resolution radiometer. "
        "Journal of Geophysical Research, 1984. This implementation applies the "
        "Price split-window structure as a Landsat Band 10/11 adaptation."
    ),
)
