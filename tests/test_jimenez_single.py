"""Independent SC equation values, domain and API contracts."""
import numpy as np
import pytest
from pylstemp import single_window, list_algorithms
from pylstemp.algorithms.single_channel import SingleChannelJimenezMunoz2014LST
from pylstemp.exceptions import InputShapesNotEqual, InvalidMaskError


def calculate(w=1., **overrides):
    inputs=dict(brightness_temperature_10=np.full((2,2),300.),
                emissivity_10=np.full((2,2),.98),radiance_band_10=np.full((2,2),10.),
                water_vapor=w,mask=None)
    inputs.update(overrides)
    return SingleChannelJimenezMunoz2014LST()(**inputs)

@pytest.mark.parametrize("w,expected",[(0,301.9831102410753),(1,303.0216977002281),
                                     (2,304.4427033109316),(3,306.2461270731858)])
def test_high_precision_reference(w,expected):
    # Independently calculated in 50-digit Decimal from paper Eqs. 1/2/4/6.
    np.testing.assert_allclose(calculate(w),expected,rtol=0,atol=1e-11)

@pytest.mark.parametrize("w",[-.01,3.000001,np.nan,np.inf,-np.inf])
def test_invalid_scalar_pwv_rejected(w):
    with pytest.raises(ValueError,match="within"):
        calculate(w)

def test_pwv_raster_screen_does_not_modify_input():
    w=np.array([[1.,3.000001],[np.nan,-1.]])
    old=w.copy();actual=calculate(w)
    assert actual[0,0]==pytest.approx(303.0216977002281)
    assert np.isnan(actual[0,1:]).all() and np.isnan(actual[1]).all()
    np.testing.assert_array_equal(w,old)

@pytest.mark.parametrize("field,value",[("radiance_band_10",0.),("radiance_band_10",-1.),
    ("radiance_band_10",np.inf),("brightness_temperature_10",0.),("emissivity_10",1.01)])
def test_invalid_pixel_is_nan(field,value):
    array=np.full((2,2),10. if field=="radiance_band_10" else 300. if field.startswith("brightness") else .98)
    array[0,0]=value
    actual=calculate(**{field:array})
    assert np.isnan(actual[0,0]);assert np.isfinite(actual[1,1])

@pytest.mark.parametrize("field",["radiance_band_10","water_vapor"])
def test_required_input_is_identified(field):
    with pytest.raises(ValueError,match="requires radiance_band_10"):
        calculate(**{field:None})

@pytest.mark.parametrize("field",["radiance_band_10","water_vapor"])
def test_grid_mismatch_rejected(field):
    with pytest.raises(InputShapesNotEqual):calculate(**{field:np.ones((1,2))})

def test_invalid_mask_rejected():
    with pytest.raises(InvalidMaskError):calculate(mask=np.zeros((2,2)))

def test_scalar_and_raster_agree_and_mask_applies():
    np.testing.assert_array_equal(calculate(2),calculate(np.full((2,2),2.)))
    assert np.isnan(calculate(mask=np.ones((2,2),bool))).all()

def test_public_api_units_and_immutability():
    tb=np.full((2,2),300.);red=np.full((2,2),20.);nir=red*2
    radiance=np.full((2,2),10.);w=np.full((2,2),1.)
    arrays=(tb,red,nir,radiance,w);old=[a.copy() for a in arrays]
    kw=dict(lst_method="jimenez-munoz-sc-2014",radiance_band_10=radiance,water_vapor=w)
    k=single_window(tb,red,nir,**kw);c=single_window(tb,red,nir,unit="celsius",**kw)
    np.testing.assert_allclose(c,k-273.15,rtol=0,atol=1e-12)
    for a,b in zip(arrays,old):np.testing.assert_array_equal(a,b)

def test_unused_parameters_are_rejected_for_avdan():
    with pytest.raises(ValueError,match="only used"):
        single_window(np.full((2,2),300.),np.ones((2,2)),np.full((2,2),2.),water_vapor=1)

def test_catalog_distinguishes_sc_from_sw():
    catalog=list_algorithms()
    assert "jimenez-munoz-sc-2014" in catalog["single_channel"]
    assert "jimenez-munoz-2014" in catalog["split_window"]
    assert "radiance_band_10" in catalog["single_channel"]["jimenez-munoz-sc-2014"]["input_requirements"]
    assert "[0,3]" in catalog["single_channel"]["jimenez-munoz-sc-2014"]["water_vapor_support"]
