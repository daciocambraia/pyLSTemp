"""Validate the complete public module matrix on two real Level-1 scenes."""
from pathlib import Path
import argparse
import json
import sys
import warnings
import hashlib
import numpy as np

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from pylstemp import spectral_index, brightness, emissivity, single_window, split_window, water_vapor
from pylstemp.algorithms import FAMILY_REGISTRIES
from pylstemp.scene import LandsatScene
from pylstemp.calibration import toa_radiance, toa_reflectance
from scripts import matrix_references as ref

def stats(a):
    valid=a[np.isfinite(a)]
    return dict(total=a.size,valid=int(valid.size),minimum=float(valid.min()) if valid.size else None,
        maximum=float(valid.max()) if valid.size else None,mean=float(valid.mean()) if valid.size else None)

def record(cases,identity,call,expected=None,reject=None,mask=None):
    item=dict(identity)
    try:
        with warnings.catch_warnings(),np.errstate(all="ignore"):
            warnings.simplefilter("ignore",RuntimeWarning)
            value=call()
        if reject:raise AssertionError("Expected rejection did not occur")
        if mask is not None:
            assert np.isnan(value[mask]).all(),"Mask did not propagate"
        assert not np.isinf(value).any(),"Infinite output"
        item.update(status="passed",stats=stats(value))
        if expected is not None:item["maximum_reference_error"]=ref.check(value,expected)
        cases.append(item)
        return value
    except Exception as exc:
        item.update(status="expected_rejection" if reject and isinstance(exc,reject) else "failed",
            exception=type(exc).__name__,message=str(exc))
        cases.append(item)
        return None

def export(scene,dest,name,a,core,units,artifacts):
    path=dest/(name+".tif")
    scene.write_geotiff(path,a,window=core,units=units)
    from PIL import Image
    with Image.open(path) as image:
        assert image.mode=="F" and image.size==(a.shape[1],a.shape[0])
        ref.check(np.array(image),a,atol=2e-5)
        assert image.tag_v2.get(42113)=="nan"
        if scene.backend=="pillow":
            original=scene.sources["B2"].tag_v2
            assert tuple(image.tag_v2[34735])==tuple(original[34735])
            assert tuple(image.tag_v2[33550])==tuple(original[33550])
            expected=list(original[33922])
            expected[3]+=core[2]*original[33550][0]
            expected[4]-=core[0]*original[33550][1]
            np.testing.assert_allclose(image.tag_v2[33922],expected,rtol=0,atol=1e-9)
    artifacts.append(dict(path=path.name,validation="passed",sha256=hashlib.sha256(path.read_bytes()).hexdigest()))

