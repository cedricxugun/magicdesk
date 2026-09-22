"""Read-only panel02 paths from the evaluated, saved R76 extraction endpoint."""
import bpy, json, hashlib, collections
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree

ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'review/I_refinement/nautilus_r1/shell02_after_coupling_r77'
OUT.mkdir(parents=True,exist_ok=True)
manifest=json.loads((ROOT/'app/assets/collection/art/I/coupling_r76/coupling_motion.json').read_text())
source=ROOT/'blender/collection/I_coupling_motion_r76.blend'
assert hashlib.sha256(source.read_bytes()).hexdigest()==manifest['motion_source_sha256']
bpy.ops.wm.open_mainfile(filepath=str(source));bpy.context.scene.frame_set(384)
bpy.context.view_layer.update()
carrier=bpy.data.objects['IN1_PanelPivot_02']
selected=[o for o in [carrier,*carrier.children_recursive] if o.type=='MESH']
assert bpy.data.objects['IN1_PorcelainPanel_02'] in selected
# The animation file keeps the one original pedestal and all parked parts.
parts=[o for o in bpy.context.scene.objects if o.type=='MESH']
assert len([o for o in bpy.context.scene.objects if o.name=='BASE_FIXED'])==1
fixed=[o for o in parts if o not in selected]

def geo(objects):
    v=[];f=[];owners=[];dg=bpy.context.evaluated_depsgraph_get()
    for o in objects:
        e=o.evaluated_get(dg);m=e.to_mesh();m.calc_loop_triangles();start=len(v)
        v.extend(e.matrix_world@x.co for x in m.vertices)
        f.extend(tuple(start+i for i in t.vertices) for t in m.loop_triangles)
        owners.extend([o.name]*len(m.loop_triangles));e.to_mesh_clear()
    return v,f,owners

v,f,n=geo(selected);fv,ff,fn=geo(fixed)
fixed_tree=BVHTree.FromPolygons(fv,ff,all_triangles=True)
fractions=sorted(set([0.,.005,.01,.02,.05]+[i/30 for i in range(1,31)]))
paths=[]
for label,direction in [('down',(0,0,-1)),('left_down',(-.7,0,-.7)),('back_down',(0,.6,-.8)),('front_down',(0,-.6,-.8)),('right_down',(.7,0,-.7))]:
    offset=Vector(direction).normalized()*.6;rows=[]
    for fraction in fractions:
        tree=BVHTree.FromPolygons([p+offset*fraction for p in v],f,all_triangles=True)
        hits=tree.overlap(fixed_tree)
        rows.append({'fraction':fraction,'contacts':len(hits),'owners':dict(collections.Counter(n[a]+' / '+fn[b] for a,b in hits))})
    print('R77_PATH',label,[(r['fraction'],r['contacts']) for r in rows],flush=True)
    paths.append({'name':label,'offset':list(offset),'clear':all(not r['contacts'] for r in rows),'samples':rows})
report={'body_source_sha256':manifest['body_source_sha256'],'motion_source_sha256':manifest['motion_source_sha256'],
        'source_frame':384,'selected':[o.name for o in selected],'retained_meshes':len(fixed),'paths':paths,
        'scope':'Finite straight-translation samples of actual panel02 carrier after evaluated R76 authored mouth/collar extraction. Original base, stationary body and all previously parked parts remain. No new geometry, animation, fastener-release or continuous-clearance claim.'}
(OUT/'probe.json').write_text(json.dumps(report,indent=2)+'\n')
