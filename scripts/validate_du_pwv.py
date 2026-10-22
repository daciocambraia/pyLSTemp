"""Reproducible real-scene Du general / Wang mean / Wang raster checks."""
import argparse
import hashlib
import itertools
import json
from pathlib import Path
import platform
import sys
import numpy as np
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from pylstemp import spectral_index, __version__
from pylstemp.scene import LandsatScene
from pylstemp.workflows import du_from_scene, scene_ndvi_range
from scripts import matrix_references as ref


def stats(a):
    finite=a[np.isfinite(a)]
    return dict(total=int(a.size),valid=int(finite.size),
                mean=float(finite.mean()) if finite.size else None,
                quantiles=np.quantile(finite,[0,.05,.5,.95,1]).tolist() if finite.size else [])


def validate_scene(folder,destination,size):
    with LandsatScene(folder) as scene:
        bounds=scene_ndvi_range(scene)
        print(scene.product_id,'full-scene NDVI bounds',bounds,flush=True)
        h,w=scene.shape
        r,c=h//2-size//2,w//2-size//2
        core=(r,r+size,c,c+size)
        results={mode:du_from_scene(scene,window=core,pwv_mode=mode,ndvi_range=bounds)
                 for mode in ('general','mean','raster')}
        # Independent LST equation and Wang scalar-window references.
        halo=(r-10,r+size+10,c-10,c+size+10)
        opt,bt,mask=scene.calibrated(halo,exclude_water=True)
        ndvi=spectral_index('ndvi',nir=opt[5],red=opt[4],mask=mask)
        e10,e11=ref.emissivity('gopinadh-2018',ndvi,opt[4])
        sl=np.s_[10:-10,10:-10]
        errors={}
        for mode in ('mean','raster'):
            water=results[mode].provenance['mean_pwv'] if mode=='mean' else results[mode].pwv
            expected=ref.temperature('du-2015',bt[10][sl],bt[11][sl],ndvi[sl],e10[sl],e11[sl],water,mask[sl])
            errors[mode]=ref.check(results[mode].lst,expected,atol=2e-10)
        # General mode includes QA water, using exactly its own validity policy.
        go,gb,gm=scene.calibrated(core)
        gn=spectral_index('ndvi',nir=go[5],red=go[4],mask=gm)
        ge10,ge11=ref.emissivity('gopinadh-2018',gn,go[4])
        errors['general']=ref.check(results['general'].lst,
            ref.temperature('du-2015',gb[10],gb[11],gn,ge10,ge11,None,gm),atol=2e-10)
        edges=np.linspace(*bounds,4)
        samples=[]
        for row,col in ((12,12),(size//2,size//2),(size-13,size-13)):
            rr,cc=row+10,col+10
            ws=np.s_[rr-10:rr+11,cc-10:cc+11]
            expected=np.nan if mask[rr,cc] else ref.water_pixel(bt[10][ws],bt[11][ws],ndvi[ws],mask[ws],edges)
            error=ref.check(np.asarray(results['raster'].pwv_raw[row,col]),np.asarray(expected),atol=1e-8)
            samples.append(dict(row=row,col=col,error=error))
        for a,b in ((r,r+size//2),(r+size//2,r+size)):
            for x,y in ((c,c+size//2),(c+size//2,c+size)):
                tile=du_from_scene(scene,window=(a,b,x,y),pwv_mode='raster',ndvi_range=bounds,chunk_rows=1)
                target=np.s_[a-r:b-r,x-c:y-c]
                ref.check(tile.pwv_raw,results['raster'].pwv_raw[target],atol=1e-8)
                ref.check(tile.lst,results['raster'].lst[target],atol=2e-10)
        artifacts=[]
        import rasterio
        from rasterio.windows import Window,transform
        expected_transform=transform(Window(c,r,size,size),scene.sources['B4'].transform)
        for mode,result in results.items():
            dest=destination/scene.product_id/mode
            result.export(scene,dest)
            for path in dest.glob('*.tif'):
                with rasterio.open(path) as src:
                    assert src.shape==(size,size) and src.dtypes==('float32',)
                    assert np.isnan(src.nodata) and src.crs==scene.sources['B4'].crs
                    assert src.transform==expected_transform and src.tags().get('units')
                    value=src.read(1)
                    key=path.stem
                    expected={'lst_du':result.lst,'lst_invalid':result.invalid_mask,
                              'pwv':result.pwv,'pwv_raw':result.pwv_raw,
                              'pwv_invalid':None if result.pwv is None else ~np.isfinite(result.pwv)}[key]
                    np.testing.assert_allclose(value,np.asarray(expected,dtype=np.float32),rtol=0,atol=0,equal_nan=True)
                artifacts.append(dict(path=str(path.relative_to(destination)),sha256=hashlib.sha256(path.read_bytes()).hexdigest()))
        common=np.logical_and.reduce([np.isfinite(x.lst) for x in results.values()])
        paired={}
        for a,b in itertools.combinations(results,2):
            pair=np.isfinite(results[a].lst)&np.isfinite(results[b].lst)
            paired[a+' minus '+b]=dict(pair_support=int(pair.sum()),
                pair_difference=stats((results[a].lst-results[b].lst)[pair]),
                all_common_difference=stats((results[a].lst-results[b].lst)[common]))
        record=dict(scene=scene.product_id,window=list(core),ndvi_range=list(bounds),
            mtl_sha256=hashlib.sha256(scene.mtl_path.read_bytes()).hexdigest(),
            common_support=int(common.sum()),pairs=paired,reference_errors_K=errors,
            pwv_scalar_reference_samples=samples,tiles_and_chunk_equivalence='passed',
            modes={mode:dict(provenance=x.provenance,lst=stats(x.lst),
                            pwv=None if x.pwv is None else stats(x.pwv)) for mode,x in results.items()},artifacts=artifacts,
            original_estimator='pending: Du coefficient-order inconsistency; Ren equation images unavailable; no inferred formula implemented')
        print(scene.product_id,'passed',len(artifacts),'GeoTIFFs',flush=True)
        return record


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--input',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--size',type=int,default=128)
    args=parser.parse_args()
    if args.size<32:parser.error('--size must be >=32')
    args.output.mkdir(parents=True,exist_ok=False)
    scenes=[p for p in sorted(args.input.iterdir()) if p.is_dir() and list(p.glob('*_MTL.txt'))]
    if not scenes:raise ValueError('No scenes found')
    output=dict(version=__version__,python=sys.version,platform=platform.platform(),numpy=np.__version__,
                scope='controlled real ROIs; no field accuracy validation',scenes=[])
    for folder in scenes:
        output['scenes'].append(validate_scene(folder,args.output,args.size))
        (args.output/'results.json').write_text(json.dumps(output,indent=2,allow_nan=False),encoding='utf8')

if __name__=='__main__':main()
