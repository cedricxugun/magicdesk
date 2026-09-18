"""Current cowl against evaluated original mouth at sampled source poses."""
import bpy,json,hashlib,sys
from pathlib import Path
from mathutils import Vector,Quaternion
from mathutils.bvhtree import BVHTree
ROOT=Path(__file__).resolve().parents[2];args=sys.argv[sys.argv.index('--')+1:]if '--'in sys.argv else [];report=ROOT/next((a.split('=',1)[1]for a in args if a.startswith('--report=')),'review/I_refinement/nautilus_r1/mouth_finish_r21/build.json');OUT=report.parent;s=json.loads(report.read_text())
assert hashlib.sha256((ROOT/s['source']).read_bytes()).hexdigest()==s['source_sha256']
bpy.ops.wm.open_mainfile(filepath=str(ROOT/s['source']));scene=bpy.context.scene
for r in s['form_panels']:
    bpy.data.objects[r['node']].animation_data_clear()
    if 'mechanism' in r:
        for k in ['carriage','rotor']:bpy.data.objects[r['mechanism'][k]].animation_data_clear()
mouth=[o for o in bpy.data.objects if o.type=='MESH' and o.name.startswith('IAM_')]
def geometry(objects):
    vertices=[];faces=[];owners=[];dg=bpy.context.evaluated_depsgraph_get()
    for o in objects:
        e=o.evaluated_get(dg);m=e.to_mesh();m.calc_loop_triangles();offset=len(vertices)
        vertices.extend(e.matrix_world@v.co for v in m.vertices)
        faces.extend(tuple(offset+i for i in t.vertices)for t in m.loop_triangles)
        owners.extend([o.name]*len(m.loop_triangles));e.to_mesh_clear()
    return BVHTree.FromPolygons(vertices,faces,all_triangles=True),vertices,faces,owners
def covers(p):
    for r in s['form_panels']:
        f=r['lift_fraction'];clear=min(1.,p/max(f,1e-6));turn=max(0.,(p-f)/max(1-f,1e-6));o=bpy.data.objects[r['node']]
        o.location=Vector(r['pivot_blender'])+Vector(r['lift_blender'])*clear;o.rotation_quaternion=Quaternion(Vector(r['axis_blender']),r['angle']*turn)
        if 'mechanism'in r:
            m=r['mechanism'];bpy.data.objects[m['carriage']].location=(0,0,m['stroke']*clear);bpy.data.objects[m['rotor']].rotation_quaternion=Quaternion(Vector(m['axis_local_blender']),r['angle']*turn)
    bpy.context.view_layer.update()
targets=[a.split('=',1)[1]for a in args if a.startswith('--mesh=')] or s['cowl_finish']['modified_meshes']
contacts=[];witnesses=[]
for frame in [1,31,61,91,121,151,181]:
    scene.frame_set(frame);bpy.context.view_layer.update();tree,vertices,faces,owners=geometry(mouth)
    witness=hashlib.sha256()
    for p in vertices[::101]:witness.update((','.join('%.7f'%v for v in p)).encode())
    witnesses.append({'source_frame':frame,'evaluated_geometry_hash':witness.hexdigest()})
    for opening in [0.,1.]:
        covers(opening)
        for name in targets:
            c,cv,cf,_=geometry([bpy.data.objects[name]]);hits=c.overlap(tree);groups={}
            for i,j in hits:groups[owners[j]]=groups.get(owners[j],0)+1
            for other,count in groups.items():contacts.append({'source_frame':frame,'cover_opening':opening,'cowl':name,'mouth_part':other,'triangle_pairs':count})
    print('COWL_MOUTH_FRAME',frame,len(contacts),flush=True)
changed=len({r['evaluated_geometry_hash']for r in witnesses})>1
result={'source_sha256':s['source_sha256'],'passed':not contacts and changed,'contacts':contacts,'modified_meshes':targets,'mouth_motion_observed':changed,'witnesses':witnesses,'scope':'Seven evaluated Blender A poses against the explicitly listed modified cowl meshes with covers closed and open. Source motion is witnessed. No runtime shader deformation, continuous collision, other fixed-part containment or final visual acceptance.'}
(OUT/'mouth_clearance.json').write_text(json.dumps(result,indent=2)+'\n');print('COWL_MOUTH_RESULT',json.dumps(contacts),flush=True)
