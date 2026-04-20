"""Du 2015 practical split-window temperature algorithm."""

from __future__ import annotations

from ...exceptions import assert_required_keywords_provided
from ...metadata import AlgorithmSpec
from .base import SplitWindowParentLST


class SplitWindowDu2015LST(SplitWindowParentLST):
    """Practical split-window LST from Du et al. (2015).

    When water_vapor is not provided, this implementation uses the all-CWV
    coefficient set reported by Du et al. for practical image-only retrieval.
    """

    coefficient_ranges = (
        ((0.0, 2.5), (-2.78009, 1.01408, 0.15833, -0.34991, 4.04487, 3.55414, -8.88394, 0.09152)),
        ((2.0, 3.5), (11.00824, 0.95995, 0.17243, -0.28852, 7.11492, 0.42684, -6.62025, -0.06381)),
        ((3.0, 4.5), (9.62610, 0.96202, 0.13834, -0.17262, 7.87883, 5.17910, -13.26611, -0.07603)),
        ((4.0, 5.5), (0.61258, 0.99124, 0.10051, -0.09664, 7.85758, 6.86626, -15.00742, -0.01185)),
        ((5.0, 6.3), (-0.34808, 0.98123, 0.05599, -0.03518, 11.96444, 9.06710, -14.74085, -0.20471)),
    )
    default_coefficients = (-0.41165, 1.00522, 0.14543, -0.27297, 4.06655, -6.92512, -18.27461, 0.24468)

    @classmethod
    def _coefficients_for(cls, water_vapor):
        """Return Du 2015 coefficients for atmospheric CWV in g/cm2."""
        if water_vapor is None:
            return cls.default_coefficients

        cwv = float(water_vapor)
        for (lower, upper), coefficients in cls.coefficient_ranges:
            if lower <= cwv <= upper:
                return coefficients

        raise ValueError("water_vapor for 'du-2015' must be between 0.0 and 6.3 g/cm2.")

    def _compute_lst(self, **kwargs):
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
        coefficients = self._coefficients_for(kwargs.get("water_vapor"))
        b0, b1, b2, b3, b4, b5, b6, b7 = coefficients
        mask = self._validate_inputs(
            mask=kwargs["mask"],
            brightness_temperature_10=tb_10,
            brightness_temperature_11=tb_11,
            emissivity_10=emissivity_10,
            emissivity_11=emissivity_11,
        )

        mean_tb = (tb_10 + tb_11) / 2
        diff_tb = (tb_10 - tb_11) / 2
        mean_e = (emissivity_10 + emissivity_11) / 2
        diff_e = emissivity_10 - emissivity_11
        emissivity_term = (1 - mean_e) / mean_e
        emissivity_diff_term = diff_e / (mean_e**2)

        result = (
            b0
            + (
                b1
                + (b2 * emissivity_term)
                + (b3 * emissivity_diff_term)
            )
            * mean_tb
            + (
                b4
                + (b5 * emissivity_term)
                + (b6 * emissivity_diff_term)
            )
            * diff_tb
            + (b7 * ((tb_10 - tb_11) ** 2))
        )
        return result, mask


ALGORITHM_SPEC = AlgorithmSpec(
    key="du-2015",
    factory=SplitWindowDu2015LST,
    name="Du 2015 practical split-window LST",
    reference="Du et al. (2015)",
    citation=(
        "Du, C., Ren, H., Qin, Q., Meng, J., and Zhao, S. A practical "
        "split-window algorithm for estimating land surface temperature from "
        "Landsat 8 data. Remote Sensing, 2015."
    ),
)
