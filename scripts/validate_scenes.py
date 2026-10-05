"""Reproducible scene validation: full-scene TOA/BT/LST and Wang ROIs.

Usage:
  python scripts/validate_scenes.py --input ../Imagens --output Verificacao/v1.11.0
  python scripts/validate_scenes.py --input <one scene> --output <new folder>
The Level-1 runs are operational checks; no ground-truth RMSE is claimed.
"""
from pathlib import Path
import argparse
import hashlib
import json
import platform
import sys
import time
import warnings

import numpy as np
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from pylstemp import __version__, spectral_index, single_window, split_window, water_vapor
from pylstemp.calibration import quality_mask
from pylstemp.scene import LandsatScene


class Stats:
    def __init__(self):
        self.total = self.count = 0
        self.sum = self.sum2 = 0.0
        self.minimum, self.maximum = np.inf, -np.inf
        self.samples = []

    def add(self, array):
        a=np.asarray(array,dtype=float)
        self.total += a.size
        finite=a[np.isfinite(a)]
        self.count += finite.size
        if finite.size:
            self.sum += float(finite.sum())
            self.sum2 += float(np.square(finite).sum())
            self.minimum=min(self.minimum,float(finite.min()))
            self.maximum=max(self.maximum,float(finite.max()))
            self.samples.append(finite[::max(1,finite.size//2000)].copy())

    def result(self):
        result=dict(total=self.total,valid=self.count,
                    valid_percent=100*self.count/self.total if self.total else 0)
        if self.count:
            sample=np.concatenate(self.samples)
            result.update(minimum=self.minimum,maximum=self.maximum,mean=self.sum/self.count,
                std=float(np.sqrt(max(0,self.sum2/self.count-(self.sum/self.count)**2))),
                approximate_percentiles=dict(zip(["p02","p50","p98"],map(float,np.percentile(sample,[2,50,98])))),
                percentile_sample_count=int(sample.size))
        return result


def digest(path):
    h=hashlib.sha256()
    with Path(path).open("rb") as stream:
        for chunk in iter(lambda:stream.read(4*1024*1024),b""):
            h.update(chunk)
    return h.hexdigest()


def checks(optical, thermal, mask, ndvi, evi, mono, du):
    for band in (2,4,5):
        assert not np.isinf(optical[band]).any()
        assert np.isnan(optical[band][mask]).all()
    for band in (10,11):
        assert not np.isinf(thermal[band]).any()
        assert np.isnan(thermal[band][mask]).all()
        assert np.all(thermal[band][np.isfinite(thermal[band])] > 0)
    for array in (ndvi,evi,mono,du):
        assert not np.isinf(array).any()
        assert np.isnan(array[mask]).all()
    assert np.all(np.abs(ndvi[np.isfinite(ndvi)]) <= 1)
    assert np.all(mono[np.isfinite(mono)] > 0)
    assert np.all(du[np.isfinite(du)] > 0)


def preview(path, arrays, extent_label):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    fig, axes=plt.subplots(2,3,figsize=(13,8),layout="constrained")
    for ax,(name,array) in zip(axes.flat,arrays.items()):
        a=np.asarray(array,dtype=float)
        finite=a[np.isfinite(a)]
        limits=np.percentile(finite,[2,98]) if finite.size else (0,1)
        handle=ax.imshow(a,cmap="viridis" if "NDVI" in name or "TOA" in name else "inferno",
                         vmin=limits[0],vmax=limits[1])
        ax.set_title(name); ax.set_xticks([]);ax.set_yticks([])
        fig.colorbar(handle,ax=ax,shrink=0.8)
    for ax in list(axes.flat)[len(arrays):]:
        ax.axis("off")
    fig.suptitle(extent_label+" | QA applied; Level-1 operational check")
    fig.savefig(path,dpi=140)
    plt.close(fig)



def validate(folder, output, tile_rows):
    started=time.perf_counter()
    with LandsatScene(folder) as scene:
        destination=output/scene.product_id
        destination.mkdir(parents=True,exist_ok=False)
        height,width=scene.shape
        metrics={name:Stats() for name in ("toa_b2","toa_b4","toa_b5","bt10_k","bt11_k",
                                         "ndvi_toa","evi_toa","mono_k","du_k","mono_minus_du_k")}
        products={}
        for name in ("toa_b2","toa_b4","toa_b5","mono_k","du_k"):
            products[name]=np.lib.format.open_memmap(destination/(name+".npy"),mode="w+",
                                                   dtype=np.float32,shape=scene.shape)
        global_min,global_max=np.inf,-np.inf
        tiles=0
        for row in range(0,height,tile_rows):
            end=min(height,row+tile_rows)
            win=(row,end,0,width)
            optical,thermal,mask=scene.calibrated(win)
            ndvi=spectral_index("ndvi",nir=optical[5],red=optical[4],mask=mask)
            evi=spectral_index("evi",nir=optical[5],red=optical[4],blue=optical[2],mask=mask)
            mono=single_window(thermal[10],optical[4],optical[5],mask=mask)
            du=split_window(thermal[10],thermal[11],optical[4],optical[5],
                            lst_method="du-2015",mask=mask)
            checks(optical,thermal,mask,ndvi,evi,mono,du)
            values=dict(toa_b2=optical[2],toa_b4=optical[4],toa_b5=optical[5],
                        bt10_k=thermal[10],bt11_k=thermal[11],ndvi_toa=ndvi,
                        evi_toa=evi,mono_k=mono,du_k=du,mono_minus_du_k=mono-du)
            for name,array in values.items():
                metrics[name].add(array)
                if name in products:
                    products[name][row:end]=array
            land=quality_mask(scene.read("QA_PIXEL",win),scene.read("QA_RADSAT",win),exclude_water=True)
            valid=~land & np.isfinite(ndvi) & np.isfinite(thermal[10]) & np.isfinite(thermal[11])
            if valid.any():
                global_min=min(global_min,float(ndvi[valid].min()))
                global_max=max(global_max,float(ndvi[valid].max()))
            tiles+=1
            if tiles % 8 == 0:
                print(f"{scene.product_id}: full-scene rows {end}/{height}",flush=True)
        full_seconds=time.perf_counter()-started
        for name,array in products.items():
            array.flush()
            scene.write_geotiff(destination/(name+".tif"),array,units="kelvin" if name.endswith("_k") else "TOA reflectance")
        # Keep only the georeferenced final products, remove individual staging files.
        for name in list(products):
            products[name]._mmap.close()
            del products[name]
            staging=(destination/(name+".npy")).resolve()
            if staging.parent != destination.resolve():
                raise RuntimeError("Unsafe staging path")
            staging.unlink()
        roi_results=[]
        roi_size=min(256,height,width)
        radius=10
        for index,(fraction_r,fraction_c) in enumerate(((0.35,0.35),(0.5,0.5),(0.65,0.65)),1):
            r0=min(height-roi_size-radius,max(radius,int(height*fraction_r)))
            c0=min(width-roi_size-radius,max(radius,int(width*fraction_c)))
            core=(r0,r0+roi_size,c0,c0+roi_size)
            halo=(r0-radius,r0+roi_size+radius,c0-radius,c0+roi_size+radius)
            optical,thermal,mask=scene.calibrated(halo,exclude_water=True)
            ndvi=spectral_index("ndvi",nir=optical[5],red=optical[4],mask=mask)
            evi=spectral_index("evi",nir=optical[5],red=optical[4],blue=optical[2],mask=mask)
            t0=time.perf_counter()
            pwv=water_vapor(thermal[10],thermal[11],ndvi,mask=mask,
                           ndvi_range=(global_min,global_max))
            pwv_seconds=time.perf_counter()-t0
            jimenez=split_window(thermal[10],thermal[11],optical[4],optical[5],
                lst_method="jimenez-munoz-2014",water_vapor=pwv,mask=mask)
            mono=single_window(thermal[10],optical[4],optical[5],mask=mask)
            du=split_window(thermal[10],thermal[11],optical[4],optical[5],lst_method="du-2015",mask=mask)
            selection=np.s_[radius:-radius,radius:-radius]
            pwv_core=pwv[selection]
            assert not np.isinf(pwv_core).any()
            assert np.isnan(pwv[mask]).all()
            assert np.all(pwv_core[np.isfinite(pwv_core)] >= 0)
            # Wang's TIGR3 reference data span 0.066..7.833 g/cm2 (paper p.6).
            # This is a range screen, not independent scientific validation.
            extrapolation = np.isfinite(pwv_core) & ((pwv_core < 0.066) | (pwv_core > 7.833))
            screened = np.where(extrapolation, np.nan, pwv_core)
            scene.write_geotiff(destination/f"roi_{index}_pwv_range_screened.tif",screened,window=core,units="g/cm2")
            scene.write_geotiff(destination/f"roi_{index}_pwv_extrapolation.tif",
                np.where(np.isfinite(pwv_core),extrapolation.astype(float),np.nan),window=core,units="0=in reference range; 1=extrapolation")
            scene.write_geotiff(destination/f"roi_{index}_jimenez_range_screened_k.tif",
                np.where(extrapolation,np.nan,jimenez[selection]),window=core,units="kelvin")
            stat=Stats();stat.add(pwv_core)
            scene.write_geotiff(destination/f"roi_{index}_pwv.tif",pwv_core,window=core,units="g/cm2")
            scene.write_geotiff(destination/f"roi_{index}_jimenez_k.tif",jimenez[selection],window=core,units="kelvin")
            plot=dict(TOA_red=optical[4][selection],NDVI_TOA=ndvi[selection],BT10_C=thermal[10][selection]-273.15,
                      mono_C=mono[selection]-273.15,du_C=du[selection]-273.15,PWV_g_cm2=pwv_core)
            preview(destination/f"roi_{index}.png",plot,f"{scene.sensor}; ROI {index}; row={r0}, col={c0}")
            roi_results.append(dict(window=core,halo=radius,pwv_seconds=pwv_seconds,pwv=stat.result(),pwv_extrapolation_pixels=int(extrapolation.sum()),pwv_reference_range=[0.066,7.833]))
            print(f"{scene.product_id}: Wang ROI {index} done, {pwv_seconds:.2f}s",flush=True)

        result=dict(product_id=scene.product_id,sensor=scene.sensor,shape=scene.shape,
            backend=scene.backend,grid_repr=repr(scene.grid),version=__version__,
            full_scene_seconds=full_seconds,total_seconds=time.perf_counter()-started,
            tile_rows=tile_rows,ndvi_land_range=[global_min,global_max],
            optical_product="TOA",solar_angle="per-pixel SZA / 100" if "SZA" in scene.sources else "MTL scene-centre",
            full_scene_methods=["mono-window-2016","du-2015"],
            wang_scope="three 256x256 ROIs with 10-pixel halo and full-scene NDVI bounds",
            temperature_validation="operational consistency only; no ground-truth RMSE",
            landsat9_coefficients="experimental transfer of Landsat-8 retrieval coefficients" if scene.sensor=="landsat_9" else "original target sensor",
            metrics={name:stat.result() for name,stat in metrics.items()},rois=roi_results,
            input_sha256={token:digest(path) for token,path in dict(scene.paths,MTL=scene.mtl_path).items()},
            calibration_metadata={k:v for k,v in scene.metadata.items() if any(x in k for x in
                ("REFLECTANCE_MULT","REFLECTANCE_ADD","RADIANCE_MULT","RADIANCE_ADD","K1_CONSTANT","K2_CONSTANT","SUN_ELEVATION","DATE_ACQUIRED"))},
            environment=dict(python=platform.python_version(),numpy=np.__version__,platform=platform.platform()))
        (destination/"results.json").write_text(json.dumps(result,indent=2,allow_nan=False),encoding="utf-8")
        lines=[f"# Scene validation: {scene.product_id}","",
            f"pyLSTemp {__version__}; {scene.shape[0]} x {scene.shape[1]} pixels; backend {scene.backend}.",
            "","## Scientific scope","",
            "Optical inputs: TOA reflectance, corrected with per-pixel SZA where available.",
            "QA: fill/cloud/cirrus/shadow/snow, B2/B4/B5 saturation and terrain occlusion.",
            "Water is excluded for Wang. Full-scene runs: mono-window and Du. Wang/Jimenez: three ROIs.",
            "No surface reflectance or ground-truth temperature is present. These are operational checks.",
            "Landsat 9 retrieval coefficients are an experimental transfer, not an accuracy validation.",
            "","## Full-scene statistics","",
            "| Quantity | Valid pixels | Valid % | Min | Mean | Max |",
            "|---|---:|---:|---:|---:|---:|"]
        for name,stat in result["metrics"].items():
            lines.append(f"| {name} | {stat['valid']} | {stat['valid_percent']:.2f} | {stat.get('minimum',float('nan')):.6f} | {stat.get('mean',float('nan')):.6f} | {stat.get('maximum',float('nan')):.6f} |")
        lines.extend(["",f"Full-scene processing: {full_seconds:.2f} s. See results.json for coefficients, hashes and sampled percentiles.","","## Wang ROIs",""])
        for i,roi in enumerate(roi_results,1):
            lines.extend([f"ROI {i}: {roi['window']}; PWV valid: {roi['pwv']['valid_percent']:.2f}%; {roi['pwv_seconds']:.2f} s.",
                          "",f"![ROI {i}](roi_{i}.png)",""])
        lines.extend(["## Checks","",
            "All full-scene blocks passed: finite outputs or NaN, QA propagation, positive absolute temperatures, NDVI bounds.",
            "Wang passed central NoData propagation and nonnegative finite PWV checks.",
            "Differences between methods are not errors against ground truth.",
            "No automatic upper-temperature threshold or upper-PWV clipping was applied."])
        (destination/"REPORT.md").write_text("\n".join(lines)+"\n",encoding="utf-8")
        return result


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input",type=Path,required=True)
    parser.add_argument("--output",type=Path,required=True)
    parser.add_argument("--tile-rows",type=int,default=128)
    args=parser.parse_args()
    if args.tile_rows < 1:
        parser.error("--tile-rows must be positive")
    args.output.mkdir(parents=True,exist_ok=True)
    scenes=[args.input] if list(args.input.glob("*_MTL.txt")) else sorted(p for p in args.input.iterdir() if p.is_dir() and list(p.glob("*_MTL.txt")))
    if not scenes:
        parser.error("No Level-1 scenes found")
    results=[validate(folder,args.output,args.tile_rows) for folder in scenes]
    (args.output/"scene_summary.json").write_text(json.dumps(results,indent=2,allow_nan=False),encoding="utf-8")
    print("All scene checks completed.",flush=True)


if __name__ == "__main__":
    main()
