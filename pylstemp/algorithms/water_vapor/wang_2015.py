"""Wang 2015 NDVI-based PWV retrieval for Landsat 8 TIRS."""

from __future__ import annotations

import numpy as np

from ...metadata import AlgorithmSpec
from ...validation import ensure_same_shape, to_float_array


class WaterVaporWang2015:
    """Retrieve precipitable water vapor from Landsat 8 TIRS brightness temperatures."""

    ndvi_soil = 0.2
    ndvi_vegetation = 0.5
    correlation_threshold = 0.97

    def __call__(
        self,
        *,
        brightness_band_10,
        brightness_band_11,
        ndvi_image,
        window_size: int = 5,
        group_count: int = 5,
    ) -> np.ndarray:
        bt_10 = to_float_array("brightness_band_10", brightness_band_10)
        bt_11 = to_float_array("brightness_band_11", brightness_band_11)
        ndvi = to_float_array("ndvi_image", ndvi_image)
        ensure_same_shape(brightness_band_10=bt_10, brightness_band_11=bt_11, ndvi_image=ndvi)

        if window_size < 3 or window_size % 2 == 0:
            raise ValueError("window_size must be an odd integer greater than or equal to 3.")
        if group_count < 1:
            raise ValueError("group_count must be greater than or equal to 1.")

        water_vapor = np.full(bt_10.shape, np.nan, dtype=float)
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
                    group_count=group_count,
                )

        return water_vapor

    def _window_water_vapor(self, bt_10, bt_11, ndvi, *, group_count: int) -> float:
        valid = ~(np.isnan(bt_10) | np.isnan(bt_11) | np.isnan(ndvi))
        if np.count_nonzero(valid) < 2:
            return np.nan

        ndvi_valid = ndvi[valid]
        ndvi_min = float(np.nanmin(ndvi_valid))
        ndvi_max = float(np.nanmax(ndvi_valid))
        if np.isclose(ndvi_min, ndvi_max):
            groups = [valid]
        else:
            edges = np.linspace(ndvi_min, ndvi_max, group_count + 1)
            groups = []
            for index in range(group_count):
                lower = edges[index]
                upper = edges[index + 1]
                if index == group_count - 1:
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

    def _group_water_vapor(self, bt_10, bt_11, ndvi) -> tuple[float, int]:
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
