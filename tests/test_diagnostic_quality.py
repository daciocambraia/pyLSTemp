"""Numerical and compatibility contracts of diagnostic PWV/LST mode."""
import warnings
import numpy as np
import pytest
from pylstemp import water_vapor,single_window,split_window
from pylstemp.quality import QualityFlag as Q


def test_sc_extrapolation_preserves_equation_and_scalar_array_parity():
    t=np.full((2,3),300.);eps=np.full(t.shape,.98);L=np.full(t.shape,10.)
    with pytest.raises(ValueError):single_window(t,method='jimenez-munoz-2014',emissivity_10=eps,radiance_band_10=L,water_vapor=4.)
    r=single_window(t,method='jimenez-munoz-2014',emissivity_10=eps,radiance_band_10=L,water_vapor=4.,quality_mode='diagnostic')
    w=4.;p1=.04019*w*w+.02916*w+1.01523;p2=-.38333*w*w-1.50294*w+.20324;p3=.00918*w*w+1.36072*w-.27514
    gamma=300**2/(1324*10);delta=300-300**2/1324;expected=gamma*((p1*10+p2)/.98+p3)+delta
    np.testing.assert_allclose(r['lst'],expected,atol=1e-12)
    assert np.all(r['quality_flags'] & Q.PWV_OUT_OF_DOMAIN) and np.isnan(r['screened_lst']).all()
    a=single_window(t,method='jimenez-munoz-2014',emissivity_10=eps,radiance_band_10=L,water_vapor=np.full(t.shape,w),quality_mode='diagnostic')
    np.testing.assert_array_equal(a['lst'],r['lst'])


def test_du_explicit_fallback_not_clipped_or_nearest_coefficients():
    t=np.full((3,3),300.);e=np.full(t.shape,.98)
    general=split_window(t,t-2,emissivity_10=e,emissivity_11=e,method='du-2015')
    r=split_window(t,t-2,emissivity_10=e,emissivity_11=e,method='du-2015',water_vapor=8.,quality_mode='diagnostic')
    np.testing.assert_array_equal(r['lst'],general)
    assert np.all(r['quality_flags'] & Q.DU_GENERAL_FALLBACK) and np.all(r['quality_flags'] & Q.PWV_OUT_OF_DOMAIN)
    assert np.isnan(r['screened_lst']).all()


def test_ren_retains_low_quality_insufficient_samples_and_nonphysical():
    y,x=np.mgrid[:7,:7];a=300+x+y*.2;b=295+.8*(a-300)+((x+y)%2)*2
    mask=np.ones(a.shape,bool);mask[2:5,2:5]=False
    r=water_vapor(a,b,method='ren-2015',ndvi_filter=False,window_size=5,mask=mask,quality_mode='diagnostic')
    assert np.isfinite(r['water_vapor'][3,3]) and np.isnan(r['screened_water_vapor'][3,3])
    assert r['quality_flags'][3,3] & Q.INSUFFICIENT_SAMPLES
    assert r['quality_flags'][3,3] & Q.LOW_QUALITY
    xx=a[2:5,2:5].ravel();yy=b[2:5,2:5].ravel();dx=xx-xx.mean();dy=yy-yy.mean();slope=np.sum(dx*dy)/np.sum(dx**2)
    np.testing.assert_allclose(r['water_vapor'][3,3],-9.674*slope*slope+.653*slope+9.087)
    negative=water_vapor(a,290+1.2*(a-300),method='ren-2015',ndvi_filter=False,window_size=5,quality_mode='diagnostic')
    assert negative['water_vapor'][3,3]<0 and negative['quality_flags'][3,3]&Q.NONPHYSICAL
    undefined=water_vapor(np.full((5,5),300.),np.full((5,5),290.),method='ren-2015',ndvi_filter=False,window_size=5,quality_mode='diagnostic')
    assert np.isnan(undefined['water_vapor']).all() and np.all(undefined['quality_flags']&Q.UNDEFINED)


def test_wang_raw_group_regression_and_original_screened_result():
    rng=np.random.default_rng(14);x=300+np.arange(49).reshape(7,7)*.2;y=295+.7*(x-300)+rng.normal(0,2.5,x.shape);nd=np.full(x.shape,.6)
    r=water_vapor(x,y,ndvi_image=nd,method='wang-2015',window_size=5,group_count=1,quality_mode='diagnostic')
    original=water_vapor(x,y,ndvi_image=nd,method='wang-2015',window_size=5,group_count=1)
    np.testing.assert_allclose(r['screened_water_vapor'],original,rtol=0,atol=0,equal_nan=True)
    xx=x[1:6,1:6];yy=y[1:6,1:6];dx=xx-xx.mean();dy=yy-yy.mean();keep=(abs(dx)>abs(dy))&(dx*dy>=0);dx=dx[keep];dy=dy[keep]
    cov=np.sum(dx*dy);vx=np.sum(dx**2);vy=np.sum(dy**2);ratio=.9966*(cov/vx+vy/cov)/2
    expected=19.13-18.973*ratio if ratio>.9 else 14.158-13.412*ratio
    np.testing.assert_allclose(r['water_vapor'][3,3],expected,atol=1e-12)
    assert r['quality_flags'][3,3]&Q.LOW_QUALITY
    assert np.isfinite(r['water_vapor'][3,3]) and np.isnan(original[3,3])
    other=water_vapor(x,y,ndvi_image=nd,method='wang-2015',window_size=5,group_count=1,quality_mode='diagnostic',chunk_rows=1)
    np.testing.assert_array_equal(other['water_vapor'],r['water_vapor'])


def test_upstream_flags_shape_validation_and_mask_preserved():
    t=np.full((2,2),300.);eps=np.full(t.shape,.98);mask=np.zeros(t.shape,bool);mask[0,0]=True;up=np.full(t.shape,int(Q.LOW_QUALITY),dtype=np.uint16)
    r=split_window(t,t-2,method='du-2015',emissivity_10=eps,emissivity_11=eps,water_vapor=2.,mask=mask,pwv_quality_flags=up,quality_mode='diagnostic')
    assert np.isnan(r['lst'][0,0]) and r['quality_flags'][0,0]&Q.INPUT_MASKED
    assert np.all(r['quality_flags']&Q.LOW_QUALITY) and not np.any(r['quality_acceptable'])
    assert not np.any(r['lst_quality_flags']&Q.LOW_QUALITY)
    with pytest.raises(ValueError):split_window(t,t-2,method='du-2015',emissivity_10=eps,emissivity_11=eps,water_vapor=2.,pwv_quality_flags=np.zeros((3,3),dtype='uint16'),quality_mode='diagnostic')
    with pytest.raises(ValueError):water_vapor(t,t,ndvi_filter=False,method='ren-2015',quality_mode='anything')

def test_mono_nonpositive_kelvin_is_retained_and_flagged_only_in_diagnostic_mode():
    t=np.full((2,2),300.);eps=np.full(t.shape,.001)
    default=single_window(t,emissivity_10=eps)
    diagnostic=single_window(t,emissivity_10=eps,quality_mode='diagnostic')
    expected=300/(1+(10.895e-6*300/1.438e-2)*np.log(.001))
    assert np.isnan(default).all()
    np.testing.assert_allclose(diagnostic['lst'],expected)
    assert np.all(diagnostic['quality_flags']&Q.NONPHYSICAL)
