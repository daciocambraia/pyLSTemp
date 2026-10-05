"""Exhaustive API combinations, numerical oracles and metamorphic checks."""
import unittest
import warnings
import numpy as np
from pylstemp import spectral_index, brightness, emissivity, single_window, split_window, water_vapor
from pylstemp.algorithms import FAMILY_REGISTRIES
from pylstemp.algorithms.spectral_indices import spectral_indices_registry
from pylstemp.exceptions import InputShapesNotEqual, InvalidMaskError, InvalidMethodRequested, InvalidTemperatureUnitError
from scripts import matrix_references as ref

EMI=tuple(FAMILY_REGISTRIES["emissivity"].available_keys())
SINGLE=tuple(FAMILY_REGISTRIES["single_channel"].available_keys())
SPLIT=tuple(FAMILY_REGISTRIES["split_window"].available_keys())
INDICES=tuple(FAMILY_REGISTRIES["spectral_index"].available_keys())

def inputs(dtype=np.float64):
    a=np.arange(144,dtype=float).reshape(12,12)
    n=-.1+.7*a/143
    red=.1+.01*(a%8)
    return tuple(np.asarray(x,dtype=dtype) for x in (280+a/8,.8*(280+a/8)+50,red,red*(1+n)/(1-n),red/2))

def mask_for(shape,mode):
    mask=np.zeros(shape,bool)
    if mode=="one": mask[0,0]=True
    if mode=="all": mask[:]=True
    return mask

class CombinationMatrix(unittest.TestCase):
    pass

def temperature_case(kind,lst,emi,unit,pwv_mode,mask_mode,dtype):
    def test(self):
        t10,t11,red,nir,blue=inputs(dtype)
        mask=mask_for(t10.shape,mask_mode)
        n=ref.ndvi(nir,red)
        w=water_vapor(t10,t11,n,window_size=5)
        finite=w[np.isfinite(w)]
        self.assertGreater(finite.size,0)
        pwv={"none":None,"scalar":float(finite.mean()),"raster":w}[pwv_mode]
        kw=dict(lst_method=lst,emissivity_method=emi,unit=unit,mask=mask)
        with warnings.catch_warnings(),np.errstate(all="ignore"):
            warnings.simplefilter("ignore",RuntimeWarning)
            if kind=="split":
                call=lambda:split_window(t10,t11,red,nir,water_vapor=pwv,**kw)
                if emi=="avdan-2016":
                    with self.assertRaisesRegex(ValueError,"single-channel"):call()
                    return
                if lst=="jimenez-munoz-2014" and pwv is None:
                    with self.assertRaisesRegex(ValueError,"requires water_vapor"):call()
                    return
                if lst=="du-2015" and pwv_mode=="raster":
                    with self.assertRaisesRegex(ValueError, 'scalar'):call()
                    return
            else:
                radiance=774.8853/np.expm1(1321.0789/t10)
                if lst=="jimenez-munoz-sc-2014":
                    call=lambda:single_window(t10,red,nir,radiance_band_10=radiance,water_vapor=pwv,**kw)
                    if pwv is None:
                        with self.assertRaisesRegex(ValueError,"requires radiance_band_10"):call()
                        return
                    if pwv_mode=="scalar" and float(pwv)>3:
                        with self.assertRaisesRegex(ValueError,"within"):call()
                        return
                else:
                    call=lambda:single_window(t10,red,nir,**kw)
            copies=[x.copy() for x in (t10,t11,red,nir,mask)]
            actual=call()
            e10,e11=ref.emissivity(emi,n,red)
            expected=ref.temperature(lst,t10,t11,n,e10,e11,pwv,mask,
                radiance=radiance if kind=="single" else None)
            if unit=="celsius":expected=expected-273.15
            ref.check(actual,expected,atol=2e-10)
            for old,new in zip(copies,(t10,t11,red,nir,mask)):np.testing.assert_array_equal(old,new)
    return test

for kind,methods in (("single",SINGLE),("split",SPLIT)):
    for lst in methods:
        for emi in EMI:
            for unit in ("kelvin","celsius"):
                for mode in (("none",) if kind=="single" and lst=="mono-window-2016" else ("none","scalar","raster")):
                    for mask in ("none","one","all"):
                        for dtype in (np.float32,np.float64):
                            name="_".join(("test",kind,lst,emi,unit,mode,mask,np.dtype(dtype).name)).replace("-","_")
                            setattr(CombinationMatrix,name,temperature_case(kind,lst,emi,unit,mode,mask,dtype))

