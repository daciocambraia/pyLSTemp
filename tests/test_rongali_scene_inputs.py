"""Canonical Rongali naming and mandatory scene QA inputs."""
import importlib.util
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch
import unittest
import numpy as np
from pylstemp import emissivity, list_algorithms
from pylstemp.exceptions import InvalidMethodRequested
from pylstemp.provenance import optical_contract

class RongaliNaming(unittest.TestCase):
    def test_catalog_and_optical_contract(self):
        from pylstemp.algorithms.emissivity.rongali_2018 import ComputeEmissivityRongali2018
        from pylstemp.algorithms.emissivity import emissivity_registry
        self.assertIsInstance(emissivity_registry.create('rongali-2018'),ComputeEmissivityRongali2018)
        self.assertEqual(set(list_algorithms()['emissivity']),{'avdan-2016','rongali-2018'})
        c=optical_contract('rongali-2018','radiance')
        self.assertEqual(c['status'],'declared_quantity_matches_source_interpretation')
        self.assertIsNotNone(c['source_condition'])

    def test_previous_selector_and_module_are_not_available(self):
        with self.assertRaises(InvalidMethodRequested):emissivity(np.array([.3]),method='gopinadh-2018')
        self.assertIsNone(importlib.util.find_spec('pylstemp.algorithms.emissivity.gopinadh_2018'))

@unittest.skipUnless(importlib.util.find_spec('rasterio'),'rasterio is optional')
class SceneQAInputs(unittest.TestCase):
    def make_scene(self,folder,missing=None,bad_grid=False):
        import rasterio
        from rasterio.transform import from_origin
        for token in ['B4','B5','B10','B11','QA_PIXEL','QA_RADSAT']:
            if token==missing:continue
            shape=(3,2) if token=='QA_RADSAT' and bad_grid else (2,2)
            with rasterio.open(Path(folder)/('TEST_'+token+'.TIF'),'w',driver='GTiff',height=shape[0],width=shape[1],count=1,dtype='uint16',crs='LOCAL_CS["QA fixture",LOCAL_DATUM["QA fixture",0],UNIT["metre",1]]',transform=from_origin(500000,1000000,30,30)) as f:f.write(np.zeros(shape,dtype='uint16'),1)
        (Path(folder)/'TEST_MTL.txt').write_text('test fixture',encoding='utf8')

    def test_each_qa_file_is_mandatory(self):
        from pylstemp.scene import LandsatScene
        metadata=dict(SPACECRAFT_ID='LANDSAT_8',LANDSAT_PRODUCT_ID='TEST',PROCESSING_LEVEL='L1TP')
        for token in ['QA_PIXEL','QA_RADSAT']:
            with self.subTest(missing=token),TemporaryDirectory() as temp:
                self.make_scene(temp,missing=token)
                with patch('pylstemp.scene.read_mtl',return_value=metadata):
                    with self.assertRaisesRegex(ValueError,token):LandsatScene(temp,backend='rasterio')

    def test_qa_grid_must_match(self):
        from pylstemp.scene import LandsatScene
        metadata=dict(SPACECRAFT_ID='LANDSAT_8',LANDSAT_PRODUCT_ID='TEST',PROCESSING_LEVEL='L1TP')
        with TemporaryDirectory() as temp:
            self.make_scene(temp,bad_grid=True)
            with patch('pylstemp.scene.read_mtl',return_value=metadata):
                with self.assertRaisesRegex(ValueError,'Unaligned band: QA_RADSAT'):LandsatScene(temp,backend='rasterio')

if __name__=='__main__':unittest.main()
