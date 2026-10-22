"""Ren et al. (2015) MSWCVR: Eqs.1b/1c/2, Sections 2 and 4.2."""
from __future__ import annotations
import numpy as np
from ...metadata import AlgorithmSpec
from ...validation import to_float_array, ensure_same_shape, ensure_boolean_mask


class WaterVaporRen2015:
    """Retrieve PWV [g/cm2] from local TOA BT covariance/variance.

    Implements mean-centered R_ji and the nonlinear Eq.2, assuming unity
    emissivity ratio. ndvi_filter=True reproduces the local +/-1.5 sigma
    sample exclusion described in Section 4.2; no global NDVI groups are used.
    The default centered 11-pixel window is an adaptation of native-TIRS
    n=10. On resampled 30-m scenes choose 33 pixels for about 1 km support.
    These moving-window outputs are not independent 30-m atmospheric samples.

    min_samples=10 and quality_threshold=.95 are explicit operational screens,
    not sample-count/threshold mandates established for TIRS by the paper.
    Domain [.06,6.3] follows the 946-profile source calibration set. No clipping.
    """

    def __call__(self, *, brightness_band_10, brightness_band_11,
                 ndvi_image=None, window_size=11, mask=None, chunk_rows=8,
                 min_samples=10, quality_threshold=.95, ndvi_filter=True,
                 return_diagnostics=False):
        x = to_float_array("brightness_band_10", brightness_band_10)
        y = to_float_array("brightness_band_11", brightness_band_11)
        ensure_same_shape(brightness_band_10=x, brightness_band_11=y)
        if x.ndim != 2:
            raise ValueError("Ren inputs must be two-dimensional.")
        for name,value,minimum in (("window_size",window_size,3),
                                   ("chunk_rows",chunk_rows,1),
                                   ("min_samples",min_samples,2)):
            if isinstance(value,(bool,np.bool_)) or not isinstance(value,(int,np.integer)) or value < minimum:
                raise ValueError(f"{name} must be an integer >= {minimum}.")
        if window_size % 2 != 1:
            raise ValueError("window_size must be odd for centered Ren windows.")
        if min_samples > window_size**2:
            raise ValueError("min_samples cannot exceed window area.")
        if not np.isscalar(quality_threshold) or not np.isfinite(quality_threshold) or not 0 <= quality_threshold <= 1:
            raise ValueError("quality_threshold must be finite in [0,1].")
        if not isinstance(ndvi_filter,(bool,np.bool_)) or not isinstance(return_diagnostics,(bool,np.bool_)):
            raise ValueError("ndvi_filter and return_diagnostics must be boolean.")
        valid = np.isfinite(x) & np.isfinite(y) & (x > 0) & (y > 0)
        if mask is not None:
            valid &= ~ensure_boolean_mask(mask,shape=x.shape)
        n = None
        if ndvi_image is not None:
            n = to_float_array("ndvi_image",ndvi_image)
            ensure_same_shape(brightness_band_10=x,ndvi_image=n)
        if ndvi_filter:
            if n is None:
                raise ValueError("Ren ndvi_filter=True requires ndvi_image; choose False explicitly for the thermal-only core.")
            valid &= np.isfinite(n) & (np.abs(n) <= 1)
        result = np.full(x.shape,np.nan)
        raw = np.full(x.shape,np.nan)
        ratio = np.full(x.shape,np.nan)
        quality = np.full(x.shape,np.nan)
        counts = np.zeros(x.shape,dtype=np.int32)
        radius = window_size//2
        arrays = [np.pad(np.where(valid,a,np.nan),radius,constant_values=np.nan)
                  for a in ([x,y,n] if ndvi_filter else [x,y])]
        axes=(-2,-1)
        for row in range(0,x.shape[0],chunk_rows):
            stop=min(x.shape[0],row+chunk_rows)
            for col in range(0,x.shape[1],128):
                right=min(x.shape[1],col+128)
                windows=[np.lib.stride_tricks.sliding_window_view(
                    a[row:stop+2*radius,col:right+2*radius],(window_size,window_size))
                    for a in arrays]
                wx,wy=windows[:2]
                good=np.isfinite(wx)&np.isfinite(wy)
                with np.errstate(divide="ignore",invalid="ignore",over="ignore"):
                    if ndvi_filter:
                        wn=windows[2]
                        number=good.sum(axis=axes)
                        mn=np.where(good,wn,0).sum(axis=axes)/number
                        dn=wn-mn[...,None,None]
                        sd=np.sqrt(np.where(good,dn*dn,0).sum(axis=axes)/number)
                        good &= np.abs(dn) <= 1.5*sd[...,None,None]
                    number=good.sum(axis=axes)
                    mx=np.where(good,wx,0).sum(axis=axes)/number
                    my=np.where(good,wy,0).sum(axis=axes)/number
                    dx=np.where(good,wx-mx[...,None,None],0)
                    dy=np.where(good,wy-my[...,None,None],0)
                    vx=(dx*dx).sum(axis=axes)
                    vy=(dy*dy).sum(axis=axes)
                    covariance=(dx*dy).sum(axis=axes)
                    r=covariance/vx
                    chi=covariance**2/(vx*vy)
                    water=-9.674*r*r+.653*r+9.087
                    tolx=number*64*np.finfo(float).eps*np.maximum(1,mx*mx)
                    toly=number*64*np.finfo(float).eps*np.maximum(1,my*my)
                    calculable=(number>=min_samples)&(vx>tolx)&(vy>toly)&(covariance>0)
                    calculable &= valid[row:stop,col:right]
                    screened=calculable & np.isfinite(water) & (chi>=quality_threshold)
                    screened &= (water>=.06)&(water<=6.3)
                sl=np.s_[row:stop,col:right]
                result[sl]=np.where(screened,water,np.nan)
                raw[sl]=np.where(calculable & np.isfinite(water),water,np.nan)
                ratio[sl]=np.where(calculable,r,np.nan)
                quality[sl]=np.where(calculable,chi,np.nan)
                counts[sl]=np.where(valid[sl],number,0)
        if return_diagnostics:
            return dict(water_vapor=result,raw_water_vapor=raw,ratio=ratio,
                        chi_squared=quality,sample_count=counts,
                        invalid_mask=~np.isfinite(result))
        return result


ALGORITHM_SPEC = AlgorithmSpec(
    key="ren-2015",factory=WaterVaporRen2015,
    name="Ren 2015 modified split-window covariance-variance PWV",
    reference="Ren et al. (2015)",
    citation="Ren, H., Du, C., Liu, R., Qin, Q., Yan, G., Li, Z.-L., Meng, J. (2015). Atmospheric water vapor retrieval from Landsat 8 thermal infrared images. JGR Atmospheres 120, 1723-1738. https://doi.org/10.1002/2014JD022619",
)
