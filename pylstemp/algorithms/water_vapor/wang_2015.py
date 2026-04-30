"""Wang 2015 NDVI-based PWV retrieval for Landsat 8 TIRS."""

from __future__ import annotations

import numpy as np

from ...metadata import AlgorithmSpec
from ...validation import ensure_same_shape, to_float_array


class WaterVaporWang2015:
    """
    Retrieve precipitable water vapor using Wang et al. (2015).

    The method estimates atmospheric column water vapor from Band 10 and
    Band 11 brightness temperatures using NDVI-based local windows.

    Notes
    -----
    - Inputs must be spatially aligned and have the same shape.
    - ``window_size`` controls the local moving window used around each pixel.
      The default 21 by 21 template is the nearest odd-sized equivalent to the
      20 by 20 template used by Wang et al. (2015).
    - ``group_count`` controls how each template is divided into NDVI groups.
      The default follows the three NDVI groups used in the article.
    - NDVI group boundaries are computed from the valid NDVI range of the full
      scene, as described by Wang et al., rather than recalculated for each
      moving template.
    """

    ndvi_soil = 0.2
    ndvi_vegetation = 0.5
    correlation_threshold = 0.97

    def __call__(
        self,
        *,
        brightness_band_10,
        brightness_band_11,
        ndvi_image,
        window_size: int = 21,
        group_count: int = 3,
    ) -> np.ndarray:
        """
        Compute a pixel-wise precipitable water vapor image.

        Parameters
        ----------
        brightness_band_10 : array-like
            Band 10 brightness temperature in Kelvin.
        brightness_band_11 : array-like
            Band 11 brightness temperature in Kelvin.
        ndvi_image : array-like
            NDVI image used to group local pixels by vegetation condition.
        window_size : int, default=21
            Odd moving-window size in pixels. Must be greater than or equal
            to 3. The article uses a fixed 20 by 20 pixel template; 21 by 21
            preserves a centered moving-window implementation while staying
            close to the original template size.
        group_count : int, default=3
            Number of NDVI groups used inside each local window.

        Returns
        -------
        ndarray
            Pixel-wise precipitable water vapor in g/cm2.

        Raises
        ------
        ValueError
            If ``window_size`` is even or smaller than 3, or if
            ``group_count`` is smaller than 1.
        """
        bt_10 = to_float_array("brightness_band_10", brightness_band_10)
        bt_11 = to_float_array("brightness_band_11", brightness_band_11)
        ndvi = to_float_array("ndvi_image", ndvi_image)
        ensure_same_shape(brightness_band_10=bt_10, brightness_band_11=bt_11, ndvi_image=ndvi)

        if window_size < 3 or window_size % 2 == 0:
            raise ValueError("window_size must be an odd integer greater than or equal to 3.")
        if group_count < 1:
            raise ValueError("group_count must be greater than or equal to 1.")

        water_vapor = np.full(bt_10.shape, np.nan, dtype=float)

        finite_ndvi = ndvi[~np.isnan(ndvi)]
        if finite_ndvi.size == 0:
            return water_vapor

        ndvi_min = float(np.nanmin(finite_ndvi))
        ndvi_max = float(np.nanmax(finite_ndvi))
        ndvi_edges = self._ndvi_group_edges(ndvi_min, ndvi_max, group_count)

        radius = window_size // 2

        for row in range(bt_10.shape[0]):
            row_start = max(0, row - radius)
            row_end = min(bt_10.shape[0], row + radius + 1)
            for col in range(bt_10.shape[1]):
                col_start = max(0, col - radius)
                col_end = min(bt_10.shape[1], col + radius + 1)
                water_vapor[row, col] = self._window_water_vapor(
                    bt_10[row_start:row_end, col_start:col_end],
                    bt_11[row_start:row_end, col_start:col_end],
                    ndvi[row_start:row_end, col_start:col_end],
                    ndvi_edges=ndvi_edges,
                )

        return water_vapor

    def _window_water_vapor(self, bt_10, bt_11, ndvi, *, ndvi_edges) -> float:
        """
        Estimate water vapor for a local image window.

        Parameters
        ----------
        bt_10 : ndarray
            Local Band 10 brightness temperature window.
        bt_11 : ndarray
            Local Band 11 brightness temperature window.
        ndvi : ndarray
            Local NDVI window.
        ndvi_edges : ndarray or None
            Scene-level NDVI group edges used to classify template pixels.

        Returns
        -------
        float
            Weighted local water vapor estimate in g/cm2.
        """
        valid = ~(np.isnan(bt_10) | np.isnan(bt_11) | np.isnan(ndvi))
        if np.count_nonzero(valid) < 2:
            return np.nan

        if ndvi_edges is None:
            groups = [valid]
        else:
            groups = []
            for index in range(len(ndvi_edges) - 1):
                lower = ndvi_edges[index]
                upper = ndvi_edges[index + 1]
                if index == len(ndvi_edges) - 2:
                    group = valid & (ndvi >= lower) & (ndvi <= upper)
                else:
                    group = valid & (ndvi >= lower) & (ndvi < upper)
                groups.append(group)

        weighted_sum = 0.0
        pixel_count = 0
        for group in groups:
            group_water_vapor, count = self._group_water_vapor(bt_10[group], bt_11[group], ndvi[group])
            if np.isnan(group_water_vapor) or count == 0:
                continue
            weighted_sum += group_water_vapor * count
            pixel_count += count

        if pixel_count == 0:
            return np.nan
        return weighted_sum / pixel_count

    def _ndvi_group_edges(self, ndvi_min: float, ndvi_max: float, group_count: int):
        """Build scene-level NDVI group edges following Wang et al. (2015)."""
        if np.isclose(ndvi_min, ndvi_max):
            return None
        return np.linspace(ndvi_min, ndvi_max, group_count + 1)

    def _group_water_vapor(self, bt_10, bt_11, ndvi) -> tuple[float, int]:
        """
        Estimate water vapor for one NDVI group.

        Parameters
        ----------
        bt_10 : ndarray
            Band 10 brightness temperature values for the group.
        bt_11 : ndarray
            Band 11 brightness temperature values for the group.
        ndvi : ndarray
            NDVI values for the group.

        Returns
        -------
        tuple
            Water vapor estimate in g/cm2 and number of valid pixels used.
        """
        if bt_10.size < 2:
            return np.nan, 0

        mean_10 = np.nanmean(bt_10)
        mean_11 = np.nanmean(bt_11)
        delta_10 = bt_10 - mean_10
        delta_11 = bt_11 - mean_11

        valid = (np.abs(delta_10) > np.abs(delta_11)) & ((delta_10 * delta_11) >= 0)
        if np.count_nonzero(valid) < 2:
            return np.nan, 0

        delta_10 = delta_10[valid]
        delta_11 = delta_11[valid]
        ndvi_valid = ndvi[valid]
        denominator_10 = np.sum(delta_10**2)
        denominator_11 = np.sum(delta_11**2)
        if np.isclose(denominator_10, 0) or np.isclose(denominator_11, 0):
            return np.nan, 0

        covariance = np.sum(delta_10 * delta_11)
        r_11_10 = covariance / denominator_10
        r_10_11 = covariance / denominator_11
        r_squared = r_11_10 * r_10_11
        if r_squared < self.correlation_threshold:
            return np.nan, 0

        emissivity_ratio = self._emissivity_ratio(float(np.nanmean(ndvi_valid)))
        transmittance_ratio = emissivity_ratio * r_11_10
        if transmittance_ratio > 0.9:
            water_vapor = (-18.973 * transmittance_ratio) + 19.13
        else:
            water_vapor = (-13.412 * transmittance_ratio) + 14.158

        return water_vapor, int(np.count_nonzero(valid))

    def _emissivity_ratio(self, ndvi: float) -> float:
        """
        Estimate the Band 11 to Band 10 emissivity ratio from NDVI.

        Parameters
        ----------
        ndvi : float
            Mean NDVI value for a local group.

        Returns
        -------
        float
            Estimated emissivity ratio.
        """
        if ndvi < self.ndvi_soil:
            return 0.9939
        if ndvi > self.ndvi_vegetation:
            return 0.9966

        pv = ((ndvi - self.ndvi_soil) / (self.ndvi_vegetation - self.ndvi_soil)) ** 2
        return ((0.0195 * pv) + 0.9688) / ((0.0149 * pv) + 0.9747)


ALGORITHM_SPEC = AlgorithmSpec(
    key="wang-2015",
    factory=WaterVaporWang2015,
    name="Wang 2015 NDVI-based precipitable water vapor",
    reference="Wang et al. (2015)",
    citation=(
        "Wang, M., He, G., Zhang, Z., Wang, G., and Long, T. NDVI-based "
        "split-window algorithm for precipitable water vapour retrieval from "
        "Landsat-8 TIRS data over land area. Remote Sensing Letters, 2015."
    ),
)
