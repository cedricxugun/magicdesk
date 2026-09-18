"""Ray-measure space between the original A and the candidate cowl."""
import bpy,json,math
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree
ROOT=Path(__file__).resolve().parents[2];OUT=ROOT/'review/I_refinement/nautilus_r1/mouth_finish_r21';s=json.loads((OUT/'build.json').read_text())
bpy.ops.wm.open_mainfile(filepath=str(ROOT/s['source']));bpy.context.scene.frame_set(1);bpy.context.view_layer.update();inv=bpy.data.objects['IAM_MODULE'].matrix_world.inverted()
def tree(objects):
    vertices=[];faces=[]
    for o in objects:
        o.data.calc_loop_triangles();offset=len(vertices);vertices.extend(inv@o.matrix_world@v.co for v in o.data.vertices);faces.extend(tuple(offset+i for i in t.vertices)for t in o.data.loop_triangles)
    return BVHTree.FromPolygons(vertices,faces,all_triangles=True)
a=tree([o for o in bpy.data.objects if o.type=='MESH' and o.name.startswith('IAM_')]);c=tree([bpy.data.objects[n] for n in s['cowl_finish']['modified_meshes']]);rows=[]
for z in [.12353,.14,.16,.18,.20,.22,.24,.25882]:
    samples=[]
    for i in range(128):
        angle=math.tau*(i+.37)/128;direction=Vector((math.cos(angle),math.sin(angle),0));origin=Vector((0,0,z))
        ah=a.ray_cast(origin+direction*1.1,-direction,1.1)[0];ch=c.ray_cast(origin+direction*.7,direction,.6)[0]
        ar=math.hypot(ah.x,ah.y)if ah is not None else None;cr=math.hypot(ch.x,ch.y)if ch is not None else None
        samples.append({'angle':angle,'A_radius':ar,'cowl_inner_radius':cr})
    aa=[r['A_radius'] for r in samples if r['A_radius']is not None];cc=[r['cowl_inner_radius']for r in samples if r['cowl_inner_radius']is not None]
    rows.append({'z':z,'A_max':max(aa)if aa else None,'cowl_min':min(cc)if cc else None,'cowl_samples':len(cc),'samples':samples})
(OUT/'shoulder_channel.json').write_text(json.dumps({'source_sha256':s['source_sha256'],'rows':rows},indent=2)+'\n')
for r in rows:print({k:v for k,v in r.items() if k!='samples'})
