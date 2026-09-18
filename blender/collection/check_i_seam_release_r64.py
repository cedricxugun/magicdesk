"""Actual threaded-retainer and stud withdrawal against the current assembly."""
import bpy,json,hashlib,math,collections,sys
from pathlib import Path
from mathutils import Vector,Matrix,Quaternion
from mathutils.bvhtree import BVHTree
ROOT=Path(__file__).resolve().parents[2];OUT=ROOT/'review/I_refinement/nautilus_r1/seam_fasteners_r64';s=json.loads((OUT/'build.json').read_text())
if '--oriented'in sys.argv:OUT=OUT/'oriented_r2';s=json.loads((OUT/'build.json').read_text())
assert hashlib.sha256((ROOT/s['source']).read_bytes()).hexdigest()==s['source_sha256'];bpy.ops.wm.open_mainfile(filepath=str(ROOT/s['source']));bpy.context.scene.frame_set(1)
for row in s['form_panels']:
    o=bpy.data.objects[row['node']];o.animation_data_clear();o.location=Vector(row['pivot_blender'])+Vector(row['lift_blender']);o.rotation_quaternion=Quaternion(Vector(row['axis_blender']),row['angle'])
    if 'mechanism'in row:
        m=row['mechanism'];bpy.data.objects[m['carriage']].animation_data_clear();bpy.data.objects[m['rotor']].animation_data_clear();bpy.data.objects[m['carriage']].location=(0,0,m['stroke']);bpy.data.objects[m['rotor']].rotation_quaternion=Quaternion(Vector(m['axis_local_blender']),row['angle'])
bpy.context.view_layer.update();mount=bpy.data.objects['IC1_MouthMount'];inverse=mount.matrix_world.inverted()
moving=[bpy.data.objects[n]for n in ['IC1_SeamCrossBolt_-1','IC1_SeamCrossBolt_1','IC64_SeamSocket_-1','IC64_SeamSocket_1']];homes={o.name:o.matrix_local.copy()for o in moving}
def geometry(o):
    e=o.evaluated_get(bpy.context.evaluated_depsgraph_get());m=e.to_mesh();m.calc_loop_triangles();v=[e.matrix_world@x.co for x in m.vertices];f=[tuple(t.vertices)for t in m.loop_triangles];e.to_mesh_clear()
    return BVHTree.FromPolygons(v,f,all_triangles=True),v,Vector(min(p[k]for p in v)for k in range(3)),Vector(max(p[k]for p in v)for k in range(3))
fixed=[o for root in [bpy.data.objects['IN1_BodyRoot'],bpy.data.objects['IAM_MODULE']]for o in root.children_recursive if o.type=='MESH'and o not in moving]
fixed=list(dict.fromkeys(fixed));fixed_trees={o.name:geometry(o)for o in fixed};samples=[];contacts=[];seatings=[]
cap_sides={r['sign']:r.get('cap_side',-1)for r in s['seam_fasteners']['pairs']}
def overlap(a,b):
    if any(a[3][k]<b[2][k]or b[3][k]<a[2][k]for k in range(3)):return []
    return a[0].overlap(b[0])
for phase in ['socket','stud']:
    for amount in [0.,.023,.047,.079,.13,.19,.27,.38,.52,.69,.83,1.]:
        for row in s['seam_fasteners']['pairs']:
            sign=row['sign'];center=Vector(row['center_parent']);cap=bpy.data.objects['IC64_SeamSocket_'+str(sign)];pin=bpy.data.objects['IC1_SeamCrossBolt_'+str(sign)]
            dy=cap_sides[sign]*.014*(amount if phase=='socket'else 1.);angle=-math.tau*dy/row['thread_pitch']
            cap.matrix_local=Matrix.Translation(Vector((0,dy,0)))@Matrix.Translation(center)@Matrix.Rotation(angle,4,'Y')@Matrix.Translation(-center)@homes[cap.name]
            pin.matrix_local=Matrix.Translation(Vector((0,-cap_sides[sign]*.15*amount if phase=='stud'else 0.,0)))@homes[pin.name]
        bpy.context.view_layer.update();trees={o.name:geometry(o)for o in moving};row_contacts=[]
        for i,o in enumerate(moving):
            a=trees[o.name];sign=-1 if o.name.endswith('_-1')else 1
            for name,b in fixed_trees.items():
                hits=overlap(a,b)
                if not hits:continue
                is_cap=o.name.startswith('IC64_');side=cap_sides[sign]if is_cap else -cap_sides[sign]
                washer='IC1_SeamWasher_%s_%s'%(sign,side)
                if name==washer:
                    pa=[inverse@v for v in a[1]];pb=[inverse@v for v in b[1]]
                    head=pa if is_cap else [v for v in pa if math.hypot(v.x-sign*.601,v.z-.590)>.00565]
                    depth=max(v.y for v in head)-min(v.y for v in pb)if side<0 else max(v.y for v in pb)-min(v.y for v in head)
                    if depth<5e-7:
                        seatings.append({'phase':phase,'amount':amount,'a':o.name,'washer':washer,'plane_numerical_overlap':max(0.,depth),'pairs':len(hits)});continue
                row_contacts.append({'a':o.name,'b':name,'pairs':len(hits)})
            for other in moving[i+1:]:
                hits=overlap(a,trees[other.name])
                if hits:row_contacts.append({'a':o.name,'b':other.name,'pairs':len(hits)})
        samples.append({'phase':phase,'amount':amount,'contacts':row_contacts});contacts.extend({'phase':phase,'amount':amount,**r}for r in row_contacts);print('R64_RELEASE',phase,amount,row_contacts,flush=True)
result={'source_sha256':s['source_sha256'],'passed':not contacts,'contacts':contacts,'seating_contacts':seatings,'samples':samples,'scope':'24 sampled threaded cap/stud withdrawal states against full current source body and mouth. Only named washer planar seating accepted within 5e-7 parent-space numerical overlap; no other exclusions. Not continuous collision, clamp opening, source-shader deformation or final visual acceptance.'}
(OUT/'release_check.json').write_text(json.dumps(result,indent=2)+'\n');print('R64_RELEASE_RESULT',result['passed'],flush=True)
