"""Bake G2 assembly fields from the saved hull UV grid and actual sail surface."""
import bpy,json,hashlib,sys
import numpy as np
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree
from mathutils.geometry import barycentric_transform
ROOT=Path(__file__).resolve().parents[2]
source=ROOT/('blender/collection/G_ship_r3.blend' if '--r3' in sys.argv else 'blender/collection/G_ship_r2.blend');bpy.ops.wm.open_mainfile(filepath=str(source));bpy.context.scene.frame_set(1)
root=bpy.data.objects['GS2_Ship'];out=ROOT/'app/assets/collection/art/G_AI/ship';resolution=512
hull=next(o for o in root.children_recursive if 'LoftedPorcelainHull' in o.name)
samples={};uv=hull.data.uv_layers[0]
for loop in hull.data.loops:
    p=uv.data[loop.index].uv;key=(round(p.x,6),round(p.y,6))
    samples.setdefault(key,hull.data.vertices[loop.vertex_index].co.copy())
xs=sorted({p[0] for p in samples});ys=sorted({p[1] for p in samples})
assert len(samples)==len(xs)*len(ys),'Hull assembly field needs its complete authored UV grid'
grid=np.array([[samples[x,y] for y in ys] for x in xs],dtype=np.float32)
def surface(u,v):
    u=np.interp(u,xs,np.arange(len(xs)));v=np.interp(v,ys,np.arange(len(ys)))
    i=np.minimum(np.floor(u).astype(int),len(xs)-2);j=np.minimum(np.floor(v).astype(int),len(ys)-2)
    a=(u-i)[...,None];b=(v-j)[...,None]
    return (1-a)*(1-b)*grid[i,j]+a*(1-b)*grid[i+1,j]+(1-a)*b*grid[i,j+1]+a*b*grid[i+1,j+1]
U,V=np.meshgrid(np.linspace(0,1,resolution),np.linspace(0,1,resolution));P=surface(U,V)
def blend_distance(a,b,k=.012):
    h=np.maximum(k-abs(a-b),0)/k
    return np.minimum(a,b)-h*h*k*.25
distance=np.linalg.norm(P-surface(U,np.zeros_like(V)),axis=-1)
for boundary in [1.0,.5]:distance=blend_distance(distance,np.linalg.norm(P-surface(U,np.full_like(V,boundary)),axis=-1))
rib_names=[];rib_us=[];xmin=float(grid[:,:,0].min());xmax=float(grid[:,:,0].max())
for obj in root.children_recursive:
    if obj.type=='CURVE' and 'InternalHullRib' in obj.name:
        point=obj.matrix_basis@Vector(obj.data.splines[0].points[0].co[:3]);u=(point.x-xmin)/(xmax-xmin)
        distance=blend_distance(distance,np.linalg.norm(P-surface(np.full_like(U,u),V),axis=-1))
        rib_names.append(obj.name);rib_us.append(u)
distance=np.maximum(0,distance-.0035);maximum=float(distance.max());field=np.clip(distance/maximum,0,1)
def save_field(name,field,progress=None):
    image=bpy.data.images.new(name,width=resolution,height=resolution,alpha=True);image.colorspace_settings.name='Non-Color'
    pixels=np.stack([field,field if progress is None else progress,field,np.ones_like(field)],axis=-1).astype(np.float32)
    image.pixels.foreach_set(pixels.ravel());image.filepath_raw=str(out/(name+'.png'));image.file_format='PNG';image.save()
    return {'texture':'res://'+str(Path(image.filepath_raw).relative_to(ROOT/'app')),'sha256':hashlib.sha256(Path(image.filepath_raw).read_bytes()).hexdigest()}
profile={'version':2,'source_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),
    'method':'Hull field uses distance to actual authored rim/keel/rib projections with rounded advancing corners on outer UV surface. Sail weft rows sample actual triangular cloth mesh; no generic noise.',
    'uv_convention':'Blender image pixels bottom-up; imported glTF UV samples texture directly. Godot UV.y = 1 - source mast-height fraction.',
    'hull':{**save_field('hull_seal',field),'max_distance':maximum,'ribs':rib_names,'rib_u':rib_us,'phase':[.30,.64]},'sails':{},'weft_guides':[]}
weave_path=out/'ivory_sail_weave.png';weave=bpy.data.images.load(str(weave_path),check_existing=True)
pixels=np.array(weave.pixels[:],dtype=np.float32).reshape(weave.size[1],weave.size[0],4)
row_luma=pixels[:,:,:3].mean(axis=(1,2));row_luma=np.clip((row_luma-row_luma.mean())/max(.02,float(row_luma.std())),-1,1)
profile['weave_source_sha256']=hashlib.sha256(weave_path.read_bytes()).hexdigest()
for label,node_name in [('main','GS2_MainBoom'),('jib','GS2_JibBoom')]:
    node=bpy.data.objects[node_name];cloth=next(o for o in node.children if 'TailoredCloth' in o.name)
    mesh=cloth.data;mesh.calc_loop_triangles();layer=mesh.uv_layers[0]
    uv_points=[];triangles=[];positions=[]
    for tri in mesh.loop_triangles:
        first=len(uv_points);uv_points.extend(Vector((*layer.data[li].uv,0)) for li in tri.loops)
        positions.append([cloth.matrix_basis@mesh.vertices[i].co for i in tri.vertices]);triangles.append((first,first+1,first+2))
    tree=BVHTree.FromPolygons(uv_points,triangles,all_triangles=True)
    def at(u,v):
        location,_,index,_=tree.find_nearest(Vector((u,v,0)))
        a,b,c=[uv_points[i] for i in triangles[index]];A,B,C=positions[index]
        return barycentric_transform(location,a,b,c,A,B,C)
    rows=np.linspace(.025,.975,24)
    h=max(p.co.z for p in mesh.vertices)-min(p.co.z for p in mesh.vertices)
    distance=np.min(abs(V[...,None]-rows)*h,axis=-1)
    line=np.clip((.00075-distance)/.00045,0,1);line[U>1-V]=0
    row_delay=.055*np.sin(np.pi*V)+np.interp(V,np.linspace(0,1,len(row_luma)),row_luma)*.010
    width=np.clip(U/np.maximum(.001,1-V),0,1)
    progress=np.clip(width+row_delay*np.sin(np.pi*width),0,1)
    profile['sails'][label]={**save_field(label+'_weft_mask',line,progress),'rows':len(rows),'warp_phase':[.54,.82],'cloth_phase':[.66,.94],'crest_phase':[.90,.995]}
    for v in rows:
        points=[]
        for t in np.linspace(0,1,25):
            p=at(float((1-v)*t),float(v));points.append([p.x,p.z,-p.y+.0015])
        profile['weft_guides'].append({'node':node_name,'points':points,'start':.54,'end':.82,'kind':'weft','delay':float(.055*np.sin(np.pi*v)+np.interp(v,np.linspace(0,1,len(row_luma)),row_luma)*.010)})
path=ROOT/'app/assets/collection/ship_fabrication.json';path.write_text(json.dumps(profile,indent=2)+'\n')
print('SHIP_FABRICATION_FIELDS',json.dumps({'hull_ribs':len(rib_names),'weft_guides':len(profile['weft_guides']),'source_sha256':profile['source_sha256']}),flush=True)
