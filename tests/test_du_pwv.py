"""Du raster boundaries, independent equations and explicit scene workflow."""
import json
import numpy as np
import pytest
from pylstemp.algorithms.split_window.du_2015 import SplitWindowDu2015LST as Du
from pylstemp.exceptions import InputShapesNotEqual, InvalidMaskError
from pylstemp.workflows import du_from_scene, scene_ndvi_range
from scripts import matrix_references as reference


def run(water, shape=(3, 4), **overrides):
    a = np.arange(np.prod(shape)).reshape(shape)
    kw = dict(brightness_temperature_10=290+a, brightness_temperature_11=288+a*.9,
              emissivity_10=np.full(shape,.97), emissivity_11=np.full(shape,.98),
              water_vapor=water, mask=np.zeros(shape,bool))
    kw.update(overrides)
    return Du()(**kw)


BOUNDARIES = [0., 2., 2.5, 3., 3.5, 4., 4.5, 5., 5.5, 6.3]
@pytest.mark.parametrize("w", [v for b in BOUNDARIES for v in (np.nextafter(b,-np.inf),b,np.nextafter(b,np.inf)) if 0<=v<=6.3])
def test_constant_raster_matches_scalar(w):
    np.testing.assert_allclose(run(np.full((3,4),w)), run(w), rtol=0, atol=0)
    a=np.arange(12).reshape(3,4)
    expected=reference.temperature("du-2015",290+a,288+a*.9,np.zeros((3,4)),
                                   np.full((3,4),.97),np.full((3,4),.98),w)
    np.testing.assert_allclose(run(w),expected,rtol=0,atol=2e-10)


def test_mixed_pixels_match_independent_table_and_equation():
    w = np.array([[0,2,2.5,3],[3.5,4,4.5,5],[5.5,6,6.3,np.nan]])
    a=np.arange(12).reshape(3,4)
    expected=reference.temperature("du-2015",290+a,288+a*.9,np.zeros((3,4)),
                                   np.full((3,4),.97),np.full((3,4),.98),w)
    np.testing.assert_allclose(run(w),expected,rtol=0,atol=2e-10,equal_nan=True)


@pytest.mark.parametrize("w", [-1., 6.30001, np.nan, np.inf, -np.inf])
def test_invalid_scalar_rejected(w):
    with pytest.raises(ValueError,match="du-2015"):
        run(w)


def test_invalid_raster_and_thermal_emissivity_masks_no_input_mutation():
    water=np.array([[np.nan,np.inf,-1,6.4],[2,2,2,2],[2,2,2,2.]])
    original=water.copy()
    bt=np.full((3,4),300.); bt[1,0]=0; bt[1,1]=np.inf
    e=np.full((3,4),.97);e[1,2]=0;e[1,3]=1.1
    mask=np.zeros((3,4),bool);mask[2,0]=True
    out=run(water,brightness_temperature_10=bt,emissivity_10=e,mask=mask)
    assert np.isnan(out[:2]).all() and np.isnan(out[2,0])
    assert np.isfinite(out[2,1:]).all() and not np.isinf(out).any()
    np.testing.assert_array_equal(water,original)
    assert mask.sum()==1


@pytest.mark.parametrize("shape", [(1,4),(3,1),(12,)])
def test_no_raster_broadcasting(shape):
    with pytest.raises(InputShapesNotEqual): run(np.ones(shape))


def test_boolean_mask_contract():
    with pytest.raises(InvalidMaskError): run(np.ones((3,4)),mask=np.zeros((3,4),int))


class Scene:
    shape=(25,31)
    product_id="TEST"
    sensor="landsat_8"
    def calibrated(self,window=None,*,exclude_water=False,optical_quantity="radiance"):
        a=np.arange(25*31,dtype=float).reshape(self.shape)
        red=.1+.01*(a%8)
        n=.1+.5*a/a.max()
        bt=280+a/100
        mask=np.zeros(self.shape,bool);mask[8,9]=True
        sl=np.s_[:,:] if window is None else np.s_[window[0]:window[1],window[2]:window[3]]
        return {4:red[sl],5:(red*(1+n)/(1-n))[sl]}, {10:bt[sl],11:(.8*bt+50)[sl]},mask[sl]


def test_scene_raster_tiles_and_chunks_match_full_scene():
    scene=Scene()
    bounds=scene_ndvi_range(scene,block_rows=4)
    full=du_from_scene(scene,pwv_mode="raster",window_size=5,ndvi_range=bounds)
    assert np.isfinite(full.pwv).any()
    for window in [(0,12,0,13),(0,12,13,31),(12,25,0,13),(12,25,13,31)]:
        tile=du_from_scene(scene,window=window,pwv_mode="raster",window_size=5,
                           ndvi_range=bounds,chunk_rows=1)
        sl=np.s_[window[0]:window[1],window[2]:window[3]]
        np.testing.assert_allclose(tile.pwv,full.pwv[sl],rtol=0,atol=1e-10,equal_nan=True)
        np.testing.assert_allclose(tile.lst,full.lst[sl],rtol=0,atol=1e-10,equal_nan=True)


def test_scene_general_unchanged_and_explicit_mean():
    scene=Scene();opt,bt,mask=scene.calibrated()
    from pylstemp import split_window
    general=du_from_scene(scene)
    np.testing.assert_array_equal(general.lst,split_window(bt[10],bt[11],opt[4],opt[5],mask=mask,lst_method="du-2015"))
    mean=du_from_scene(scene,pwv_mode="mean",window_size=5)
    assert mean.provenance["mean_pwv"]==float(np.nanmean(mean.pwv))
    expected=split_window(bt[10],bt[11],opt[4],opt[5],mask=mask,lst_method="du-2015",water_vapor=mean.provenance["mean_pwv"])
    np.testing.assert_array_equal(mean.lst,expected)


def test_scene_missing_pwv_never_falls_back():
    scene=Scene();mask=np.ones(scene.shape,bool)
    raster=du_from_scene(scene,pwv_mode="raster",mask=mask)
    assert np.isnan(raster.lst).all()
    with pytest.raises(ValueError,match="No in-domain"):
        du_from_scene(scene,pwv_mode="mean",mask=mask)
    with pytest.raises(ValueError,match="pending"):
        du_from_scene(scene,pwv_method="ren-2015")
    with pytest.raises(ValueError,match="pwv_mode"):
        du_from_scene(scene,pwv_mode="automatic")


def test_export_provenance_and_masks(tmp_path):
    scene=Scene();result=du_from_scene(scene,pwv_mode="raster",window_size=5)
    written={}
    def write(path,value,*,window,units): written[path.name]=(value,window,units)
    scene.write_geotiff=write
    result.export(scene,tmp_path)
    metadata=json.loads((tmp_path/'provenance.json').read_text())
    assert metadata['chain']=='alternative Wang -> Du'
    assert metadata['pwv_units']=='g/cm2'
    assert set(written)=={'lst_du.tif','lst_invalid.tif','pwv.tif','pwv_raw.tif','pwv_invalid.tif'}
    np.testing.assert_array_equal(written['lst_invalid.tif'][0],~np.isfinite(result.lst))
