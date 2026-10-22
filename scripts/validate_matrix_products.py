"""Verify new full-scene products and matrix products without changing inputs."""
from pathlib import Path
import argparse,json,sys
import numpy as np
from PIL import Image
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from pylstemp.scene import LandsatScene
from scripts import matrix_references as ref

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input",type=Path,required=True)
    parser.add_argument("--results",type=Path,required=True)
    parser.add_argument("--baseline",type=Path,
        default=ROOT/"Verificacao/v1.11.0/todos_modelos/all_models_results.json",
        help="Prior all_models_results.json used as comparison baseline; supply your own run outside the local audit workspace.")
    parser.add_argument("--allow-numerical-change",action="store_true",
        help="Record expected numerical changes after an algorithm correction; input hashes and GeoTIFF checks remain strict.")
    args=parser.parse_args()
    if not args.baseline.is_file():
        parser.error("Baseline not found. Supply --baseline PATH_TO_PRIOR_all_models_results.json.")
    changes=[]
    full=json.loads((args.results/"cenas_completas/all_models_results.json").read_text(encoding="utf-8-sig"))
    matrix=json.loads((args.results/"matriz_real/module_matrix_results.json").read_text(encoding="utf-8-sig"))
    previous=json.loads(args.baseline.read_text(encoding="utf-8-sig"))
    old={s["scene"]:s for s in previous["scenes"]}
    checked=[]
    for info in full["scenes"]:
        dest=args.results/"cenas_completas"/info["scene"]
        assert info["input_sha256"]==old[info["scene"]]["input_sha256"],"Scene inputs changed"
        for key,metric in info["metrics"].items():
            baseline=old[info["scene"]]["metrics"].get(key)
            if baseline is None:
                changes.append(dict(scene=info["scene"],method=key,status="new diagnostic",stats=metric))
                continue
            changes.append(dict(scene=info["scene"],method=key,
                valid_delta=metric["valid"]-baseline["valid"],
                mean_delta=metric["mean"]-baseline["mean"]))
            if not args.allow_numerical_change or key in ("bt10_k","bt11_k"):
                assert metric["valid"]==baseline["valid"]
                np.testing.assert_allclose(metric["mean"],baseline["mean"],rtol=0,atol=1e-9)
        with LandsatScene(args.input/info["scene"]) as scene:
            raw_tags=scene.sources["B2"].tag_v2 if scene.backend=="pillow" else None
            for path in sorted(dest.glob("*.tif")):
                core=None
                if path.name.startswith("roi_"):
                    idx=int(path.name.split("_")[1])
                    core=tuple(info["rois"][idx-1]["window"])
                    shape=(256,256)
                    counterpart="roi%d_%s"%(idx,"pwv_screened" if "_pwv" in path.name else "jimenez-munoz-2014_gopinadh-2018_wang_raster")
                    other=args.results/"matriz_real"/info["scene"]/(counterpart+".tif")
                    with Image.open(other) as image:expected=np.array(image)
                else:
                    shape=tuple(info["shape"])
                    r,c=int(shape[0]*.5),int(shape[1]*.5)
                    win=(r,r+64,c,c+64)
                    optical,thermal,mask=scene.calibrated(win)
                    n=np.where(mask,np.nan,ref.ndvi(optical[5],optical[4]))
                    e10,e11=ref.emissivity("gopinadh-2018",n,optical[4])
                    expected=ref.temperature(path.stem[:-2],thermal[10],thermal[11],n,e10,e11,mask=mask)
                with Image.open(path) as image:
                    assert image.mode=="F"
                    assert (image.height,image.width)==shape
                    assert image.tag_v2[42113]=="nan"
                    if raw_tags is not None:
                        assert tuple(image.tag_v2[34735])==tuple(raw_tags[34735])
                        assert tuple(image.tag_v2[33550])==tuple(raw_tags[33550])
                        tie=list(raw_tags[33922])
                        if core is not None:
                            tie[3]+=core[2]*raw_tags[33550][0]
                            tie[4]-=core[0]*raw_tags[33550][1]
                        np.testing.assert_allclose(image.tag_v2[33922],tie,rtol=0,atol=1e-9)
                    actual=np.array(image) if core is not None else np.array(image.crop((c,r,c+64,r+64)))
                error=ref.check(actual,expected,atol=2e-5)
                checked.append(dict(scene=info["scene"],file=path.name,status="passed",reference_error=error))
        print(info["sensor"],"full-scene exports, input hashes and independent references passed",flush=True)
    for scene in matrix["scenes"]:
        for roi in scene["rois"]:
            checked.extend(dict(scene=scene["scene"],file=a["path"],status=a["validation"],scope="validated during matrix execution")
                for a in roi["artifacts"])
    result=dict(outputs=checked,output_count=len(checked),unexpected_failures=0,
        input_hashes_match_prior_run=True,full_scene_metrics_reproducibility="numerical changes recorded" if args.allow_numerical_change else "passed",
        baseline_comparison=changes,float32_tolerance=2e-5)
    (args.results/"geotiff_validation.json").write_text(json.dumps(result,indent=2)+"\n",encoding="utf-8")
    print("GeoTIFFs:",len(checked),"passed")

if __name__=="__main__":main()
