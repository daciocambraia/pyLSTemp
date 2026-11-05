"""Independent radiance-space checks of Chavez (1996), Eq.2, pp.1027-1029.

DOS and COST share Lhaze in that paper. These checks establish numerical
consistency with those assumptions, not atmospheric accuracy for OLI.
"""
import unittest
import numpy as np
from pylstemp import optical_correction
from pylstemp.optical import ChavezParameters


class ChavezReferenceTests(unittest.TestCase):
    def test_radiance_equation_multiple_bands_and_solar_angles(self):
        # E0 includes Earth-Sun distance; independent physical units W/m2/um.
        E0 = np.array([1500., 1000.])
        L = np.array([[20., 25.], [50., 50.]])
        Ldark = np.array([8., 4.])
        for elevation in [25., 47.08529577, 70., 90.]:
            c = np.cos(np.deg2rad(90-elevation))
            Lhaze = Ldark - .01*E0*c/np.pi
            rho_toa = np.pi*L/(E0*c)
            for method,tau in [('dos',1.),('cost',c)]:
                expected = np.pi*(L-Lhaze)/(E0*c*tau)
                for band in range(2):
                    p = ChavezParameters(method, float(np.pi*Ldark[band]/(E0[band]*c)), .01, elevation, 0., 2)
                    actual = optical_correction(rho_toa[:,band], method='chavez-'+method+'-1996', parameters=p)
                    np.testing.assert_allclose(actual,expected[:,band],rtol=2e-14,atol=2e-15)

    def test_known_reflectances_differ_but_ndvi_cancels(self):
        # At solar elevation 30: RED DOS=.10, NIR DOS=.30;
        # COST=.20,.60. Both NDVI=.50. Hand-computed values.
        results={}
        for method in ['dos','cost']:
            vals=[]
            for rho,dark in [(.15,.06),(.33,.04)]:
                p=ChavezParameters(method,dark,.01,30.,0.,2)
                vals.append(float(optical_correction(np.array([rho]),method='chavez-'+method+'-1996',parameters=p)[0]))
            results[method]=vals
        np.testing.assert_allclose(results['dos'],[.10,.30])
        np.testing.assert_allclose(results['cost'],[.20,.60])
        for red,nir in results.values():
            self.assertAlmostEqual((nir-red)/(nir+red),.5)

    def test_no_transmittance_correction_at_sun_zenith(self):
        a=np.array([.10,.20,.30])
        d=optical_correction(a,method='chavez-dos-1996',sun_elevation=90.,percentile=0.)
        c=optical_correction(a,method='chavez-cost-1996',sun_elevation=90.,percentile=0.)
        np.testing.assert_allclose(d,c)

    def test_cost_range_mask_can_differ_from_dos(self):
        a=np.array([.1,.8,np.nan,.3]);mask=np.array([False,False,False,True])
        outputs={}
        for method in ['dos','cost']:
            p=ChavezParameters(method,.1,.01,30.,0.,3)
            outputs[method]=optical_correction(a,method='chavez-'+method+'-1996',parameters=p,mask=mask)
        self.assertAlmostEqual(outputs['dos'][1],.71)
        self.assertTrue(np.isnan(outputs['cost'][1])) # 1.42 exceeds unit reflectance
        self.assertTrue(np.isnan(outputs['dos'][2:]).all())
        self.assertTrue(np.isnan(outputs['cost'][2:]).all())

    def test_scene_fit_percentile_and_tile_reuse(self):
        # Fixed dark percentile instead of estimating it again on each tile.
        a=np.array([.03,.04,.10,.20,.30])
        for method in ['chavez-dos-1996','chavez-cost-1996']:
            fit=optical_correction(a,method=method,sun_elevation=50.,percentile=25.,return_diagnostics=True)
            self.assertAlmostEqual(fit['parameters'].dark_reflectance,.04)
            tiled=np.concatenate([optical_correction(x,method=method,parameters=fit['parameters']) for x in [a[:2],a[2:]]])
            np.testing.assert_allclose(tiled,fit['reflectance'])

if __name__=='__main__':unittest.main()

