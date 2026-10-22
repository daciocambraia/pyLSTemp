"""Rozenstein + Sobrino 2008 + Chavez in a controlled Landsat ROI.

Run: python exemples/metodos_imagem.py SCENE --saida resultados/metodos
Parameters fitted here describe this ROI; they are not a full-scene haze fit.
"""
from pathlib import Path
import argparse
import json
from pylstemp import (toa_reflectance, spectral_index, water_vapor, fit_chavez,
                     chavez_reflectance, sobrino_2008, split_window_from_emissivity)
from pylstemp.scene import LandsatScene
from pylstemp.workflows import scene_ndvi_range


def executar(pasta, saida, perfil):
    dest=Path(saida);dest.mkdir(parents=True,exist_ok=True)
    with LandsatScene(pasta) as cena:
        h,w=cena.shape
        if h<148 or w<148:
            raise ValueError("This example requires at least 148x148 pixels for a 128x128 ROI plus halo.")
        r,c=h//2-64,w//2-64
        janela=(r,r+128,c,c+128);halo=(r-10,r+138,c-10,c+138)
        limites=scene_ndvi_range(cena)
        opt,bt,mascara=cena.calibrated(halo,exclude_water=True)
        n=spectral_index("ndvi",nir=opt[5],red=opt[4],mask=mascara)
        pwv=water_vapor(bt[10],bt[11],n,mask=mascara,ndvi_range=limites)
        recorte=(slice(10,-10),slice(10,-10))
        pwv=pwv[recorte];mascara=mascara[recorte]
        elevacao=float(cena.metadata["SUN_ELEVATION"])
        rho={b:toa_reflectance(cena.read("B"+str(b),janela),metadata=cena.metadata,
                              band=b,sun_elevation=elevacao,mask=mascara) for b in (4,5)}
        parametros={b:fit_chavez(rho[b],sun_elevation=elevacao,method="cost",mask=mascara) for b in (4,5)}
        corrigido={b:chavez_reflectance(rho[b],parameters=parametros[b],mask=mascara) for b in (4,5)}
        ndvi=spectral_index("ndvi",nir=corrigido[5],red=corrigido[4],mask=mascara)
        # Controlled combination: Sobrino's squared FVC with existing Rongali
        # TIRS endmembers. These parameters do not constitute new calibration.
        e10=sobrino_2008(ndvi,soil_emissivity=.971,vegetation_emissivity=.987,mask=mascara)
        e11=sobrino_2008(ndvi,soil_emissivity=.977,vegetation_emissivity=.989,mask=mascara)
        lst=split_window_from_emissivity(bt[10][recorte],bt[11][recorte],e10,e11,
                    lst_method="rozenstein-2014",water_vapor=pwv,mask=mascara,
                    atmospheric_profile=perfil,temperature_range="0-60")
        for name,value,unit in (("red_cost",corrigido[4],"dimensionless"),
                                ("nir_cost",corrigido[5],"dimensionless"),
                                ("ndvi_cost",ndvi,"dimensionless"),
                                ("emissivity10",e10,"dimensionless"),
                                ("emissivity11",e11,"dimensionless"),
                                ("pwv_wang",pwv,"g/cm2"),("lst_rozenstein",lst,"kelvin")):
            cena.write_geotiff(dest/(name+".tif"),value,window=janela,units=unit)
        provenance=dict(product=cena.product_id,window=janela,halo=halo,
            pwv="Wang, radiance NDVI, full-scene grouping bounds",ndvi_bounds=limites,
            chavez_fit_scope="controlled ROI",chavez_parameters={str(b):vars(p) for b,p in parametros.items()},
            emissivity="Sobrino 2008 Eq.9 with supplied Rongali 2018 endmembers",
            atmospheric_profile=perfil,temperature_range="0-60 Celsius",lst_units="kelvin",
            warning="Experimental combination; profile representativeness and field accuracy not established")
        (dest/"provenance.json").write_text(json.dumps(provenance,indent=2),encoding="utf8")


if __name__=="__main__":
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("cena",type=Path)
    parser.add_argument("--saida",type=Path,default=Path("resultados/metodos_imagem"))
    parser.add_argument("--perfil",required=True,choices=["us-standard-1976","midlatitude-summer"])
    args=parser.parse_args()
    executar(args.cena,args.saida,args.perfil)
