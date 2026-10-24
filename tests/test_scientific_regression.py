"""Small independent source regressions; no articles, imagery or local fixtures.

Oracles transcribe equations/tables cited in pylstemp/method_cards.json.
Production coefficients/helpers are never used to construct expected values.
Agreement establishes numerical behavior, not empirical accuracy.
"""
import json
from pathlib import Path
import unittest
import warnings
import numpy as np
import pylstemp
from pylstemp import emissivity, single_window, split_window, water_vapor
from pylstemp.calibration import toa_radiance, toa_reflectance, brightness_from_mtl, quality_mask
from pylstemp import optical_correction
from pylstemp.exceptions import InputShapesNotEqual
from pylstemp.workflows import du_from_scene, scene_ndvi_range


class ScientificRegression(unittest.TestCase):
    def test_mtl_calibration_units_and_sensor_separation(self):
        # USGS LSDS-1747, Sections 4.7.2.5 and 4.7.3.4.
        for sensor in ('LANDSAT_8', 'LANDSAT_9'):
            with self.subTest(sensor=sensor):
                m=dict(SPACECRAFT_ID=sensor, PROCESSING_LEVEL='L1TP', SUN_ELEVATION=30,
                       RADIANCE_MULT_BAND_10=.002, RADIANCE_ADD_BAND_10=.1,
                       K1_CONSTANT_BAND_10=800., K2_CONSTANT_BAND_10=1300.,
                       REFLECTANCE_MULT_BAND_4=.00002, REFLECTANCE_ADD_BAND_4=-.1)
                dn=np.array([1000.,5000.,0.])
                np.testing.assert_allclose(toa_radiance(dn,metadata=m,band=10)[:2],[2.1,10.1])
                expected=1300/np.log1p(800/np.array([2.1,10.1]))
                np.testing.assert_allclose(brightness_from_mtl(dn,metadata=m,band=10)[:2],expected)
                np.testing.assert_allclose(toa_reflectance(dn,metadata=m,band=4)[:2],[-.16,0],atol=1e-16)
                self.assertTrue(np.isnan(brightness_from_mtl(dn,metadata=m,band=10)[2]))
                m['PROCESSING_LEVEL']='L2SP'
                with self.assertRaises(ValueError): toa_radiance(dn,metadata=m,band=10)

    def test_qa_mask(self):
        qa=np.array([0,1,2,4,8,16,32,128],dtype=np.uint16)
        np.testing.assert_array_equal(quality_mask(qa),[False,True,True,True,True,True,True,False])
        self.assertTrue(quality_mask(qa,exclude_water=True)[-1])

    def test_avdan_endmembers_and_mixed_branch(self):
        n=np.array([[-.1,.1,.2,.35,.5,.8]])
        expected=[[.991,.966,.971,.97275,.978,.973]]
        np.testing.assert_allclose(emissivity(n),expected,atol=1e-14)

    def test_rongali_linear_fraction_both_bands(self):
        n=np.array([0,.15,.315,.48,.8])
        for band,expected in [(10,[.971,.971,.979,.987,.987]),(11,[.977,.977,.983,.989,.989])]:
            with self.subTest(band=band):
                np.testing.assert_allclose(emissivity(n,band=band,emissivity_method='gopinadh-2018'),expected)

    def test_sobrino_2004_native_tm6(self):
        result=emissivity(np.array([.1,.2,.35,.5,.8]),method="sobrino-2004-tm6",band=6)
        self.assertTrue(np.isnan(result[0]))
        np.testing.assert_allclose(result[1:],[.986,.987,.990,.99])

    def test_sobrino_2008_both_variants(self):
        n=np.array([.1,.35,.8]); es=.96; ev=.98
        np.testing.assert_allclose(emissivity(n,method="sobrino-2008",soil_emissivity=es,vegetation_emissivity=ev),[.96,.965,.98])
        expected=[.97-.1*.2,.965+(1-.96)*.98*.55*.75,.985]
        np.testing.assert_allclose(emissivity(n,method="sobrino-2008",soil_emissivity=es,vegetation_emissivity=ev,
            variant='full',red_surface=np.full(3,.2),soil_red_coefficients=(.97,-.1)),expected)

    def test_mono_window_absolute_kelvin(self):
        t=np.array([[290.,300.]]); red=np.ones((1,2)); nir=np.full((1,2),3.) # NDVI=.5, e=.978
        expected=t/(1+10.895e-6*t/.01438*np.log(.978))
        np.testing.assert_allclose(single_window(t,red,nir),expected)
        np.testing.assert_allclose(single_window(t,red,nir,unit='celsius'),expected-273.15)

    def test_jimenez_single_channel_polynomial(self):
        t=np.array([[295.,305.]]); L=np.array([[8.,10.]]); w=2.; e=.978
        p1=.04019*w*w+.02916*w+1.01523
        p2=-.38333*w*w-1.50294*w+.20324
        p3=.00918*w*w+1.36072*w-.27514
        expected=t*t/(1324*L)*((p1*L+p2)/e+p3)+t-t*t/1324
        np.testing.assert_allclose(single_window(t,np.ones((1,2)),np.full((1,2),3.),
            lst_method='jimenez-munoz-2014-sc',radiance_band_10=L,water_vapor=w),expected)
        with self.assertRaises(ValueError):
            single_window(t,np.ones((1,2)),np.full((1,2),3.),lst_method='jimenez-munoz-2014-sc',radiance_band_10=L,water_vapor=3.01)

    def test_du_all_rows_and_overlaps(self):
        # Du 2015 Table1, b0..b7, independently transcribed.
        rows=[(-2.78009,1.01408,.15833,-.34991,4.04487,3.55414,-8.88394,.09152),
              (11.00824,.95995,.17243,-.28852,7.11492,.42684,-6.62025,-.06381),
              (9.62610,.96202,.13834,-.17262,7.87883,5.17910,-13.26611,-.07603),
              (.61258,.99124,.10051,-.09664,7.85758,6.86626,-15.00742,-.01185),
              (-.34808,.98123,.05599,-.03518,11.96444,9.06710,-14.74085,-.20471),
              (-.41165,1.00522,.14543,-.27297,4.06655,-6.92512,-18.27461,.24468)]
        intervals=[(0,2.5),(2,3.5),(3,4.5),(4,5.5),(5,6.3)]
        e=(.97+.98)/2; de=.97-.98; mean=299.; d=2.
        f=np.array([1,mean,(1-e)/e*mean,de/e**2*mean,d/2,(1-e)/e*d/2,de/e**2*d/2,d*d])
        for w in [None,0,1,2,2.5,3,3.5,4,4.5,5,5.5,6.3]:
            with self.subTest(w=w):
                coeff=[rows[-1]] if w is None else [r for (lo,hi),r in zip(intervals,rows) if lo<=w<=hi]
                expected=np.mean([np.dot(r,f) for r in coeff])
                actual=split_window(np.array([300.]),np.array([298.]),emissivity_10=np.array([.97]),emissivity_11=np.array([.98]),lst_method='du-2015',water_vapor=w)
                np.testing.assert_allclose(actual,expected,atol=2e-10,rtol=0)

    def test_legacy_and_jimenez_split_equations(self):
        t=np.array([300.]); u=np.array([298.]); a=np.array([.97]); b=np.array([.98]); d=2.; w=2.
        cases={'jimenez-munoz-2014-sw':300+1.378*d+.183*d*d-.268+(54.3-2.238*w)*.025+(-129.2+16.4*w)*(-.01),
               'sobrino-1993':300+(1.060+.46*d)*d+53*.03-53*(-.01),
               'price-1984':(300+3.33*d)*(5.5-.97)/4.5+.75*298*(-.01),
               'kerr-1992':300*(3.1+.5*.5)+298*(-2.1-.5*.5)+3.1-5.5*.5}
        with warnings.catch_warnings():
            warnings.simplefilter('ignore',RuntimeWarning)
            for key,expected in cases.items():
                with self.subTest(method=key):
                    actual=split_window(t,u,emissivity_10=a,emissivity_11=b,lst_method=key,
                        water_vapor=w if key=='jimenez-munoz-2014-sw' else None,ndvi_image=np.array([.415]) if key=='kerr-1992' else None)
                    np.testing.assert_allclose(actual,expected,rtol=0,atol=2e-10)

    def test_rozenstein_profiles_and_temperature_tables(self):
        profiles=[('us-standard-1976',1.0286,-.1146,1.0083,-.1568),('midlatitude-summer',1.0335,-.1134,1.0078,-.1546)]
        tables=[('0-60',-64.4661,.4398,-68.8678,.4755),('0-30',-59.1391,.4213,-63.3921,.4565),('0-40',-60.9196,.4276,-65.2240,.4629),('10-40',-62.8065,.4338,-67.1728,.4694),('10-50',-64.6081,.4399,-69.0215,.4756)]
        for profile,i,s,j,r in profiles:
            for interval,a,b,c,d in tables:
                with self.subTest(profile=profile,interval=interval):
                    t10,t11=299.,298.; w=1.; e10,e11=.97,.98
                    p,q=i+s*w,j+r*w; C=e10*p; D=e11*q
                    x=(1-p)*(1+(1-e10)*p); y=(1-q)*(1+(1-e11)*q)
                    den=y*C-x*D; A=x/den; E1=y*(1-C-x)/den; E2=x*(1-D-y)/den
                    expected=E1*a+E2*c+(1+A+E1*b)*t10-(A+E2*d)*t11
                    lo,hi=map(float,interval.split('-'))
                    if not lo+273.15<=expected<=hi+273.15: expected=np.nan
                    actual=split_window(np.array([t10]),np.array([t11]),emissivity_10=np.array([e10]),emissivity_11=np.array([e11]),lst_method='rozenstein-2014',water_vapor=w,atmospheric_profile=profile,temperature_range=interval)
                    np.testing.assert_allclose(actual,expected,rtol=0,atol=2e-10)

    def test_wang_and_ren_are_distinct_estimators(self):
        x=np.arange(121,dtype=float).reshape(11,11)/10+290; y=.9*x+25
        n=np.full(x.shape,.1)
        wang=water_vapor(x,y,n,method='wang-2015',window_size=5)
        np.testing.assert_allclose(wang[2:-2,2:-2],14.158-13.412*(.9939*.9),atol=1e-10)
        ren=water_vapor(x,y,n,method='ren-2015',window_size=5,return_diagnostics=True)
        np.testing.assert_allclose(ren['water_vapor'][2:-2,2:-2],-9.674*.9**2+.653*.9+9.087,atol=1e-10)
        np.testing.assert_allclose(ren['chi_squared'][2:-2,2:-2],1,atol=1e-14)
        self.assertFalse(np.isclose(wang[5,5],ren['water_vapor'][5,5]))
        self.assertTrue(np.isnan(water_vapor(np.full_like(x,300),np.full_like(x,298),n,method='ren-2015')).all())

    def test_chavez_scene_fit_and_reusable_tiles(self):
        rho=np.array([[.1,.2],[.3,.4]])
        for method,divisor in [('dos',1.),('cost',.5)]:
            key='chavez-'+method
            p=optical_correction(rho,sun_elevation=30,method=key,percentile=0,return_diagnostics=True)['parameters']
            expected=(rho-.09)/divisor
            np.testing.assert_allclose(optical_correction(rho,method=key,parameters=p),expected)
            np.testing.assert_allclose(optical_correction(rho[:1],method=key,parameters=p),expected[:1])

    def test_internal_ndvi_diagnostics_mask_and_declaration(self):
        t=np.array([300.,301.,302.]); red=np.ones(3); nir=np.array([1.,3.,1.])
        mask=np.array([False,False,True])
        result=split_window(t,t-2,red,nir,lst_method='du-2015',mask=mask,
                            return_diagnostics=True,optical_quantity='radiance')
        np.testing.assert_allclose(result['ndvi'],[0,.5,np.nan],equal_nan=True)
        self.assertTrue(result['invalid_mask'][-1])
        self.assertEqual(result['optical_contract']['status'],'declared_quantity_matches_source_interpretation')
        self.assertFalse(hasattr(pylstemp,'spectral_index'))
        with self.assertRaises(ValueError):
            split_window(t,t-2,red,nir,lst_method='du-2015',optical_quantity='dn')

    def test_physical_masks_and_no_broadcasting(self):
        t=np.array([300.,0.,np.nan,300.]); u=np.full(4,298.); e=np.array([.97,.97,.97,1.1])
        out=split_window(t,u,emissivity_10=e,emissivity_11=np.full(4,.98),lst_method='du-2015')
        self.assertTrue(np.isnan(out[1:]).all())
        with self.assertRaises(InputShapesNotEqual):
            split_window(t,u,emissivity_10=np.ones(2),emissivity_11=np.ones(4),lst_method='du-2015')

    def test_catalog_has_audited_contract_for_every_registered_method(self):
        cards=json.loads(Path(pylstemp.__file__).with_name('method_cards.json').read_text(encoding='utf8'))
        self.assertEqual(len(cards),20)
        names={c['method'] for c in cards}
        for family, entries in pylstemp.list_algorithms().items():
            if family=='credit': continue
            for key, entry in entries.items():
                self.assertIn("sobrino-2008-simplified" if key=="sobrino-2008" else key,names)
                self.assertIn('Primary',entry['source_review_status'])
        self.assertEqual(len({c['method'] for c in cards}),20)
        for card in cards:
            self.assertEqual(len(card['source_sha256']),64)
            self.assertNotIn('not re-audited',card['source_review_status'])
            self.assertIn('equation',card)
            self.assertTrue(card['coefficients'])


