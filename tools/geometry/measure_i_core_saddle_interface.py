"""Measure the actual core, fixed porcelain and saddle at the four existing feet."""
import bpy,json,hashlib,math,sys
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree
ROOT=Path(__file__).resolve().parents[2];args=sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else [];report=ROOT/next((a.split('=',1)[1] for a in args if a.startswith('--report=')),'review/I_refinement/nautilus_r1/front_sockets_r12/build.json');s=json.loads(report.read_text());assert hashlib.sha256((ROOT/s['source']).read_bytes()).hexdigest()==s['source_sha256']
bpy.ops.wm.open_mainfile(filepath=str(ROOT/s['source']));bpy.context.scene.frame_set(1);bpy.context.view_layer.update()
def tree(objects):
    vertices=[];faces=[];owners=[]
    for o in objects:
        o.data.calc_loop_triangles();offset=len(vertices);vertices.extend(o.matrix_world@v.co for v in o.data.vertices)
        faces.extend(tuple(offset+i for i in t.vertices) for t in o.data.loop_triangles);owners.extend(o.name for t in o.data.loop_triangles)
    return BVHTree.FromPolygons(vertices,faces,all_triangles=True),owners
body=bpy.data.objects['IN1_BodyRoot'];meshes=[o for o in body.children_recursive if o.type=='MESH'];core=bpy.data.objects['IN3_ContinuousThroat'];skins=[o for o in meshes if o.name.startswith(('IN1_PorcelainPanel_','IN1_FixedRearShell_')) or o.name=='IN1_FixedMouthCheek05']
targets={'core':tree([core]),'porcelain':tree(skins),'saddle':tree([bpy.data.objects['IN1_LowSaddle']])}
def up_hits(target,x,y):
    bvh,owners=targets[target];start=Vector((x,y,.70));rows=[]
    for _ in range(12):
        hit=bvh.ray_cast(start,Vector((0,0,1)),.8)
        if hit[0] is None or hit[0].z>1.40:break
        rows.append({'z':hit[0].z,'normal':list(hit[1]),'mesh':owners[hit[2]]});start=hit[0]+Vector((0,0,.00001))
    return rows
rows=[]
for index,(x,y) in enumerate([(-.18,.10),(.18,.04),(.17,.34),(-.20,.32)]):
    samples=[]
    for radius in [0.,.025,.045]:
        for k in range(12 if radius else 1):
            a=k*math.tau/12;sx=x+radius*math.cos(a);sy=y+radius*math.sin(a);samples.append({'xy':[sx,sy],'radius':radius,'surfaces':{name:up_hits(name,sx,sy) for name in targets}})
    rows.append({'existing_foot':index+1,'center':[x,y],'samples':samples})
OUT=ROOT/'review/I_refinement/nautilus_r1/core_saddle_r14';OUT.mkdir(parents=True,exist_ok=True);(OUT/'interface_inventory.json').write_text(json.dumps({'source_sha256':s['source_sha256'],'rows':rows,'scope':'Read-only vertical ray measurements at existing saddle shoe footprints. No new support, ports or load path built.'},indent=2)+'\n')
print(json.dumps([{'foot':r['existing_foot'],'center_surfaces':r['samples'][0]['surfaces']} for r in rows],indent=2),flush=True)
