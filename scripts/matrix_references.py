"""Independent equation checks for the validation matrix, not retrieval algorithms.

No production helpers or constants are imported. Values follow the source
decisions documented in docs/scientific-methods.md. Agreement checks numerical
implementation, not ground-truth accuracy or AVHRR-to-Landsat transfer.
"""
import numpy as np

# Du Table 1 coefficient sets in increasing CWV interval order.
DU = (
 ((0,2.5),(-2.78009,1.01408,.15833,-.34991,4.04487,3.55414,-8.88394,.09152)),
 ((2,3.5),(11.00824,.95995,.17243,-.28852,7.11492,.42684,-6.62025,-.06381)),
 ((3,4.5),(9.62610,.96202,.13834,-.17262,7.87883,5.17910,-13.26611,-.07603)),
 ((4,5.5),(.61258,.99124,.10051,-.09664,7.85758,6.86626,-15.00742,-.01185)),
 ((5,6.3),(-.34808,.98123,.05599,-.03518,11.96444,9.06710,-14.74085,-.20471)),
)
DU_ALL=(-.41165,1.00522,.14543,-.27297,4.06655,-6.92512,-18.27461,.24468)
THERMAL = {
 ("landsat_8",10):(774.8853,1321.0789,.0003342,.1),
 ("landsat_8",11):(480.8883,1201.1442,.0003342,.1),
 ("landsat_9",10):(799.0284,1329.2405,.00038,.1),
 ("landsat_9",11):(475.6581,1198.3494,.000349,.1),
}

def ndvi(nir,red):
    nir,red=np.asarray(nir,dtype=float),np.asarray(red,dtype=float)
    with np.errstate(all="ignore"):
        value=(nir-red)/(nir+red+1e-15)
    return np.where(np.isfinite(value)&(np.abs(value)<=1),value,np.nan)

def spectral(index,nir,red,blue=None,mask=None):
    if index=="ndvi":
        value=ndvi(nir,red)
    else:
        nir,red,blue=(np.asarray(a,dtype=float) for a in (nir,red,blue))
        with np.errstate(all="ignore"):
            value=2.5*(nir-red)/(1+nir+6*red-7.5*blue)
        value=np.where(np.isfinite(value)&(np.abs(value)<=1),value,np.nan)
    return np.where(mask,value*0+np.nan,value) if mask is not None else value

def brightness(dn,k1,k2,gain,bias,mask=None):
    a=np.asarray(dn,dtype=float)
    with np.errstate(all="ignore"):
        radiance=gain*a+bias
        value=k2/np.log1p(k1/radiance)
    invalid=(a<=0)|~np.isfinite(a)|(radiance<=0)|~np.isfinite(value)
    if mask is not None: invalid|=mask
    return np.where(invalid,np.nan,value)

def emissivity(method,index,red):
    n=np.asarray(index,dtype=float)
    pv=np.clip(((n-.2)/.3)**2,0,1)
    # Match the documented FVC endmembers outside the mixed NDVI class.
    pv=np.where(n<.2,0,np.where(n>.5,1,pv))
    if method=="avdan-2016":
        value=np.select([n<0,n<.2,n<=.5,n<=1],[.991,.966,.971+.007*pv,.973],default=np.nan)
        pair=(value,value.copy())
    elif method=="gopinadh-2018":
        fraction=np.clip((n-.15)/.33,0,1)
        pair=(.971+.016*fraction,.977+.012*fraction)
    else:
        red=np.asarray(red,dtype=float)
        values=[]
        for soil,veg,a,b in ((.9668,.9863,.973,.047),(.9747,.9896,.984,.026)):
            cavity=.55*(1-soil)*veg*(1-pv)
            values.append(np.select([n<.2,n<=.5,n<=1],
                [a-b*red,soil+(veg-soil)*pv+cavity,veg+cavity],default=np.nan))
        pair=tuple(values)
    invalid=~np.isfinite(n)|(np.abs(n)>1)
    return tuple(np.where(invalid|~np.isfinite(v)|(v<=0)|(v>1),np.nan,v) for v in pair)