def index_case(index,dtype,mask_mode):
    def test(self):
        _,_,red,nir,blue=inputs(dtype)
        mask=mask_for(red.shape,mask_mode)
        kw=dict(nir=nir,red=red,mask=mask)
        actual=spectral_index(index,**kw)
        ref.check(actual,ref.spectral(index,nir,red,blue,mask),atol=1e-13)
        if index=="ndvi":
            legacy=spectral_indices_registry.create("ndvi")
            ref.check(legacy(band_5_nir=nir,band_4_red=red,mask=mask),actual,atol=0)
    return test

for index in INDICES:
    for dtype in (np.float32,np.float64):
        for mask in ("none","one","all"):
            setattr(CombinationMatrix,"test_index_%s_%s_%s"%(index,np.dtype(dtype).name,mask),index_case(index,dtype,mask))

def emissivity_case(method,band):
    def test(self):
        n=np.array([[-1,-.1,0,.15,.2,.35,.48,.5,.500001,1,np.nan,np.inf,1.01]])
        red=np.full(n.shape,.2)
        actual=emissivity(n,band,band_4_red=red,emissivity_method=method)
        ref.check(actual,ref.emissivity(method,n,red)[band-10])
    return test

for method in EMI:
    for band in (10,11):
        setattr(CombinationMatrix,"test_emissivity_%s_b%s"%(method.replace("-","_"),band),emissivity_case(method,band))

def brightness_case(sensor,band,alias,overrides,mask_mode):
    def test(self):
        a=np.array([[0.,-1.,np.nan,10000.,20000.,30000.]])
        mask=mask_for(a.shape,mask_mode)
        k1,k2,gain,bias=ref.THERMAL[sensor,band]
        kw={}
        if overrides:gain,bias=.0003,.2;kw=dict(rad_gain=gain,rad_bias=bias)
        actual=brightness(a,band=alias,sensor=sensor,mask=mask,**kw, input_quantity="dn")
        ref.check(actual,ref.brightness(a,k1,k2,gain,bias,mask),atol=1e-10)
    return test

for sensor in ("landsat_8","landsat_9"):
    for band in (10,11):
        for alias in (band,str(band),"b"+str(band),"band_"+str(band)):
            for overrides in (False,True):
                for mask in ("none","one","all"):
                    name="test_brightness_%s_%s_%s_%s_%s"%(sensor,band,str(alias),type(alias).__name__+str(overrides),mask)
                    setattr(CombinationMatrix,name,brightness_case(sensor,band,alias,overrides,mask))



