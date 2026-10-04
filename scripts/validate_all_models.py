"""Exercise every available model on supplied Level-1 scenes.

Xiaolei remains synthetic-only without surface reflectance.
Legacy AVHRR adaptations and Landsat-9 transfers are operational comparisons.
"""
from pathlib import Path
import argparse
import json
import sys
import time
import warnings
import numpy as np

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
sys.path.insert(0,str(ROOT/"scripts"))
from pylstemp import brightness, emissivity, single_window, split_window, spectral_index, water_vapor, list_algorithms
from pylstemp.algorithms import FAMILY_REGISTRIES
from pylstemp.calibration import quality_mask
from pylstemp.scene import LandsatScene
from validate_scenes import Stats, digest

SPLIT=("du-2015","kerr-1992","price-1984","sobrino-1993")


def valid_output(array,mask,*,kind):
    assert array.shape==mask.shape
    assert not np.isinf(array).any()
    assert np.isnan(array[mask]).all()
    finite=array[np.isfinite(array)]
    if kind=="temperature":
        assert np.all(finite>0)
    elif kind=="emissivity":
        assert np.all((finite>0)&(finite<=1))
    elif kind=="index":
        assert np.all(np.abs(finite)<=1)


def plot(path,results,label):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    fig,axes=plt.subplots(2,3,figsize=(13,8),layout="constrained")
    finite=np.concatenate([a[np.isfinite(a)] for a in results.values()])
    low,high=np.percentile(finite,[2,98]) if finite.size else (0,1)
    for ax,(name,array) in zip(axes.flat,results.items()):
        handle=ax.imshow(array,cmap="inferno",vmin=low,vmax=high)
        ax.set_title(name);ax.set_xticks([]);ax.set_yticks([])
        fig.colorbar(handle,ax=ax,label="C",shrink=.8)
    fig.suptitle(label+" | shared colour limits; operational comparison")
    fig.savefig(path,dpi=140);plt.close(fig)