class SyntheticScene:
    shape=(25,31); product_id='INDEPENDENT_SYNTHETIC'; sensor='landsat_8'
    def calibrated(self,window=None,*,exclude_water=False,optical_quantity='radiance'):
        r,c=np.indices(self.shape); x=290+r*.4+c*.1; y=.9*x+25
        n=.1+.6*c/30; red=np.ones(self.shape); nir=(1+n)/(1-n)
        window=(0,25,0,31) if window is None else window
        a,b,d,e=window; sl=np.s_[a:b,d:e]
        return {4:red[sl],5:nir[sl]},{10:x[sl],11:y[sl]},np.zeros(x[sl].shape,bool)


class WorkflowRegression(unittest.TestCase):
    def test_halo_tiles_global_bounds_and_chunks(self):
        scene=SyntheticScene(); bounds=scene_ndvi_range(scene,block_rows=4)
        full=du_from_scene(scene,pwv_mode='raster',window_size=5,ndvi_range=bounds,diagnostics=True)
        for method in ('wang-2015','ren-2015'):
            if method=='ren-2015': full=du_from_scene(scene,pwv_mode='raster',pwv_method=method,window_size=5,diagnostics=True)
            for win in [(0,12,0,13),(0,12,13,31),(12,25,0,13),(12,25,13,31)]:
                with self.subTest(method=method,window=win):
                    kw={'ndvi_range':bounds} if method=='wang-2015' else {}
                    tile=du_from_scene(scene,window=win,pwv_mode='raster',pwv_method=method,window_size=5,chunk_rows=1,diagnostics=True,**kw)
                    sl=np.s_[win[0]:win[1],win[2]:win[3]]
                    np.testing.assert_allclose(tile.lst,full.lst[sl],rtol=0,atol=2e-9,equal_nan=True)
                    np.testing.assert_allclose(tile.pwv,full.pwv[sl],rtol=0,atol=2e-9,equal_nan=True)
                    np.testing.assert_array_equal(tile.intermediates['ndvi'],full.intermediates['ndvi'][sl])

    def test_provenance_is_serializable_and_numerical_defaults_unchanged(self):
        scene=SyntheticScene(); plain=du_from_scene(scene); rich=du_from_scene(scene,diagnostics=True)
        np.testing.assert_array_equal(plain.lst,rich.lst)
        self.assertIsNone(plain.intermediates)
        self.assertEqual(len(rich.intermediates),7)
        json.dumps(rich.provenance,allow_nan=False)
        self.assertEqual(len(rich.provenance['package_sha256']),64)
        self.assertIn('du-2015',rich.provenance['source_method_cards'])


if __name__=='__main__':
    unittest.main()