def temperature(method,t10,t11,n,e10,e11,pwv=None,mask=None):
    t10,t11,e10,e11=(np.asarray(a,dtype=float) for a in (t10,t11,e10,e11))
    invalid=~np.isfinite(t10)|(t10<=0)|~np.isfinite(e10)|(e10<=0)|(e10>1)
    if mask is not None: invalid|=mask
    if method!="mono-window-2016":
        invalid|=~np.isfinite(t11)|(t11<=0)|~np.isfinite(e11)|(e11<=0)|(e11>1)
    with np.errstate(all="ignore"):
        delta=t10-t11
        if method=="mono-window-2016":
            value=1/(1/t10+(10.895e-6/.01438)*np.log(e10))
        elif method=="price-1984":
            value=(4.33*t10-3.33*t11)*(1+(1-e10)/4.5)+.75*t11*(e10-e11)
        elif method=="sobrino-1993":
            value=t10+1.06*delta+.46*delta**2+53*(1-2*e10+e11)
        elif method=="kerr-1992":
            fraction=np.clip((n-.11)/.61,0,1)
            value=t10+2.1*delta+3.1+fraction*(.5*delta-5.5)
        elif method=="jimenez-munoz-2014":
            w=np.asarray(pwv,dtype=float)
            invalid|=~np.isfinite(w)|(w<0)
            value=t10+1.378*delta+.183*delta**2-.268
            value+=(54.3-2.238*w)*(1-(e10+e11)/2)+(-129.2+16.4*w)*(e10-e11)
        else:
            coeffs=[DU_ALL] if pwv is None else [c for (lo,hi),c in DU if lo<=float(pwv)<=hi]
            if not coeffs: raise ValueError("Du CWV outside table domain")
            m=(t10+t11)/2
            q=(2-e10-e11)/(e10+e11)
            z=4*(e10-e11)/(e10+e11)**2
            features=np.stack([np.ones(t10.shape),m,q*m,z*m,delta/2,q*delta/2,z*delta/2,delta**2])
            value=np.mean([np.tensordot(c,features,axes=1) for c in coeffs],axis=0)
    return np.where(invalid|~np.isfinite(value)|(value<=0),np.nan,value)

def check(actual,expected,atol=1e-9):
    np.testing.assert_allclose(actual,expected,rtol=0,atol=atol,equal_nan=True)
    valid=np.isfinite(actual)&np.isfinite(expected)
    return float(np.max(np.abs(actual[valid]-expected[valid]))) if valid.any() else None



def water_pixel(t10,t11,n,mask,edges):
    """Independent centered-window regression for a single valid center."""
    good=(~mask)&np.isfinite(t10)&np.isfinite(t11)&np.isfinite(n)&(t10>0)&(t11>0)&(np.abs(n)<=1)
    totals=[]
    groups=[good] if edges is None else [good&(n>=lo)&((n<=hi) if i==len(edges)-2 else (n<hi))
        for i,(lo,hi) in enumerate(zip(edges[:-1],edges[1:]))]
    for group in groups:
        x,y,z=t10[group],t11[group],n[group]
        if x.size<2:continue
        dx,dy=x-x.mean(),y-y.mean()
        keep=(np.abs(dx)>np.abs(dy))&(dx*dy>=0)
        dx,dy,z=dx[keep],dy[keep],z[keep]
        if dx.size<2:continue
        vx,vy,cov=float(dx@dx),float(dy@dy),float(dx@dy)
        if np.isclose(vx,0) or np.isclose(vy,0) or cov**2/(vx*vy)<.97:continue
        mean=float(z.mean())
        e_ratio=.9939 if mean<.2 else .9966 if mean>.5 else (.0195*((mean-.2)/.3)**2+.9688)/(.0149*((mean-.2)/.3)**2+.9747)
        ratio=e_ratio*(cov/vx+vy/cov)/2
        w=19.13-18.973*ratio if ratio>.9 else 14.158-13.412*ratio
        if np.isfinite(w) and w>=0:totals.append((w,dx.size))
    return sum(w*c for w,c in totals)/sum(c for _,c in totals) if totals else np.nan