class DeepContracts(unittest.TestCase):
    def test_wang_chunk_and_halo_invariance_across_128_column_boundary(self):
        rng=np.random.default_rng(704)
        a=290+rng.uniform(0,10,(25,145))
        b=.8*a+50
        n=rng.uniform(-.1,.6,a.shape)
        mask=np.zeros(a.shape,bool);mask[10,127]=True
        for groups in (1,3,5):
            whole=water_vapor(a,b,n,window_size=5,group_count=groups,mask=mask,ndvi_range=(-.1,.6),chunk_rows=1)
            batched=water_vapor(a,b,n,window_size=5,group_count=groups,mask=mask,ndvi_range=(-.1,.6),chunk_rows=8)
            ref.check(whole,batched,atol=1e-12)
            tile=water_vapor(a[5:20,120:140],b[5:20,120:140],n[5:20,120:140],
                window_size=5,group_count=groups,mask=mask[5:20,120:140],ndvi_range=(-.1,.6))
            ref.check(whole[7:18,122:138],tile[2:-2,2:-2],atol=1e-12)

    def test_wang_offset_and_common_scale_invariance(self):
        a,b,red,nir,_=inputs()
        n=ref.ndvi(nir,red)
        first=water_vapor(a,b,n,window_size=5)
        ref.check(first,water_vapor(a+10,b+15,n,window_size=5),atol=1e-10)
        ref.check(first,water_vapor(2*a,2*b,n,window_size=5),atol=1e-10)

    def test_wang_parameter_domains_and_degenerate_windows(self):
        a,b,red,nir,_=inputs()
        n=ref.ndvi(nir,red)
        for kwargs in (dict(window_size=2),dict(window_size=4),dict(window_size=True),
                       dict(group_count=0),dict(group_count=1.5),dict(chunk_rows=0),
                       dict(ndvi_range=(.5,.2)),dict(ndvi_range=(np.nan,1)),
                       dict(ndvi_range=(0,.2))):
            with self.subTest(kwargs=kwargs),self.assertRaises(ValueError):water_vapor(a,b,n,**kwargs)
        with self.assertRaises(ValueError):water_vapor(a.ravel(),b.ravel(),n.ravel())
        flat=water_vapor(a*0+300,b*0+298,n)
        self.assertTrue(np.isnan(flat).all())
        self.assertTrue(np.isnan(water_vapor(a,b,n,mask=np.ones(a.shape,bool))).all())

    def test_shape_mask_unit_and_unknown_method_errors(self):
        a,b,red,nir,blue=inputs()
        for call in (lambda:spectral_index("ndvi",nir=nir,red=red[:1]),
                     lambda:single_window(a,red[:1],nir),
                     lambda:split_window(a,b[:1],red,nir,lst_method="du-2015"),
                     lambda:emissivity(ref.ndvi(nir,red),10,band_4_red=red[:1]),
                     lambda:water_vapor(a,b,ref.ndvi(nir,red)[:1])):
            with self.assertRaises(InputShapesNotEqual):call()
        for call in (lambda:spectral_index("ndvi",nir=nir,red=red,mask=np.zeros(a.shape,int)),
                     lambda:brightness(a,10,"landsat_8",mask=np.zeros(a.shape,int), input_quantity="dn"),
                     lambda:single_window(a,red,nir,mask=np.zeros(a.shape,int)),
                     lambda:split_window(a,b,red,nir,lst_method="du-2015",mask=np.zeros(a.shape,int)),
                     lambda:water_vapor(a,b,ref.ndvi(nir,red),mask=np.zeros(a.shape,int))):
            with self.assertRaises(InvalidMaskError):call()
        with self.assertRaises(InvalidTemperatureUnitError):single_window(a,red,nir,unit="fahrenheit")
        for call in (lambda:spectral_index("not_registered",nir=nir,red=red),
                     lambda:emissivity(ref.ndvi(nir,red),10,emissivity_method="not_registered"),
                     lambda:single_window(a,red,nir,lst_method="not_registered"),
                     lambda:split_window(a,b,red,nir,lst_method="not_registered"),
                     lambda:water_vapor(a,b,ref.ndvi(nir,red),method="not_registered")):
            with self.assertRaises(InvalidMethodRequested):call()

    def test_pwv_sensitivity_and_unused_parameters(self):
        a,b,red,nir,_=inputs()
        for method in ("price-1984","kerr-1992","sobrino-1993"):
            with warnings.catch_warnings():
                warnings.simplefilter("ignore",RuntimeWarning)
                without=split_window(a,b,red,nir,lst_method=method)
                supplied=split_window(a,b,red,nir,lst_method=method,water_vapor=np.full(a.shape,3.))
            ref.check(without,supplied,atol=0)
        for method in ("du-2015","jimenez-munoz-2014"):
            x=split_window(a,b,red,nir,lst_method=method,water_vapor=1.)
            y=split_window(a,b,red,nir,lst_method=method,water_vapor=4.)
            self.assertGreater(float(np.nanmax(np.abs(x-y))),.01)

    def test_jimenez_invalid_pwv_raster_and_constant_equivalence(self):
        a,b,red,nir,_=inputs()
        scalar=split_window(a,b,red,nir,lst_method="jimenez-munoz-2014",water_vapor=2.)
        field=split_window(a,b,red,nir,lst_method="jimenez-munoz-2014",water_vapor=np.full(a.shape,2.))
        ref.check(scalar,field,atol=0)
        bad=np.full(a.shape,2.);bad[0,:3]=[-1,np.inf,np.nan]
        result=split_window(a,b,red,nir,lst_method="jimenez-munoz-2014",water_vapor=bad)
        self.assertTrue(np.isnan(result[0,:3]).all())
        for value in (-1,np.inf,np.nan):
            with self.assertRaises(ValueError):split_window(a,b,red,nir,lst_method="jimenez-munoz-2014",water_vapor=value)

    def test_case_insensitive_methods_and_units(self):
        a,b,red,nir,_=inputs()
        x=single_window(a,red,nir,lst_method="MONO-WINDOW-2016",emissivity_method="GOPINADH-2018",unit="CELSIUS")
        y=single_window(a,red,nir,emissivity_method="gopinadh-2018")-273.15
        ref.check(x,y,atol=0)
        with self.assertRaisesRegex(ValueError,"single-channel"):
            split_window(a,b,red,nir,lst_method="du-2015",emissivity_method="AVDAN-2016")
