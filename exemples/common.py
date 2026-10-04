"""Shared calibrated ROI for the example notebooks."""
import os
from pathlib import Path
import sys
import numpy as np

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))
from pylstemp.scene import LandsatScene
from pylstemp import spectral_index


def example_inputs():
    configured = os.environ.get("PYLSTEMP_SCENE")
    if configured:
        folder = Path(configured).expanduser().resolve()
    else:
        folders = []
        for data_root in (PROJECT_ROOT/"Imagens", PROJECT_ROOT.parent/"Imagens"):
            folders = sorted(p for p in data_root.glob("*") if p.is_dir() and list(p.glob("*_MTL.txt")))
            if folders:
                break
        if not folders:
            raise FileNotFoundError("Set PYLSTEMP_SCENE to a Landsat 8/9 Level-1 scene folder with MTL, bands and QA.")
        folder = folders[0]
    with LandsatScene(folder) as scene:
        r0,c0=scene.shape[0]//2,scene.shape[1]//2
        win=(r0,min(r0+256,scene.shape[0]),c0,min(c0+256,scene.shape[1]))
        optical,thermal,mask=scene.calibrated(win,exclude_water=True)
        return dict(blue=optical[2],red=optical[4],nir=optical[5],
            bt10=thermal[10],bt11=thermal[11],mask=mask,sensor=scene.sensor,
            product=scene.product_id,window=win,
            ndvi=spectral_index("ndvi",nir=optical[5],red=optical[4],mask=mask))
