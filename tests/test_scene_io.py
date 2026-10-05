"""GeoTIFF reader/export checks using a small synthetic aligned scene."""
from pathlib import Path
import tempfile
import unittest
import numpy as np
try:
    from PIL import Image, TiffImagePlugin
except ImportError:
    Image = None
from pylstemp.scene import LandsatScene


@unittest.skipIf(Image is None, "Install .[examples] to test GeoTIFF IO")
class SceneIOTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.folder=Path(self.tmp.name)
        metadata=dict(SPACECRAFT_ID='"LANDSAT_8"',PROCESSING_LEVEL='"L1TP"',
                      LANDSAT_PRODUCT_ID='"TEST"',SUN_ELEVATION=30)
        for band in (2,4,5):
            metadata[f"REFLECTANCE_MULT_BAND_{band}"]=2e-5
            metadata[f"REFLECTANCE_ADD_BAND_{band}"]=-0.1
            metadata[f"RADIANCE_MULT_BAND_{band}"]=.005
            metadata[f"RADIANCE_ADD_BAND_{band}"]=-25.
        for band in (10,11):
            metadata[f"RADIANCE_MULT_BAND_{band}"]=0.0003342
            metadata[f"RADIANCE_ADD_BAND_{band}"]=0.1
            metadata[f"K1_CONSTANT_BAND_{band}"]=774.8853 if band==10 else 480.8883
            metadata[f"K2_CONSTANT_BAND_{band}"]=1321.0789 if band==10 else 1201.1442
        (self.folder/"TEST_MTL.txt").write_text("\n".join(f"{k} = {v}" for k,v in metadata.items()))
        for token in ("B2","B4","B5","B10","B11","QA_PIXEL","QA_RADSAT","SZA"):
            value=6000 if token=="SZA" else 0 if token.startswith("QA") else 20000
            data=np.full((12,14),value,dtype=np.uint16)
            if token=="QA_PIXEL": data[2,3]=8
            self.write(token,data)

    def tearDown(self):
        self.tmp.cleanup()

    def write(self,token,data,x_origin=100):
        tags=TiffImagePlugin.ImageFileDirectory_v2()
        tags[33550]=(30.,30.,0.)
        tags[33922]=(0.,0.,0.,x_origin,1000.,0.)
        tags[34735]=(1,1,0,2,1024,0,1,1,3072,0,1,32623)
        tags.tagtype[33550]=12
        tags.tagtype[33922]=12
        tags.tagtype[34735]=3
        Image.fromarray(data).save(self.folder/f"TEST_{token}.TIF",tiffinfo=tags)

    def test_mtl_angles_and_qa_are_used(self):
        with LandsatScene(self.folder,backend="pillow") as scene:
            optical,thermal,mask=scene.calibrated(optical_quantity="reflectance")
            self.assertEqual(scene.shape,(12,14))
            self.assertTrue(mask[2,3])
            self.assertTrue(np.isnan(optical[4][2,3]))
            self.assertTrue(np.isnan(thermal[10][2,3]))
            self.assertAlmostEqual(float(optical[4][0,0]),0.6,places=10)

    def test_full_and_cropped_geotiff_roundtrip(self):
        with LandsatScene(self.folder,backend="pillow") as scene:
            data=np.arange(20,dtype=np.float32).reshape(4,5);data[0,0]=np.nan
            path=self.folder/"result.tif"
            scene.write_geotiff(path,data,window=(3,7,4,9),units="kelvin")
            with Image.open(path) as exported:
                np.testing.assert_allclose(np.array(exported),data,equal_nan=True)
                self.assertEqual(exported.tag_v2[33922][3:5],(220.,910.))
                self.assertEqual(exported.tag_v2[34735],scene.sources["B2"].tag_v2[34735])
                self.assertEqual(exported.tag_v2[42113],"nan")

    def test_reject_unaligned_band(self):
        self.write("B5",np.ones((12,14),dtype=np.uint16),x_origin=130)
        with self.assertRaisesRegex(ValueError,"Unaligned"):
            LandsatScene(self.folder,backend="pillow")

    def test_reject_missing_band(self):
        (self.folder/"TEST_B11.TIF").unlink()
        with self.assertRaisesRegex(ValueError,"Missing"):
            LandsatScene(self.folder,backend="pillow")

    def test_reject_out_of_scene_window(self):
        with LandsatScene(self.folder,backend="pillow") as scene:
            with self.assertRaises(ValueError):
                scene.read("B4",(-1,5,0,5))

    def test_radiance_default_and_explicit_reflectance(self):
        with LandsatScene(self.folder,backend="pillow") as scene:
            optical,thermal,mask=scene.calibrated()
            reflected,other,other_mask=scene.calibrated(optical_quantity="reflectance")
            self.assertEqual(float(optical[4][0,0]),75.)
            self.assertAlmostEqual(float(reflected[4][0,0]),.6)
            np.testing.assert_array_equal(thermal[10],other[10])
            np.testing.assert_array_equal(mask,other_mask)
            with self.assertRaisesRegex(ValueError,"optical_quantity"):
                scene.calibrated(optical_quantity="dn")

    def test_scene_without_blue_runs_and_exports(self):
        (self.folder/"TEST_B2.TIF").unlink()
        with LandsatScene(self.folder,backend="pillow") as scene:
            optical,thermal,mask=scene.calibrated()
            self.assertEqual(set(optical),{4,5})
            scene.write_geotiff(self.folder/"no_blue.tif",thermal[10],units="K")
