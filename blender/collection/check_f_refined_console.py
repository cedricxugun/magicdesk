"""Actual manufactured F control meshes at operational endpoints and intermediate poses."""
import bpy,sys,math,json,hashlib
from pathlib import Path
from mathutils import Matrix,Vector
from mathutils.bvhtree import BVHTree
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(Path(__file__).parent))
from geometry import C
source=ROOT/'blender/collection/F_Refined_Controls.blend';bpy.ops.wm.open_mainfile(filepath=str(source));CI=C.inverted()
def geom(obj):
    ev=obj.evaluated_get(bpy.context.evaluated_depsgraph_get());mesh=ev.to_mesh();mesh.calc_loop_triangles()
    data=([v.co.copy() for v in mesh.vertices],[tuple(p.vertices) for p in mesh.loop_triangles]);ev.to_mesh_clear();return data
cache={o.name:geom(o) for o in bpy.data.objects if o.type in ['MESH','CURVE','FONT']}
def tree(objs):
    points=[];faces=[];owners=[]
    for o in objs:
        if o.name not in cache:continue
        vs,fs=cache[o.name];first=len(points);points.extend(o.matrix_world@v for v in vs);faces.extend(tuple(first+j for j in face) for face in fs);owners.extend([o.name]*len(fs))
    return BVHTree.FromPolygons(points,faces,all_triangles=True),owners
issues=[];count=0
for kind in ['rotary','hold','detent','gauge','service']:
    root=bpy.data.objects['FCTRL_'+kind];static=next(o for o in root.children if o.name.startswith('WidgetSocket'));moving=next(o for o in root.children if o.name.startswith('MovingGrip'))
    moving.matrix_basis=Matrix.Identity(4);bpy.context.view_layer.update();fixed,fo=tree(static.children_recursive)
    for j in range(25):
        value=j/24 if kind in ['hold','gauge'] else -1+2*j/24
        mat=Matrix.Identity(4)
        if kind=='rotary':mat=Matrix.Rotation(value*math.pi*.8,4,Vector((0,0,-1)))
        elif kind=='gauge':mat=Matrix.Rotation(-1+value*2,4,Vector((0,0,-1)))
        elif kind=='hold':mat=Matrix.Translation((0,0,-value*.010))
        else:
            pivot=Vector((0,0,.037 if kind=='detent' else .043));axis=Vector((1,0,0)) if kind=='detent' else Vector((0,1,0))
            angle=value*(-.325 if kind=='detent' else .26);mat=Matrix.Translation(pivot)@Matrix.Rotation(angle,4,axis)@Matrix.Translation(-pivot)
        moving.matrix_basis=CI@mat@C;bpy.context.view_layer.update();a,ao=tree(moving.children_recursive);count+=1
        pairs=set((ao[x],fo[y]) for x,y in a.overlap(fixed))
        if pairs:issues.append({'kind':kind,'value':value,'pairs':sorted(pairs)})
report={'passed':not issues,'poses':count,'source_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),'intersections':issues,'scope':'Each control moving group against its own fixed parts, 25 poses. Does not certify mounting to shared base, cowl sweep, cross-control clearance, input or visual quality.'}
out=ROOT/'review/F_complete/revision_20260911';out.mkdir(exist_ok=True);(out/'console_clearance.json').write_text(json.dumps(report,indent=2)+'\n');print('F_CONSOLE_CLEARANCE',json.dumps({'passed':not issues,'poses':count,'first':issues[:5]}),flush=True)
if issues:raise SystemExit(1)
