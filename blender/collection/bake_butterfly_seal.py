"""Bake numeric formation fields from authored wing veins. No geometry edits."""
import bpy,json,hashlib
import numpy as np
from pathlib import Path
from mathutils import Vector
ROOT=Path(__file__).resolve().parents[2]
source=ROOT/'blender/collection/G_butterfly_r2.blend'
bpy.ops.wm.open_mainfile(filepath=str(source));bpy.context.scene.frame_set(120)
resolution=512;profile={'version':1,'source_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),'method':'Distance outside the projected metal radius of actual front spars, rim and inlay seats; wing-local X/Z data, not color or noise','image_v':'Blender pixels bottom-up; shader flips normalized local height to PNG top-down','wings':{}}
folder=ROOT/'app/assets/collection/art/G_AI'
for label,node_name,seal,red,metal in [('upper','GB2_WingUpper1',[.54,.86],[.88,.98],[.28,.54]),('lower','GB2_WingLower1',[.60,.90],[.92,.995],[.32,.58])]:
    wing=bpy.data.objects[node_name];shell=next(o for o in wing.children if 'DomedWingEnamel' in o.name)
    vertices=[shell.matrix_basis@v.co for v in shell.data.vertices]
    xmin=min(p.x for p in vertices);xmax=max(p.x for p in vertices);ymin=min(p.z for p in vertices);ymax=max(p.z for p in vertices)
    xs=np.linspace(xmin,xmax,resolution,dtype=np.float32);ys=np.linspace(ymin,ymax,resolution,dtype=np.float32);X,Y=np.meshgrid(xs,ys)
    distance=np.full(X.shape,np.inf,dtype=np.float32);paths=[];outline=None
    for obj in wing.children:
        if obj.type!='CURVE' or not any(key in obj.name for key in ['CurvedWingSpar','WingRolledGoldRim','CurvedInlaySeat']):continue
        points=[obj.matrix_basis@Vector(p.co[:3]) for spline in obj.data.splines for p in spline.points]
        path=[(p.x,p.z) for p in points];paths.append(path)
        if 'WingRolledGoldRim' in obj.name:outline=path
        for a,b in zip(path,path[1:]):
            dx=b[0]-a[0];dy=b[1]-a[1];length=dx*dx+dy*dy
            if length<1e-12:continue
            t=np.clip(((X-a[0])*dx+(Y-a[1])*dy)/length,0,1)
            distance=np.minimum(distance,np.maximum(0,np.sqrt((X-a[0]-t*dx)**2+(Y-a[1]-t*dy)**2)-obj.data.bevel_depth))
    assert outline and len(paths)==7
    inside=np.zeros(X.shape,dtype=bool)
    for a,b in zip(outline,outline[1:]):
        if abs(a[1]-b[1])<1e-12:continue
        inside^=((a[1]>Y)!=(b[1]>Y))&(X<(b[0]-a[0])*(Y-a[1])/(b[1]-a[1])+a[0])
    maximum=float(distance[inside].max());field=np.clip(distance/maximum,0,1)
    pixels=np.stack([field,field,field,np.ones_like(field)],axis=-1).astype(np.float32)
    image=bpy.data.images.new('Butterfly_'+label+'_seal_data',width=resolution,height=resolution,alpha=True)
    image.colorspace_settings.name='Non-Color';image.pixels.foreach_set(pixels.ravel());image.file_format='PNG'
    path=folder/f'butterfly_{label}_seal.png';image.filepath_raw=str(path);image.save()
    profile['wings'][label]={'texture':'res://'+str(path.relative_to(ROOT/'app')),'bounds':[xmin,ymin,xmax-xmin,ymax-ymin],'max_distance':maximum,'paths':len(paths),'seal_phase':seal,'red_phase':red,'metal_phase':metal,'texture_sha256':hashlib.sha256(path.read_bytes()).hexdigest()}
path=ROOT/'app/assets/collection/butterfly_seal.json';path.write_text(json.dumps(profile,indent=2)+'\n')
print('BUTTERFLY_SEAL_BAKED',json.dumps(profile),flush=True)
