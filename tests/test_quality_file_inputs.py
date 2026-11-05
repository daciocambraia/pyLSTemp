"""QA file requirements, grid validation and actual downstream screening."""
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
import numpy as np
try:
    import rasterio
    from rasterio.transform import from_origin
except ImportError:
    rasterio = None
from pylstemp import read_quality_mask, emissivity, optical_correction

@unittest.skipIf(rasterio is None, 'rasterio optional dependency')
class ExplicitQAInputs(unittest.TestCase):
    def write(self, folder, name, data, *, shifted=False, nodata=None):
        path=Path(folder)/name
        with rasterio.open(path,'w',driver='GTiff',height=data.shape[0],width=data.shape[1],count=1,dtype=data.dtype,crs='LOCAL_CS["QA test",LOCAL_DATUM["QA test",0],UNIT["metre",1]]',transform=from_origin(10 if shifted else 0,100,30,30),nodata=nodata) as f:
            f.write(data,1)
        return path

    def fixture(self, temp):
        q=np.array([[8,0,128],[0,0,0]],dtype='uint16')
        s=np.array([[0,0,0],[1<<3,1<<11,0]],dtype='uint16')
        ref=self.write(temp,'red.tif',np.full((2,3),.2,dtype='float32'))
        qp=self.write(temp,'QA_PIXEL.tif',q)
        qs=self.write(temp,'QA_RADSAT.tif',s)
        return ref,qp,qs

    def test_bits_and_actual_emissivity_mask(self):
        with TemporaryDirectory() as temp:
            ref,qp,qs=self.fixture(temp)
            mask=read_quality_mask(qp,qs,reference_path=ref)
            np.testing.assert_array_equal(mask,[[True,False,False],[True,True,False]])
            water=read_quality_mask(qp,qs,reference_path=ref,exclude_water=True)
            self.assertTrue(water[0,2]);self.assertFalse(mask[0,2])
            result=emissivity(np.full((2,3),.3),method='rongali-2018',mask=mask)
            np.testing.assert_array_equal(np.isnan(result),mask)

    def test_missing_and_required_paths(self):
        with TemporaryDirectory() as temp:
            ref,qp,qs=self.fixture(temp)
            for name in ('QA_PIXEL','QA_RADSAT'):
                with self.subTest(name=name):
                    args=(None,qs) if name=='QA_PIXEL' else (qp,None)
                    with self.assertRaisesRegex(ValueError,name):read_quality_mask(*args,reference_path=ref)
            with self.assertRaises(TypeError):read_quality_mask(qp,reference_path=ref)
            with self.assertRaises(TypeError):read_quality_mask(qp,qs)

    def test_shifted_grid_float_qa_and_nodata(self):
        with TemporaryDirectory() as temp:
            ref,qp,qs=self.fixture(temp)
            bad=self.write(temp,'shifted.tif',np.zeros((2,3),dtype='uint16'),shifted=True)
            with self.assertRaisesRegex(ValueError,'Unaligned QA_RADSAT'):read_quality_mask(qp,bad,reference_path=ref)
            bad=self.write(temp,'float.tif',np.zeros((2,3),dtype='float32'))
            with self.assertRaisesRegex(ValueError,'integer QA'):read_quality_mask(qp,bad,reference_path=ref)
            a=np.zeros((2,3),dtype='uint16');a[1,2]=65535
            nodata=self.write(temp,'nodata.tif',a,nodata=65535)
            self.assertTrue(read_quality_mask(qp,nodata,reference_path=ref)[1,2])

    def test_dos_fit_excludes_qa_rejected_dark_pixel(self):
        with TemporaryDirectory() as temp:
            ref,qp,qs=self.fixture(temp)
            mask=read_quality_mask(qp,qs,reference_path=ref)
            rho=np.array([[.05,.2,.3],[.06,.07,.4]])
            result=optical_correction(rho,method='chavez-dos',sun_elevation=45,percentile=0,mask=mask,return_diagnostics=True)
            unmasked=optical_correction(rho,method='chavez-dos',sun_elevation=45,percentile=0,return_diagnostics=True)
            self.assertTrue(np.isnan(result['reflectance'][0,0]))
            # A cloudy artificial dark pixel must not influence the fit for clear pixels.
            self.assertNotEqual(float(result['reflectance'][0,1]),float(unmasked['reflectance'][0,1]))

if __name__=='__main__':unittest.main()