def run_scene(folder,out,tile_rows):
    start=time.perf_counter()
    with LandsatScene(folder) as scene:
        dest=out/scene.product_id
        dest.mkdir(parents=True,exist_ok=False)
        names=["bt10_k","bt11_k","ndvi","evi","legacy_ndvi",
               "avdan_e10","avdan_e11","gopinadh_e10","gopinadh_e11",
               "mono_avdan_k","mono_gopinadh_k"]+[key+"_k" for key in SPLIT]
        metrics={name:Stats() for name in names}
        products={name:np.lib.format.open_memmap(dest/(name+".npy"),mode="w+",
            dtype=np.float32,shape=scene.shape) for name in ("kerr-1992_k","price-1984_k","sobrino-1993_k")}
        height,width=scene.shape
        global_min,global_max=np.inf,-np.inf
        with warnings.catch_warnings(record=True) as recorded:
            warnings.simplefilter("once",RuntimeWarning)
            for row in range(0,height,tile_rows):
                r1=min(height,row+tile_rows);window=(row,r1,0,width)
                optical,thermal,mask=scene.calibrated(window)
                values={"bt10_k":thermal[10],"bt11_k":thermal[11]}
                for band in (10,11):
                    api=brightness(scene.read(f"B{band}",window),band=f"band_{band}",sensor=scene.sensor,
                        rad_gain=scene.metadata[f"RADIANCE_MULT_BAND_{band}"],
                        rad_bias=scene.metadata[f"RADIANCE_ADD_BAND_{band}"],mask=mask)
                    np.testing.assert_allclose(api,thermal[band],rtol=0,atol=1e-10,equal_nan=True)
                ndvi=spectral_index("ndvi",nir=optical[5],red=optical[4],mask=mask)
                values["ndvi"]=ndvi
                values["evi"]=spectral_index("evi",nir=optical[5],red=optical[4],blue=optical[2],mask=mask)
                values["legacy_ndvi"]=FAMILY_REGISTRIES["spectral_indices"].create("ndvi")(
                    band_5_nir=optical[5],band_4_red=optical[4],mask=mask)
                np.testing.assert_allclose(values["legacy_ndvi"],ndvi,rtol=0,atol=1e-14,equal_nan=True)
                for method,prefix in (("avdan-2016","avdan"),("gopinadh-2018","gopinadh")):
                    for band in (10,11):
                        values[f"{prefix}_e{band}"]=emissivity(ndvi,band=f"band_{band}",emissivity_method=method)
                    values[f"mono_{prefix}_k"]=single_window(thermal[10],optical[4],optical[5],
                        emissivity_method=method,mask=mask)
                for method in SPLIT:
                    values[method+"_k"]=split_window(thermal[10],thermal[11],optical[4],optical[5],
                        lst_method=method,emissivity_method="gopinadh-2018",mask=mask)
                for name,array in values.items():
                    kind="index" if name in ("ndvi","evi","legacy_ndvi") else "emissivity" if "_e1" in name else "temperature"
                    valid_output(array,mask,kind=kind)
                    metrics[name].add(array)
                    if name in products: products[name][row:r1]=array
                land=quality_mask(scene.read("QA_PIXEL",window),scene.read("QA_RADSAT",window),exclude_water=True)
                ok=~land&np.isfinite(ndvi)&np.isfinite(thermal[10])&np.isfinite(thermal[11])
                if ok.any():
                    global_min=min(global_min,float(ndvi[ok].min()))
                    global_max=max(global_max,float(ndvi[ok].max()))
                if row//tile_rows%8==0:print(scene.sensor,"all models full-scene",r1,"/",height,flush=True)
            warnings_log=[str(w.message) for w in recorded]
        full_seconds=time.perf_counter()-start
        for name,array in list(products.items()):
            array.flush();scene.write_geotiff(dest/(name+".tif"),array,units="kelvin")
            array._mmap.close();del products[name]
            staging=(dest/(name+".npy")).resolve()
            if staging.parent!=dest.resolve():raise RuntimeError("Unsafe staging path")
            staging.unlink()

        rois=[]
        for index,(fr,fc) in enumerate(((.35,.35),(.5,.5),(.65,.65)),1):
            r0,c0=int(height*fr),int(width*fc)
            core=(r0,r0+256,c0,c0+256);halo=(r0-10,r0+266,c0-10,c0+266)
            optical,thermal,mask=scene.calibrated(halo,exclude_water=True)
            ndvi=spectral_index("ndvi",nir=optical[5],red=optical[4],mask=mask)
            pwv=water_vapor(thermal[10],thermal[11],ndvi,mask=mask,ndvi_range=(global_min,global_max))
            extrap=np.isfinite(pwv)&((pwv<.066)|(pwv>7.833))
            pwv=np.where(extrap,np.nan,pwv)
            select=np.s_[10:-10,10:-10]
            roi_metrics={};arrays={}
            for method in ("mono-window-2016",)+SPLIT+("jimenez-munoz-2014",):
                with warnings.catch_warnings():
                    warnings.simplefilter("ignore",RuntimeWarning)
                    if method=="mono-window-2016":
                        result=single_window(thermal[10],optical[4],optical[5],mask=mask)
                    else:
                        result=split_window(thermal[10],thermal[11],optical[4],optical[5],
                            lst_method=method,water_vapor=pwv if method=="jimenez-munoz-2014" else None,mask=mask)
                valid_output(result,mask,kind="temperature")
                a=result[select]
                stat=Stats();stat.add(a);roi_metrics[method]=stat.result()
                arrays[method]=a-273.15
            valid_output(pwv,mask,kind="pwv")
            stat=Stats();stat.add(pwv[select]);roi_metrics["wang-2015"]=stat.result()
            scene.write_geotiff(dest/f"roi_{index}_jimenez_k.tif",arrays["jimenez-munoz-2014"]+273.15,window=core,units="kelvin")
            scene.write_geotiff(dest/f"roi_{index}_pwv.tif",pwv[select],window=core,units="g/cm2")
            plot(dest/f"roi_{index}_all_lst.png",arrays,f"{scene.sensor}; ROI {index}")
            # The optional Du CWV branch is tested with ROI mean in-domain Wang PWV.
            finite=pwv[select][np.isfinite(pwv[select])]
            cwv=float(finite.mean()) if finite.size else None
            if cwv is not None and 0<=cwv<=6.3:
                with_pwv=split_window(thermal[10],thermal[11],optical[4],optical[5],
                    lst_method="du-2015",water_vapor=cwv,mask=mask)
                valid_output(with_pwv,mask,kind="temperature")
                stat=Stats();stat.add(with_pwv[select]);roi_metrics["du-2015_roi_mean_cwv"]=stat.result()
            rois.append(dict(window=core,halo_pixels=10,metrics=roi_metrics,roi_mean_cwv=cwv,
                pwv_extrapolation_pixels=int(extrap[select].sum())))
        result=dict(scene=scene.product_id,sensor=scene.sensor,shape=scene.shape,
            backend=scene.backend,full_scene_seconds=full_seconds,total_seconds=time.perf_counter()-start,
            metrics={key:stat.result() for key,stat in metrics.items()},rois=rois,warnings=warnings_log,
            ndvi_land_range=[global_min,global_max],
            xiaolei="synthetic tests only: physical surface reflectance unavailable",
            legacy_models="Price/Kerr/Sobrino are unvalidated AVHRR-to-Landsat adaptations",
            landsat9="experimental coefficient transfer; radiometric calibration uses sensor MTL",
            scientific_accuracy="no independent ground truth; no RMSE claim",
            input_sha256={token:digest(path) for token,path in dict(scene.paths,MTL=scene.mtl_path).items()})
        (dest/"results.json").write_text(json.dumps(result,indent=2,allow_nan=False),encoding="utf-8")
        print(scene.sensor,"all model scene checks passed",flush=True)
        return result


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input",type=Path,required=True)
    parser.add_argument("--output",type=Path,required=True)
    parser.add_argument("--tile-rows",type=int,default=128)
    args=parser.parse_args()
    if args.tile_rows<1:parser.error("tile rows must be positive")
    args.output.mkdir(parents=True,exist_ok=False)
    folders=[args.input] if list(args.input.glob("*_MTL.txt")) else sorted(p for p in args.input.iterdir() if p.is_dir() and list(p.glob("*_MTL.txt")))
    if not folders:parser.error("No scenes found")
    results=[run_scene(p,args.output,args.tile_rows) for p in folders]
    inventory={family:list(methods) for family,methods in list_algorithms().items() if family!="credit"}
    (args.output/"all_models_results.json").write_text(json.dumps(dict(inventory=inventory,scenes=results),indent=2,allow_nan=False),encoding="utf-8")


if __name__=="__main__":
    main()
