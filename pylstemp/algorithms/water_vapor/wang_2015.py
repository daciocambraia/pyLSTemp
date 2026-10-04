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

    def __call__(self, *, brightness_band_10, brightness_band_11, ndvi_image,
                 window_size=21, group_count=3, mask=None, ndvi_range=None,
                 chunk_rows=8):
        """Retrieve PWV in g/cm2, using bounded-memory vectorized windows.

        Invalid central pixels remain NaN. ndvi_range, if supplied, is the
        valid full-scene NDVI (minimum, maximum), required for tiled/ROI use.
        chunk_rows changes memory usage, not the numerical method.
        """
        bt10 = to_float_array("brightness_band_10", brightness_band_10)
        bt11 = to_float_array("brightness_band_11", brightness_band_11)
        ndvi = to_float_array("ndvi_image", ndvi_image)
        ensure_same_shape(brightness_band_10=bt10, brightness_band_11=bt11, ndvi_image=ndvi)
        if bt10.ndim != 2:
            raise ValueError("Wang inputs must be two-dimensional.")
        for name, value, minimum in (("window_size", window_size, 3),
                                      ("group_count", group_count, 1),
                                      ("chunk_rows", chunk_rows, 1)):
            if isinstance(value, (bool, np.bool_)) or not isinstance(value, (int, np.integer)) or value < minimum:
                raise ValueError(f"{name} must be an integer >= {minimum}.")
        if window_size % 2 == 0:
            raise ValueError("window_size must be odd.")
        valid = np.isfinite(bt10) & np.isfinite(bt11) & np.isfinite(ndvi)
        valid &= (bt10 > 0) & (bt11 > 0) & (np.abs(ndvi) <= 1)
        if mask is not None:
            from ...validation import ensure_boolean_mask
            valid &= ~ensure_boolean_mask(mask, shape=bt10.shape)
        result = np.full(bt10.shape, np.nan)
        if not valid.any():
            return result
        if ndvi_range is None:
            ndvi_min, ndvi_max = ndvi[valid].min(), ndvi[valid].max()
        else:
            bounds = np.asarray(ndvi_range, dtype=float)
            if bounds.shape != (2,) or not np.isfinite(bounds).all() or not -1 <= bounds[0] <= bounds[1] <= 1:
                raise ValueError("ndvi_range must be ordered finite bounds within [-1, 1].")
            ndvi_min, ndvi_max = bounds
            if np.any((ndvi[valid] < ndvi_min) | (ndvi[valid] > ndvi_max)):
                raise ValueError("ndvi_range must contain all valid input NDVI values.")
        edges = self._ndvi_group_edges(float(ndvi_min), float(ndvi_max), group_count)
        radius = window_size // 2
        # Padding happens only for this input; external tiles need halo pixels.
        padded = [np.pad(np.where(valid, a, np.nan), radius,
                         constant_values=np.nan) for a in (bt10, bt11, ndvi)]
        height, width = result.shape
        for row in range(0, height, chunk_rows):
            r1 = min(height, row + chunk_rows)
            for col in range(0, width, 128):
                c1 = min(width, col + 128)
                windows = [np.lib.stride_tricks.sliding_window_view(
                    a[row:r1+2*radius, col:c1+2*radius], (window_size, window_size)
                ) for a in padded]
                result[row:r1, col:c1] = self._vectorized_windows(*windows, ndvi_edges=edges)
        result[~valid | ~np.isfinite(result) | (result < 0)] = np.nan
        return result

    def _vectorized_windows(self, x, y, ndvi, *, ndvi_edges):
        """Same grouped regression as the scalar oracle; windows are views."""
        axes = (-2, -1)
        valid = np.isfinite(x) & np.isfinite(y) & np.isfinite(ndvi)
        weighted = np.zeros(x.shape[:2])
        counts = np.zeros(x.shape[:2])
        ranges = [(None, None)] if ndvi_edges is None else list(zip(ndvi_edges[:-1], ndvi_edges[1:]))
        for index, (lower, upper) in enumerate(ranges):
            group = valid.copy()
            if lower is not None:
                group &= (ndvi >= lower) & ((ndvi <= upper) if index == len(ranges)-1 else (ndvi < upper))
            n = group.sum(axis=axes)
            with np.errstate(divide="ignore", invalid="ignore"):
                mx = np.where(group, x, 0).sum(axis=axes) / n
                my = np.where(group, y, 0).sum(axis=axes) / n
                dx, dy = x - mx[..., None, None], y - my[..., None, None]
                keep = group & (np.abs(dx) > np.abs(dy)) & (dx * dy >= 0)
                count = keep.sum(axis=axes)
                xx = np.where(keep, dx, 0)
                yy = np.where(keep, dy, 0)
                vx, vy = (xx**2).sum(axis=axes), (yy**2).sum(axis=axes)
                cov = (xx * yy).sum(axis=axes)
                forward, reverse = cov / vx, cov / vy
                mean_ndvi = np.where(keep, ndvi, 0).sum(axis=axes) / count
                pv = ((mean_ndvi - 0.2) / 0.3)**2
                ratio_e = np.where(mean_ndvi < 0.2, 0.9939,
                    np.where(mean_ndvi > 0.5, 0.9966,
                             (0.0195*pv+0.9688)/(0.0149*pv+0.9747)))
                ratio = ratio_e * (forward + 1/reverse) / 2
                water = np.where(ratio > 0.9, -18.973*ratio+19.13, -13.412*ratio+14.158)
                ok = (count >= 2) & ~np.isclose(vx, 0) & ~np.isclose(vy, 0)
                ok &= (forward*reverse >= self.correlation_threshold) & np.isfinite(water) & (water >= 0)
            weighted += np.where(ok, water*count, 0)
            counts += np.where(ok, count, 0)
        with np.errstate(divide="ignore", invalid="ignore"):
            return np.where(counts > 0, weighted/counts, np.nan)

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
        valid = np.isfinite(bt_10) & np.isfinite(bt_11) & np.isfinite(ndvi)
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
        transmittance_ratio = emissivity_ratio * (r_11_10 + 1 / r_10_11) / 2
        if transmittance_ratio > 0.9:
            water_vapor = (-18.973 * transmittance_ratio) + 19.13
        else:
            water_vapor = (-13.412 * transmittance_ratio) + 14.158

        if not np.isfinite(water_vapor) or water_vapor < 0:
            return np.nan, 0
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
