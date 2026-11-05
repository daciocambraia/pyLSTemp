"""Behavior regressions for the unified public API."""
import importlib.util
import unittest
import numpy as np
import pylstemp
from pylstemp import emissivity,split_window,optical_correction,list_algorithms

class UnifiedAPI(unittest.TestCase):
    def setUp(self):
        self.t=np.full((5,6),300.);self.u=self.t-2
        self.red=np.ones((5,6));self.nir=np.full((5,6),2.)

    def test_single_channel_prepared_emissivity_routes(self):
        from pylstemp import single_window
        mask = np.zeros(self.t.shape, dtype=bool); mask[0,0] = True
        for method in ("mono-window-2016", "jimenez-munoz-2014-sc"):
            extra = dict(radiance_band_10=np.full(self.t.shape,10.), water_vapor=1.5) if method.endswith("-sc") else {}
            for provider in ("avdan-2016", "rongali-2018"):
                with self.subTest(method=method, provider=provider):
                    e = emissivity(method=provider, band=10, red=self.red, nir=self.nir, mask=mask)
                    auto = single_window(self.t, self.red, self.nir, lst_method=method, emissivity_method=provider, mask=mask, **extra)
                    ready = single_window(self.t, lst_method=method, emissivity_10=e, mask=mask, return_diagnostics=True, **extra)
                    np.testing.assert_array_equal(auto, ready['lst'])
                    self.assertIsNone(ready['ndvi'])
                    self.assertTrue(np.isnan(ready['lst'][0,0]))
                    c = single_window(self.t, lst_method=method, emissivity_10=e, mask=mask, unit='celsius', **extra)
                    np.testing.assert_array_equal(c, auto-273.15)
        for extra in (dict(band_4_red=self.red), dict(emissivity_method='avdan-2016')):
            with self.assertRaises(ValueError):single_window(self.t, emissivity_10=np.full(self.t.shape,.98), **extra)
        with self.assertRaises(Exception):single_window(self.t, emissivity_10=np.ones((2,2)))
        with self.assertRaises(ValueError):single_window(self.t)

    def test_old_entry_points_and_empty_family_are_absent(self):
        for name in ('split_window_from_emissivity','sobrino_2004_tm6','sobrino_2008','fit_chavez','chavez_reflectance','ChavezParameters'):
            self.assertFalse(hasattr(pylstemp,name),name)
            self.assertNotIn(name,pylstemp.__all__)
        import pylstemp.api as api
        self.assertFalse(hasattr(api,'split_window_from_emissivity'))
        self.assertIsNone(importlib.util.find_spec('pylstemp.algorithms.radiative_transfer'))
        self.assertNotIn('radiative_transfer',list_algorithms())
        self.assertEqual(sum(len(v) for k,v in list_algorithms().items() if k!='credit'),14)

    def test_only_jimenez_split_window_is_renamed(self):
        from pylstemp.algorithms.split_window import split_window_registry
        catalog = list_algorithms()
        expected = {'du-2015', 'jimenez-munoz-2014-sw',
                    'price-1984', 'kerr-1992', 'sobrino-1993'}
        self.assertEqual(set(catalog['split_window']), expected)
        self.assertIn('jimenez-munoz-2014-sc', catalog['single_channel'])
        self.assertEqual(split_window_registry.resolve_key('jimenez-munoz-2014'),
                         'jimenez-munoz-2014-sw')
        options = dict(emissivity_10=np.full(self.t.shape, .97),
                       emissivity_11=np.full(self.t.shape, .98),
                       water_vapor=1.5, return_diagnostics=True)
        a = split_window(self.t, self.u, lst_method='jimenez-munoz-2014', **options)
        b = split_window(self.t, self.u, lst_method='jimenez-munoz-2014-sw', **options)
        self.assertEqual(a.keys(), b.keys())
        for key in a:
            if isinstance(a[key], np.ndarray):
                np.testing.assert_array_equal(a[key], b[key])
            else:
                self.assertEqual(a[key], b[key])
        for key in expected:
            self.assertNotEqual(catalog['split_window'][key]['source_review_status'],
                                'Not reviewed')


    def test_jimenez_sc_suffix_and_compatibility_alias(self):
        from pylstemp import single_window
        from pylstemp.algorithms.single_channel import single_channel_registry
        catalog = list_algorithms()['single_channel']
        self.assertIn('jimenez-munoz-2014-sc', catalog)
        self.assertNotIn('jimenez-munoz-sc-2014', catalog)
        self.assertEqual(single_channel_registry.resolve_key('jimenez-munoz-sc-2014'),
                         'jimenez-munoz-2014-sc')
        self.assertNotEqual(catalog['jimenez-munoz-2014-sc']['source_review_status'],
                            'Not reviewed')
        options = dict(radiance_band_10=np.full(self.t.shape, 10.),
                       water_vapor=1.5, return_diagnostics=True)
        a = single_window(self.t, self.red, self.nir,
                          lst_method='jimenez-munoz-sc-2014', **options)
        b = single_window(self.t, self.red, self.nir,
                          lst_method='jimenez-munoz-2014-sc', **options)
        self.assertEqual(a.keys(), b.keys())
        for key in a:
            if isinstance(a[key], np.ndarray):
                np.testing.assert_array_equal(a[key], b[key])
            else:
                self.assertEqual(a[key], b[key])

    def test_catalog_separates_numerical_evidence_and_sensor_applicability(self):
        catalog=list_algorithms(include_inactive=True)
        for family,entries in catalog.items():
            if family=='credit':continue
            for method,item in entries.items():
                with self.subTest(method=method):
                    self.assertEqual(item['evidence']['implementation'],
                                     'independent_synthetic_regression_checked')
                    self.assertEqual(item['evidence']['empirical_accuracy'],
                                     'not_established_by_this_library')
                    self.assertIn('numerical_evidence',item)
                    self.assertIn('empirical_accuracy',item)
        for method in ['price-1984','kerr-1992','sobrino-1993']:
            for sensor in ['landsat_8','landsat_9']:
                self.assertEqual(catalog['split_window'][method]['evidence'][sensor],
                                 'experimental_avhrr_to_tirs_transfer')
        self.assertEqual(catalog['thermal']['brightness']['evidence']['landsat_9'],
                         'scene_metadata_calibration')
        self.assertEqual(catalog['split_window']['du-2015']['evidence']['landsat_9'],
                         'experimental_coefficient_transfer')
        self.assertEqual(catalog['optical_correction']['chavez-cost']['evidence']['landsat_8'],
                         'experimental_tm_to_oli_transfer')

    def test_prepared_pair_matches_optical_route_and_diagnostics(self):
        e10=emissivity(red=self.red,nir=self.nir,method='rongali-2018',band=10)
        e11=emissivity(red=self.red,nir=self.nir,method='rongali-2018',band=11)
        for method,options in [('du-2015',{}),('jimenez-munoz-2014-sw',{'water_vapor':2})]:
            with self.subTest(method=method):
                a=split_window(self.t,self.u,self.red,self.nir,lst_method=method,**options)
                b=split_window(self.t,self.u,emissivity_10=e10,emissivity_11=e11,lst_method=method,return_diagnostics=True,**options)
                np.testing.assert_array_equal(a,b['lst'])
                self.assertIsNone(b['ndvi'])
                self.assertEqual(b['optical_contract']['emissivity_source'],'caller supplied; band/sensor provenance required')
                c=split_window(self.t,self.u,emissivity_10=e10,emissivity_11=e11,lst_method=method,unit='celsius',**options)
                np.testing.assert_array_equal(c,a-273.15)

    def test_kerr_ndvi_with_prepared_pair_has_explicit_inputs(self):
        e10=np.full(self.t.shape,.97);e11=np.full(self.t.shape,.98)
        a=split_window(self.t,self.u,self.red,self.nir,emissivity_10=e10,emissivity_11=e11,lst_method='kerr-1992',optical_quantity='surface_reflectance')
        n=(self.nir-self.red)/(self.nir+self.red)
        b=split_window(self.t,self.u,emissivity_10=e10,emissivity_11=e11,ndvi_image=n,lst_method='kerr-1992')
        np.testing.assert_array_equal(a,b)
        with self.assertRaises(ValueError):split_window(self.t,self.u,emissivity_10=e10,emissivity_11=e11,lst_method='kerr-1992')

    def test_ambiguous_and_partial_routes_are_rejected(self):
        options=[{'emissivity_10':self.red}, {'emissivity_11':self.red},
                 {'emissivity_10':self.red,'emissivity_11':self.red,'band_4_red':self.red,'band_5_nir':self.nir},
                 {'emissivity_10':self.red,'emissivity_11':self.red,'emissivity_method':'rongali-2018'},
                 {'band_4_red':self.red}, {'band_4_red':self.red,'band_5_nir':self.nir,'ndvi_image':self.red}]
        for kw in options:
            with self.subTest(options=list(kw)),self.assertRaises(ValueError):
                split_window(self.t,self.u,lst_method='du-2015',**kw)


    def test_emissivity_selector_and_method_specific_options(self):
        for key in ('avdan-2016','rongali-2018'):
            np.testing.assert_array_equal(emissivity(red=self.red,nir=self.nir,method=key),emissivity(red=self.red,nir=self.nir,emissivity_method=key))
        for kw in ({'method':'avdan-2016','emissivity_method':'avdan-2016'},):
            with self.assertRaises(ValueError):emissivity(red=self.red,nir=self.nir,**kw)

    def test_optical_fit_reuse_and_parameter_conflicts(self):
        rho=np.arange(30,dtype=float).reshape(5,6)/100+.1
        for method in ('chavez-dos','chavez-cost'):
            details=optical_correction(rho,method=method,sun_elevation=30,percentile=0,return_diagnostics=True)
            direct=optical_correction(rho,method=method,sun_elevation=30,percentile=0)
            np.testing.assert_array_equal(details['reflectance'],direct)
            params=details['parameters']
            for tile in (np.s_[:2,:],np.s_[2:,:]):
                np.testing.assert_array_equal(optical_correction(rho[tile],method=method,parameters=params),direct[tile])
            other='chavez-cost' if method=='chavez-dos' else 'chavez-dos'
            with self.assertRaises(ValueError):optical_correction(rho,method=other,parameters=params)
            with self.assertRaises(ValueError):optical_correction(rho,method=method,parameters=params,sun_elevation=30)
        with self.assertRaises(ValueError):optical_correction(rho,method='unknown',sun_elevation=30)
        with self.assertRaises(ValueError):optical_correction(rho)

if __name__=='__main__':unittest.main()
