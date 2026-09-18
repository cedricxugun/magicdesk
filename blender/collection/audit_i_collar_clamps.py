"""Read-only measurements of current ceramic/latch fit before local refinement."""
import bpy, json, hashlib, math
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree
ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'review/I_refinement/part_a_mouth/shutter_r2/collar_clamps'
spec=json.loads((OUT.parent/'diaphragm/build.json').read_text())
source=ROOT/spec['source'];assert hashlib.sha256(source.read_bytes()).hexdigest()==spec['source_sha256']
bpy.ops.wm.open_mainfile(filepath=str(source));bpy.context.scene.frame_set(1);bpy.context.view_layer.update()
mouth=bpy.data.objects['IAM_Mouth'];inv=mouth.matrix_world.inverted();trees={};inventory=[]
for o in bpy.data.objects:
    if o.type!='MESH':continue
    if any(t in o.name for t in ['PorcelainUpper','PorcelainLower','CollarLatchSeat','EnamelLatchBar','LatchCaptiveHead','LatchSlottedCap','EyelidFixedCarrier']):
        v=[inv@o.matrix_world@p.co for p in o.data.vertices]
        inventory.append({'name':o.name,'vertices':len(v),'bounds':[[min(p[k] for p in v) for k in range(3)],[max(p[k] for p in v) for k in range(3)]]})
    if 'PorcelainUpper' in o.name or 'PorcelainLower' in o.name:
        m=o.data;m.calc_loop_triangles();trees[o.name]=BVHTree.FromPolygons([inv@o.matrix_world@p.co for p in m.vertices],[tuple(t.vertices) for t in m.loop_triangles],all_triangles=True)
samples=[]
for i in range(6):
    a=.2+i*math.tau/6
    for radius in [.802,.808,.816,.824,.832,.838,.846,.854,.864,.875]:
        x,y=radius*math.cos(a),radius*math.sin(a);hits=[]
        for name,tree in trees.items():
            front=tree.ray_cast(Vector((x,y,-.5)),Vector((0,0,1)),1.)
            rear=tree.ray_cast(Vector((x,y,.5)),Vector((0,0,-1)),1.)
            if front[0] is not None:hits.append({'porcelain':name,'front_z':front[0].z,'rear_z':rear[0].z})
        assert len(hits)==1,(i,radius,hits)
        samples.append({'index':i,'angle':a,'radius':radius,**hits[0]})
OUT.mkdir(parents=True,exist_ok=True)
(OUT/'seed_audit.json').write_text(json.dumps({'source_sha256':spec['source_sha256'],'component_sha256':spec['component_sha256'],'inventory':inventory,'front_rear_rays':samples,'scope':'Actual current ceramic and clamp geometry; read-only. Ray coordinates are mouth-local scene units, not millimeters.'},indent=2)+'\n')
print('I_COLLAR_SEED_AUDIT',len(samples),len(inventory),flush=True)
