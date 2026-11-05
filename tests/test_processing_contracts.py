"""General input, diagnostic and export contracts using synthetic measurements."""
import json
from pathlib import Path
import numpy as np
import pytest
from pylstemp import calibrate, emissivity, single_window, split_window, water_vapor, optical_correction, quality_mask
from pylstemp.exceptions import ApplicabilityWarning, DomainWarning, UnusedParameterWarning
from pylstemp.quality import QualityFlag
from pylstemp.workflows import du_from_scene


def metadata():
    return dict(SPACECRAFT_ID="LANDSAT_8",PROCESSING_LEVEL="L1TP",RADIANCE_MULT_BAND_10=.01,
        RADIANCE_ADD_BAND_10=.1,K1_CONSTANT_BAND_10=774.8853,K2_CONSTANT_BAND_10=1321.0789)


def test_masked_inputs_do_not_reveal_hidden_values_and_booleans_are_explicit():
    dn=np.ma.array([1000.,2000.],mask=[False,True])
    result=calibrate(dn,method="toa-radiance",metadata=metadata(),band=10)
    np.testing.assert_allclose(result,[10.1,np.nan],equal_nan=True)
    with pytest.raises(ValueError,match="exclude_water must be boolean"):
        quality_mask("missing","missing",reference_path="missing",exclude_water="False")
    with pytest.raises(ValueError,match="return_diagnostics must be boolean"):
        emissivity([.3],return_diagnostics=1)
    with pytest.raises(ValueError,match="calibrate"):
        calibrate([1+2j],method="toa-radiance",metadata=metadata(),band=10)


def test_six_families_have_json_safe_processing_identity_and_selected_result():
    r,c=np.indices((7,7));t=295+r*.2+c*.4;u=298+.85*(t-300);red=np.ones(t.shape);nir=red*2
    cases=[calibrate([1000.],method="toa-radiance",metadata=metadata(),band=10,return_diagnostics=True),
        emissivity(red=red,nir=nir,method="rongali-2018",return_diagnostics=True,optical_quantity="radiance"),
        single_window(t,emissivity_10=np.full(t.shape,.98),return_diagnostics=True),
        split_window(t,u,emissivity_10=np.full(t.shape,.97),emissivity_11=np.full(t.shape,.98),method="du-2015",return_diagnostics=True),
        water_vapor(t,u,red=red,nir=nir,window_size=5,return_diagnostics=True),
        optical_correction(np.linspace(.1,.3,49).reshape(7,7),method="chavez-dos-1996",sun_elevation=45,return_diagnostics=True)]
    assert len({item['family'] for item in cases})==6
    for item in cases:
        assert item['metadata']['method']==item['method']
        assert item['metadata']['version']=='2.0.0'
        json.dumps(item['metadata'],allow_nan=False)
        np.testing.assert_array_equal(item['invalid_mask'],~np.isfinite(item['result']))
        if 'screened_result' in item:np.testing.assert_array_equal(item['result'],item['screened_result'])


def test_pwv_details_preserve_default_screening_and_true_raw_values():
    rng=np.random.default_rng(14);x=300+np.arange(49).reshape(7,7)*.2
    y=295+.7*(x-300)+rng.normal(0,2.5,x.shape);nd=np.full(x.shape,.6)
    plain=water_vapor(x,y,ndvi_image=nd,window_size=5,group_count=1)
    details=water_vapor(x,y,ndvi_image=nd,window_size=5,group_count=1,return_diagnostics=True)
    np.testing.assert_array_equal(details['water_vapor'],plain)
    assert np.isfinite(details['raw_water_vapor'][3,3]) and np.isnan(plain[3,3])
    raw=water_vapor(x,y,ndvi_image=nd,window_size=5,group_count=1,quality_mode='diagnostic')
    np.testing.assert_array_equal(details['raw_water_vapor'],raw['water_vapor'])


def test_screened_lst_diagnostics_keep_upstream_rejection_reasons():
    t=np.full((2,2),300.);e=np.full(t.shape,.98);up=np.full(t.shape,int(QualityFlag.LOW_QUALITY),dtype='uint16')
    details=single_window(t,emissivity_10=e,return_diagnostics=True,pwv_quality_flags=up)
    np.testing.assert_array_equal(details['lst'],single_window(t,emissivity_10=e))
    assert np.all(details['quality_flags'] & QualityFlag.LOW_QUALITY)
    assert not details['quality_acceptable'].any()


def test_warning_categories_separate_applicability_domains_and_unused_inputs():
    t=np.array([300.]);u=t-2;e=np.array([.98])
    with pytest.warns(ApplicabilityWarning):split_window(t,u,method='price-1984',emissivity_10=e,emissivity_11=e)
    with pytest.warns(DomainWarning):split_window(t,u,method='jimenez-munoz-2014',water_vapor=6.1,emissivity_10=e,emissivity_11=e)
    with pytest.warns(UnusedParameterWarning):
        with pytest.warns(ApplicabilityWarning):split_window(t,u,method='price-1984',water_vapor=1.,emissivity_10=e,emissivity_11=e)


class SyntheticScene:
    shape=(9,11);product_id='SYNTHETIC';sensor='landsat_8'
    def calibrated(self,window=None,*,exclude_water=False,optical_quantity='radiance'):
        r,c=np.indices(self.shape);x=295+r*.4+c*.2;y=298+.85*(x-300)
        a,b,d,e=(0,9,0,11) if window is None else window;sl=np.s_[a:b,d:e]
        invalid=np.zeros(self.shape,bool);invalid[0,0]=True
        return {4:np.ones(self.shape)[sl],5:np.full(self.shape,3.)[sl]}, {10:x[sl],11:y[sl]},invalid[sl]


