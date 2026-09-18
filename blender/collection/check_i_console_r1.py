"""Read-only operational sweeps of the exact saved I console."""
import bpy,sys,math,json,hashlib
from pathlib import Path
from mathutils import Matrix,Vector
from mathutils.bvhtree import BVHTree
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(Path(__file__).parent))
from geometry import C
CI=C.inverted();out=ROOT/'review/I_refinement/console_r1';out.mkdir(parents=True,exist_ok=True)
spec=json.loads((ROOT/'production/I_refinement/console_r1/build.json').read_text())
source=ROOT/spec['source'];bpy.ops.wm.open_mainfile(filepath=str(source))
def geom(obj):
    ev=obj.evaluated_get(bpy.context.evaluated_depsgraph_get());mesh=ev.to_mesh();mesh.calc_loop_triangles()
    result=([v.co.copy() for v in mesh.vertices],[tuple(t.vertices) for t in mesh.loop_triangles]);ev.to_mesh_clear();return result
cache={o.name:geom(o) for o in bpy.data.objects if o.type in ['MESH','CURVE','FONT']}
def tree(objects):
    points=[];faces=[];owners=[]
    for o in objects:
        if o.name not in cache:continue
        vs,fs=cache[o.name];offset=len(points);points.extend(o.matrix_world@v for v in vs);faces.extend(tuple(offset+i for i in f) for f in fs);owners.extend([o.name]*len(fs))
    return BVHTree.FromPolygons(points,faces,all_triangles=True),owners
issues=[];count=0
for kind,r in spec['rig'].items():
    root=bpy.data.objects[r['root']];parts=[bpy.data.objects[r['moving']]]
    if kind=='pressure':parts.append(bpy.data.objects[r['indicator']])
    if kind=='gauge':parts.extend(bpy.data.objects[r[k]] for k in ['outgoing','return'])
    moving_set=set(o for p in parts for o in p.children_recursive)
    static=[o for o in root.children_recursive if o not in moving_set]
    for p in parts:p.matrix_basis=Matrix.Identity(4)
    bpy.context.view_layer.update();fixed,fo=tree(static)
    for step in range(25):
        value=step/24;mat=Matrix.Identity(4)
        if kind=='frequency':mat=Matrix.Rotation((-1+value*2)*math.pi*.8,4,Vector((0,0,-1)))
        elif kind=='pressure':mat=Matrix.Translation((0,0,-value*r['stroke']))
        elif kind in ['throat','service']:
            pivot=Vector(r['pivot']);angle=(-1+value*2)*(.52 if kind=='throat' else .26)
            mat=Matrix.Translation(pivot)@Matrix.Rotation(angle,4,Vector((0,1,0)))@Matrix.Translation(-pivot)
        parts[0].matrix_basis=CI@mat@C
        for p in parts[1:]:p.matrix_basis=CI@Matrix.Translation((0,value*(r['indicator_travel'] if kind=='pressure' else r['travel']),0))@C
        bpy.context.view_layer.update();moving,mo=tree(moving_set);count+=1
        pairs=sorted(set((mo[a],fo[b]) for a,b in moving.overlap(fixed)))
        if pairs:issues.append({'kind':kind,'value':value,'pairs':pairs})
report={'passed':not issues,'source_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),'poses':count,'intersections':issues,'scope':'25 positions/control, moving grips and readout floats versus own fixed structure. Excludes base mount, adjacent controls, cowl, containment and continuous volumes.'}
(out/'clearance.json').write_text(json.dumps(report,indent=2)+'\n');print('I_CONSOLE_CLEARANCE',report['passed'],json.dumps(issues[:4]),flush=True)
if issues:raise SystemExit(1)
