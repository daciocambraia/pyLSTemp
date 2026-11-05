"""Run public notebook paths against aligned synthetic GeoTIFF/MTL/QA inputs."""
import ast
import contextlib
import importlib
import inspect
import io
import json
from pathlib import Path
import re
import warnings
import numpy as np
import pytest

ROOT=Path(__file__).resolve().parents[1]
NOTEBOOKS=sorted((ROOT/'exemple').glob('*.ipynb'))


@pytest.fixture
def prepared_files(tmp_path):
    rasterio=pytest.importorskip('rasterio')
    from rasterio.transform import from_origin
    shape=(40,40);r,c=np.indices(shape);x=(r*40+c)/1600
    arrays={'red':.2+.1*x,'nir':.45+.15*x,'bt10':295+10*x,'bt11':298+.85*(295+10*x-300),
        'radiancia':np.full(shape,10.),'dn':np.full(shape,1000.),'rho_toa':.15+.2*x,
        'e10':np.full(shape,.97),'e11':np.full(shape,.98),'pwv':np.full(shape,1.5),'ndvi':np.full(shape,.35)}
    qa=np.zeros(shape,dtype='uint16');qa[0,0]=8
    arrays.update(qa_pixel=qa,qa_radsat=np.zeros_like(qa))
    paths={}
    for key,data in arrays.items():
        path=tmp_path/(key+'.tif');data=data.astype('uint16' if key.startswith('qa_') else 'float32')
        with rasterio.open(path,'w',driver='GTiff',height=40,width=40,count=1,dtype=data.dtype,
            crs='LOCAL_CS["Notebook fixture",LOCAL_DATUM["Notebook fixture",0],UNIT["metre",1]]',
            transform=from_origin(0,1200,30,30)) as dst:dst.write(data,1)
        paths[key]=path
    fields=dict(SPACECRAFT_ID='LANDSAT_8',PROCESSING_LEVEL='L1TP',SUN_ELEVATION=30.)
    for band in range(1,12):fields.update({f'RADIANCE_MULT_BAND_{band}':.01,f'RADIANCE_ADD_BAND_{band}':.1,
        f'REFLECTANCE_MULT_BAND_{band}':.0001,f'REFLECTANCE_ADD_BAND_{band}':-.1})
    for band in (10,11):fields.update({f'K1_CONSTANT_BAND_{band}':774.8853,f'K2_CONSTANT_BAND_{band}':1321.0789})
    mtl=tmp_path/'MTL.txt';mtl.write_text('\n'.join(f'{k} = {json.dumps(v)}' for k,v in fields.items()),encoding='utf-8')
    paths['mtl']=mtl
    return paths


@pytest.mark.parametrize('path',NOTEBOOKS,ids=lambda p:p.stem)
def test_notebook_main_path(path,prepared_files,tmp_path):
    files=prepared_files
    aliases={'emissividade':'e10','ndvi_preparado':'ndvi','radiancia10':'radiancia','reference':'red'}
    notebook=json.loads(path.read_text(encoding='utf-8'))
    cells=[c for c in notebook['cells'] if c['cell_type']=='code']
    assert len(cells)==4
    ns={};destination=tmp_path/'outputs'
    for i,cell in enumerate(cells):
        tree=ast.parse(''.join(cell['source']))
        if i==0:
            for node in tree.body:
                if isinstance(node,ast.Assign) and isinstance(node.targets[0],ast.Name):
                    name=node.targets[0].id
                    if isinstance(node.value,ast.Call) and isinstance(node.value.func,ast.Name) and node.value.func.id=='Path':
                        if name.endswith('_path'):
                            key=name[:-5];node.value.args=[ast.Constant(files[aliases.get(key,key)].as_posix())]
                        elif name=='saida':node.value.args=[ast.Constant(destination.as_posix())]
                    elif name=='elevacao_solar':node.value=ast.Constant(45.)
        with contextlib.redirect_stdout(io.StringIO()),warnings.catch_warnings():
            warnings.simplefilter('ignore',RuntimeWarning)
            exec(compile(ast.fix_missing_locations(tree),str(path),'exec'),ns)
        if i==0:ns['saida']=destination
    image=ns.get('imagem_com_mascara',ns.get('imagem',ns.get('lst')))
    assert image.shape==(40,40) and np.isnan(image[0,0]) and np.isfinite(image).any()
    outputs=list(destination.glob('*.tif'));assert outputs
    import rasterio
    with rasterio.open(outputs[0]) as src:
        assert src.shape==(40,40) and src.crs is not None
        assert src.transform.c==0 and src.transform.f==1200


def test_readme_exports_and_documented_python_calls_match_installed_api():
    import pylstemp
    text=(ROOT/'README.md').read_text(encoding='utf-8')
    section=text.split('## API publica',1)[1].split('## Algoritmos e artigos',1)[0]
    rows=set(re.findall(r'^\| `([^`]+)` \|',section,re.M))
    assert {n for n in pylstemp.__all__ if callable(getattr(pylstemp,n))}<=rows
    functions={name:getattr(pylstemp,name) for name in pylstemp.__all__ if callable(getattr(pylstemp,name))}
    for path in [ROOT/'README.md',*(ROOT/'docs').glob('*.md'),ROOT/'exemple/README.md']:
        content=path.read_text(encoding='utf-8')
        for target in re.findall(r'\]\(([^)]+)\)',content):
            if '://' not in target and not target.startswith(('#','mailto:')):
                assert (path.parent/target.split('#')[0]).exists(),(path,target)
        for block in re.findall(r'```python\s*\n(.*?)```',content,re.S):
            for node in ast.walk(ast.parse(block)):
                if isinstance(node,ast.ImportFrom) and node.module.startswith('pylstemp'):
                    module=importlib.import_module(node.module)
                    for name in node.names:assert hasattr(module,name.name),(path,name.name)
                if isinstance(node,ast.Call) and isinstance(node.func,ast.Name) and node.func.id in functions:
                    params=inspect.signature(functions[node.func.id]).parameters
                    extra=any(v.kind==v.VAR_KEYWORD for v in params.values())
                    for kw in node.keywords:
                        if kw.arg is not None:assert kw.arg in params or extra,(path,node.func.id,kw.arg)