def run_roi(scene,dest,index,core,bounds):
    r0,r1,c0,c1=core
    halo=(r0-10,r1+10,c0-10,c1+10)
    optical,thermal,mask=scene.calibrated(halo,exclude_water=True)
    red,nir=optical[4],optical[5]
    t10,t11=thermal[10],thermal[11]
    select=np.s_[10:-10,10:-10]
    cases,artifacts=[],[]
    n=ref.ndvi(nir,red)
    for method in FAMILY_REGISTRIES["spectral_index"].available_keys():
        kwargs=dict(nir=nir,red=red,mask=mask)
        record(cases,dict(module="spectral_index",method=method),
            lambda m=method,k=kwargs:spectral_index(m,**k),ref.spectral(method,nir,red,mask=mask),mask=mask)
    n=np.where(mask,np.nan,n)
    for band in (10,11):
        md=scene.metadata
        raw=scene.read("B"+str(band),halo)
        expected=ref.brightness(raw,md[f"K1_CONSTANT_BAND_{band}"],md[f"K2_CONSTANT_BAND_{band}"],
            md[f"RADIANCE_MULT_BAND_{band}"],md[f"RADIANCE_ADD_BAND_{band}"],mask)
        record(cases,dict(module="brightness",band=band,sensor=scene.sensor),
            lambda b=band,d=raw:brightness(d,b,scene.sensor,rad_gain=md[f"RADIANCE_MULT_BAND_{b}"],
                rad_bias=md[f"RADIANCE_ADD_BAND_{b}"],mask=mask,input_quantity="dn"),expected,mask=mask)
        radiance=toa_radiance(raw,metadata=md,band=band,mask=mask)
        record(cases,dict(module="brightness",band=band,input_quantity="radiance",sensor=scene.sensor),
            lambda b=band,a=radiance:brightness(a,b,metadata=md,mask=mask),expected,mask=mask)
    pwvs={}
    for window in (3,5,21):
        for groups in (1,3):
            key=(window,groups)
            result=record(cases,dict(module="water_vapor",method="wang-2015",window=window,groups=groups),
                lambda w=window,g=groups:water_vapor(t10,t11,n,window_size=w,group_count=g,
                    mask=mask,ndvi_range=bounds),mask=mask)
            if result is None:continue
            pwvs[key]=result
            radius=window//2
            edges=np.linspace(*bounds,groups+1) if not np.isclose(*bounds) else None
            for row,col in ((12,12),(70,140),(140,70),(200,200)):
                sl=np.s_[row-radius:row+radius+1,col-radius:col+radius+1]
                expected=np.nan if mask[row,col] or not np.isfinite(n[row,col]) else ref.water_pixel(
                    t10[sl],t11[sl],n[sl],mask[sl],edges)
                ref.check(np.asarray(result[row,col]),np.asarray(expected),atol=1e-8)
            assert np.all(result[np.isfinite(result)]>=0)
    raw=pwvs[21,3]
    screened=np.where((raw>=.066)&(raw<=7.833),raw,np.nan)
    finite=screened[select][np.isfinite(screened[select])]
    assert finite.size,"ROI has no in-domain PWV"
    mean=float(finite.mean())
    modes=dict(none=None,wang_mean=mean,wang_raster=screened)
    export(scene,dest,f"roi{index}_pwv_raw",raw[select],core,"g/cm2",artifacts)
    export(scene,dest,f"roi{index}_pwv_screened",screened[select],core,"g/cm2",artifacts)
    emi_methods=FAMILY_REGISTRIES["emissivity"].available_keys()
    for method in emi_methods:
        for band in (10,11):
            identity=dict(module="emissivity",method=method,band=band)
            expected=ref.emissivity(method,n,red)[band-10]
            record(cases,identity,lambda m=method,b=band:emissivity(n,b,emissivity_method=m),expected)
    for lst in FAMILY_REGISTRIES["single_channel"].available_keys():
        for emi in emi_methods:
            for unit in ("kelvin","celsius"):
                identity=dict(module="single_channel",lst=lst,emissivity=emi,unit=unit)
                e10,e11=ref.emissivity(emi,n,red)
                expected=ref.temperature(lst,t10,t11,n,e10,e11,mask=mask)
                if unit=="celsius":expected-=273.15
                result=record(cases,identity,lambda l=lst,e=emi,u=unit:single_window(
                    t10,red,nir,lst_method=l,emissivity_method=e,unit=u,mask=mask),expected,mask=mask)
                if result is not None and unit=="kelvin":
                    export(scene,dest,f"roi{index}_{lst}_{emi}",result[select],core,"kelvin",artifacts)


    for lst in FAMILY_REGISTRIES["split_window"].available_keys():
        for emi in emi_methods:
            for mode,pwv in modes.items():
                for unit in ("kelvin","celsius"):
                    identity=dict(module="split_window",lst=lst,emissivity=emi,pwv_mode=mode,unit=unit,
                        pwv_used_by_algorithm=lst in ("du-2015","jimenez-munoz-2014"))
                    reject=None
                    if emi=="avdan-2016":reject=ValueError
                    elif lst=="jimenez-munoz-2014" and pwv is None:reject=ValueError
                    elif lst=="du-2015" and mode=="wang_raster":reject=ValueError
                    elif lst=="du-2015" and pwv is not None and not 0<=pwv<=6.3:reject=ValueError
                    expected=None
                    if reject is None:
                        e10,e11=ref.emissivity(emi,n,red)
                        expected=ref.temperature(lst,t10,t11,n,e10,e11,pwv,mask)
                        if unit=="celsius":expected-=273.15
                    value=record(cases,identity,lambda l=lst,e=emi,u=unit,w=pwv:split_window(
                        t10,t11,red,nir,lst_method=l,emissivity_method=e,unit=u,water_vapor=w,mask=mask),
                        expected,reject=reject,mask=mask)
                    if value is not None and unit=="kelvin":
                        export(scene,dest,f"roi{index}_{lst}_{emi}_{mode}",value[select],core,"kelvin",artifacts)
    # Metadata-based optical calibration, separately from production helpers.
    sza=scene.read("SZA",halo) if "SZA" in scene.sources else None
    elevation=90-sza.astype(float)*.01 if sza is not None else scene.metadata["SUN_ELEVATION"]
    for band in (4,5):
        dn=scene.read(f"B{band}",halo)
        with np.errstate(all="ignore"):
            expected=(dn.astype(float)*scene.metadata[f"REFLECTANCE_MULT_BAND_{band}"]+
                scene.metadata[f"REFLECTANCE_ADD_BAND_{band}"])/np.sin(np.deg2rad(elevation))
        expected=np.where(mask|(dn<=0)|~np.isfinite(expected),np.nan,expected)
        record(cases,dict(module="calibration",band=band,quantity="TOA_reflectance"),
            lambda b=band:toa_reflectance(scene.read(f"B{b}",halo),metadata=scene.metadata,band=b,mask=mask,sun_elevation=elevation),expected,mask=mask)
        expected_radiance=dn.astype(float)*scene.metadata[f"RADIANCE_MULT_BAND_{band}"]+scene.metadata[f"RADIANCE_ADD_BAND_{band}"]
        expected_radiance=np.where(mask|(dn<=0)|~np.isfinite(expected_radiance),np.nan,expected_radiance)
        record(cases,dict(module="calibration",band=band,quantity="TOA_radiance"),
            lambda b=band:optical[b],expected_radiance,mask=mask)
    # Real-pixel chunk-size equivalence; no change to algorithm.
    sub=np.s_[80:144,80:144]
    a=water_vapor(t10[sub],t11[sub],n[sub],mask=mask[sub],ndvi_range=bounds,chunk_rows=1)
    b=water_vapor(t10[sub],t11[sub],n[sub],mask=mask[sub],ndvi_range=bounds,chunk_rows=8)
    ref.check(a,b,atol=1e-10)
    return dict(index=index,window=core,halo=10,cases=cases,artifacts=artifacts,
        pwv_mean_g_cm2=mean,pwv_extrapolation_pixels=int((np.isfinite(raw[select])&
        ((raw[select]<.066)|(raw[select]>7.833))).sum()),pwv_raw_stats=stats(raw[select]),
        pwv_screened_stats=stats(screened[select]),real_chunk_invariance="passed",
        independent_pwv_samples=24)

