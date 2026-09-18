"""Independent evaluated suspension range and connection checks, with raw contacts."""
import bpy,bmesh,json,hashlib
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree
ROOT=Path(__file__).resolve().parents[2];OUT=ROOT/'review/I_refinement/part_a_mouth/shutter_r2/diaphragm'
spec=json.loads((OUT/'build.json').read_text());source=ROOT/spec['source'];assert hashlib.sha256(source.read_bytes()).hexdigest()==spec['source_sha256']
bpy.ops.wm.open_mainfile(filepath=str(source));scene=bpy.context.scene;scene.frame_set(1);moving=bpy.data.objects[spec['diaphragm']['moving']];moving.animation_data_clear()
# Keep the translation driver but remove only the keyframed source action.
moving.driver_add('location',2)
d=moving.animation_data.drivers.find('location',index=2).driver;d.type='SCRIPTED'
v=d.variables.new();v.name='s';v.type='SINGLE_PROP';v.targets[0].id=moving;v.targets[0].data_path='["stroke"]';d.expression='s'
deps=bpy.context.evaluated_depsgraph_get();meshes=[o for o in bpy.data.objects if o.type=='MESH']
dynamic={o.name for o in moving.children_recursive if o.type=='MESH'}|set(spec['diaphragm']['morphs'])
def data(o):
    e=o.evaluated_get(deps);m=e.to_mesh();m.calc_loop_triangles();vertices=[e.matrix_world@v.co for v in m.vertices];triangles=[tuple(t.vertices) for t in m.loop_triangles];e.to_mesh_clear();return vertices,triangles
def tree(o):
    p,t=data(o);return BVHTree.FromPolygons(p,t,all_triangles=True)
bpy.context.view_layer.update();fixed=[(o.name,tree(o)) for o in meshes if o.name not in dynamic]
contacts=[];self_contacts=[];solids=[];connections=[]
for o in meshes:
    bm=bmesh.new();bm.from_mesh(o.data);bm.normal_update();solids.append({'name':o.name,'nonmanifold':sum(not e.is_manifold for e in bm.edges),'volume':bm.calc_volume(signed=True)});bm.free()
for value in [-.006,-.0045,-.003,-.0015,0.,.0015,.003,.0045,.006]:
    moving['stroke']=value;moving.update_tag();bpy.context.view_layer.update();assert abs(moving.location.z-value)<1e-6,('Stale suspension evaluation',value,moving.location.z)
    built={name:tree(bpy.data.objects[name]) for name in dynamic}
    for name,t in built.items():
        for other,ft in fixed:
            overlaps=t.overlap(ft)
            if overlaps:contacts.append({'stroke':value,'a':name,'b':other,'triangles':len(overlaps)})
        if name in spec['diaphragm']['morphs']:
            points,triangles=data(bpy.data.objects[name]);sets=[set(x) for x in triangles]
            pairs=[(a,b) for a,b in t.overlap(t) if a<b and not sets[a].intersection(sets[b])]
            if pairs:self_contacts.append({'stroke':value,'name':name,'count':len(pairs)})
    for row in spec['diaphragm']['connections']:
        points,_=data(bpy.data.objects[row['spring']]);front=bpy.data.objects[row['front_seat']];rear=bpy.data.objects[row['rear_seat']]
        front_surface=front.matrix_world.translation.z+.0075;rear_surface=rear.matrix_world.translation.z-.0075
        connections.append({'stroke':value,'index':row['index'],'front_gap':abs(min(p.z for p in points)-front_surface),'rear_gap':abs(max(p.z for p in points)-rear_surface)})
    print('DIAPHRAGM_CHECK',value,len(contacts),len(self_contacts),flush=True)
result={'source_sha256':spec['source_sha256'],'solids':solids,'contacts':contacts,'self_contacts':self_contacts,'connections':connections,'connections_passed':max(max(x['front_gap'],x['rear_gap']) for x in connections)<.0001,'scope':'Nine evaluated independent suspension amplitudes with closed tongues; all moving suspension meshes versus fixed scene, deforming self-surface checks and actual spring endpoint/cup gaps. Raw designed rim/interface contacts retained for classification. Not continuous collision or full-device acceptance.'}
(OUT/'suspension_check.json').write_text(json.dumps(result,indent=2)+'\n');print('I_DIAPHRAGM_CHECK_FINISHED',flush=True)