def test_complete_raw_and_screened_scene_chains_and_mean_flags():
    scene=SyntheticScene()
    screened=du_from_scene(scene,pwv_mode='mean',window_size=5)
    raw=du_from_scene(scene,pwv_mode='mean',window_size=5,quality_mode='diagnostic')
    np.testing.assert_array_equal(raw.lst_screened,screened.lst)
    np.testing.assert_array_equal(raw.lst_raw,screened.lst_raw)
    assert np.isnan(raw.lst[0,0])
    assert np.all(raw.quality_flags & QualityFlag.SPATIAL_MEAN_PWV)
    assert raw.provenance['mean_contributor_count']>0
    assert raw.provenance['screened_mean_contributor_count']>0
    json.dumps(raw.provenance,allow_nan=False)


@pytest.fixture
def reference(tmp_path):
    rasterio=pytest.importorskip('rasterio')
    from rasterio.transform import from_origin
    path=tmp_path/'reference.tif'
    with rasterio.open(path,'w',driver='GTiff',height=9,width=11,count=1,dtype='uint16',
        crs='LOCAL_CS["Export fixture",LOCAL_DATUM["Export fixture",0],UNIT["metre",1]]',
        transform=from_origin(100,1000,30,30)) as dst:dst.write(np.ones((9,11),dtype='uint16'),1)
    return path


def writer_scene(reference,backend):
    from pylstemp.scene import LandsatScene
    scene=object.__new__(LandsatScene);scene.shape=(9,11);scene.product_id='SYNTHETIC';scene.backend=backend
    if backend=='rasterio':
        import rasterio
        source=rasterio.open(reference)
    else:
        from PIL import Image
        source=Image.open(reference)
    scene.sources={'B4':source}
    return scene


@pytest.mark.parametrize('backend',['rasterio','pillow'])
@pytest.mark.parametrize('dtype',['bool','uint16','float32'])
def test_typed_geotiff_roundtrip_keeps_grid_zero_and_metadata(tmp_path,reference,backend,dtype):
    rasterio=pytest.importorskip('rasterio')
    if backend=='pillow':pytest.importorskip('PIL')
    data=np.arange(12).reshape(3,4)
    data=(data%2).astype(bool) if dtype=='bool' else data.astype(dtype)
    scene=writer_scene(reference,backend);out=tmp_path/f'{backend}-{dtype}.tif'
    try:scene.write_geotiff(out,data,window=(1,4,2,6),units='test',metadata=dict(family='test',method='synthetic'))
    finally:scene.close()
    with rasterio.open(out) as src:
        np.testing.assert_array_equal(src.read(1),data)
        assert src.transform.c==160 and src.transform.f==970
        assert src.dtypes[0]==('uint8' if dtype=='bool' else dtype)
        assert not np.ma.getmaskarray(src.read(1,masked=True)).any()
        if dtype!='float32':assert src.nodata is None
        if backend=='rasterio':assert json.loads(src.tags()['processing_metadata'])['method']=='synthetic'
        else:assert json.loads(src.tags()['TIFFTAG_IMAGEDESCRIPTION'])['method']=='synthetic'


def test_export_rejects_lossy_integer_conversion_before_writing(tmp_path,reference):
    scene=writer_scene(reference,'rasterio');out=tmp_path/'bad.tif'
    try:
        with pytest.raises(ValueError,match='lose values'):
            scene.write_geotiff(out,np.full(scene.shape,65536),dtype='uint16')
        assert not out.exists()
    finally:scene.close()


def test_scene_export_keeps_flags_legend_and_both_chains(tmp_path,reference):
    result=du_from_scene(SyntheticScene(),pwv_mode='raster',window_size=5,quality_mode='diagnostic')
    scene=writer_scene(reference,'rasterio')
    try:result.export(scene,tmp_path/'products')
    finally:scene.close()
    import rasterio
    with rasterio.open(tmp_path/'products/quality_flags.tif') as src:
        assert src.dtypes==('uint16',) and src.nodata is None
        np.testing.assert_array_equal(src.read(1),result.quality_flags)
    with rasterio.open(tmp_path/'products/lst_invalid.tif') as src:assert src.dtypes==('uint8',) and src.nodata is None
    with rasterio.open(tmp_path/'products/pwv_raw.tif') as src:
        assert src.tags()['family']=='water_vapor' and src.tags()['method']=='wang-2015'
        assert src.tags()['quality_mode']=='diagnostic'
    assert json.loads((tmp_path/'products/quality_legend.json').read_text())['INPUT_MASKED']['value']==1
    assert (tmp_path/'products/lst_raw.tif').is_file() and (tmp_path/'products/lst_screened.tif').is_file()


def test_scene_quality_mask_preserves_nodata_even_when_its_bits_are_clear(tmp_path,reference):
    import rasterio
    scene=writer_scene(reference,'rasterio')
    with rasterio.open(reference) as src:profile=src.profile.copy()
    qa=np.full(scene.shape,64,dtype='uint16');qa[1,1]=0
    sat=np.zeros(scene.shape,dtype='uint16')
    try:
        for token,data,nodata in [('QA_PIXEL',qa,0),('QA_RADSAT',sat,None)]:
            path=tmp_path/(token+'.tif');profile.update(nodata=nodata)
            with rasterio.open(path,'w',**profile) as dst:dst.write(data,1)
            scene.sources[token]=rasterio.open(path)
        mask=scene.quality_mask()
        assert mask.sum()==1 and mask[1,1]
        with pytest.raises(ValueError,match='four integer bounds'):scene.read('B4',(0,1.5,0,2))
    finally:scene.close()