def probes():
    """Audit suspicious contracts without concealing them as passing tests."""
    cases=[]
    value=spectral_index("ndvi",nir=np.array([[0.]]),red=np.array([[0.]]))
    cases.append(dict(probe="ndvi_zero_denominator",expected="undefined ratio / NaN",
        actual=repr(float(value[0,0])),status="finding" if np.isfinite(value).any() else "passed"))
    for name,call in (
        ("scalar_ndvi",lambda:spectral_index("ndvi",nir=.6,red=.2)),
        ("uppercase_band_alias",lambda:brightness([[10.]],"B10","landsat_8"))):
        try:
            value=call()
            cases.append(dict(probe=name,status="accepted",actual=repr(value)))
        except Exception as exc:
            cases.append(dict(probe=name,status="unsupported",exception=type(exc).__name__,message=str(exc)))
    return cases

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input",type=Path,required=True)
    parser.add_argument("--full-summary",type=Path,required=True)
    parser.add_argument("--output",type=Path,required=True)
    args=parser.parse_args()
    args.output.mkdir(parents=True,exist_ok=False)
    previous=json.loads(args.full_summary.read_text(encoding="utf-8-sig"))
    catalog={family:list(reg.available_keys()) for family,reg in FAMILY_REGISTRIES.items()}
    scenes=[]
    for full in previous["scenes"]:
        with LandsatScene(args.input/full["scene"]) as scene:
            dest=args.output/scene.product_id;dest.mkdir()
            rois=[]
            for i,(fr,fc) in enumerate(((.35,.35),(.5,.5),(.65,.65)),1):
                r,c=int(scene.shape[0]*fr),int(scene.shape[1]*fc)
                rois.append(run_roi(scene,dest,i,(r,r+256,c,c+256),full["ndvi_land_range"]))
                print(scene.sensor,"deep matrix ROI",i,"passed",flush=True)
            result=dict(scene=scene.product_id,sensor=scene.sensor,rois=rois,
                input_sha256=full["input_sha256"],optical_level="Level-1 TOA radiance",optical_units="W m-2 sr-1 um-1",
                coefficient_transfer="Landsat 9 and legacy AVHRR coefficients are not accuracy-validated")
            (dest/"results.json").write_text(json.dumps(result,indent=2,allow_nan=False),encoding="utf-8")
            scenes.append(result)
    result=dict(catalog=catalog,scenes=scenes,diagnostic_probes=probes(),
        scope="three 256x256 ROIs per real scene; full scenes reprocessed separately")
    (args.output/"module_matrix_results.json").write_text(json.dumps(result,indent=2,allow_nan=False),encoding="utf-8")
    failed=[case for scene in scenes for roi in scene["rois"] for case in roi["cases"] if case["status"]=="failed"]
    if failed:raise RuntimeError(f"{len(failed)} unexpected matrix failures")
    print("All supported real-data combinations matched independent references.",flush=True)

if __name__=="__main__":main()
