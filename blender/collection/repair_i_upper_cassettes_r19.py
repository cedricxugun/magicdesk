"""Repair the known liner fit and actual render fins in the built three-cassette source."""
import bpy,json,hashlib,sys,shutil,struct
from pathlib import Path
from mathutils import Vector
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(Path(__file__).parent));import i_machined_geometry as h;import i_render_triangle_cleanup as tri
OUT=ROOT/'review/I_refinement/nautilus_r1/upper_cassettes_r19';s=json.loads((OUT/'build.json').read_text());source=ROOT/s['source'];component=ROOT/s['component'];sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();assert sha(source)==s['source_sha256'];before=s['source_sha256']
archive=OUT/'iterations'/before[:12];archive.mkdir(parents=True,exist_ok=True)
for p in OUT.glob('*.json'):shutil.copy2(p,archive/p.name)
if (OUT/'views').exists():shutil.copytree(OUT/'views',archive/'views',dirs_exist_ok=True)
backup=source.parent/'checkpoints'/('I-three-cassettes-'+before[:12]+'.blend');shutil.copy2(source,backup)
bpy.ops.wm.open_mainfile(filepath=str(source));bpy.context.scene.frame_set(1);bpy.context.view_layer.update();allowed={r['name'] for r in s['new_cassette_solids']}|set(s['cassette_source_skins'])
def fingerprint(o):
    d=hashlib.sha256()
    for v in o.data.vertices:d.update(struct.pack('<3f',*v.co))
    for f in o.data.polygons:d.update(struct.pack('<'+'I'*len(f.vertices),*f.vertices))
    return [d.hexdigest(),[list(r) for r in o.matrix_world]]
protected={o.name:fingerprint(o) for o in bpy.data.objects if o.type=='MESH' and o.name not in allowed};col=bpy.data.collections.new('I_R19_FIT_REPAIR');bpy.context.scene.collection.children.link(col);h.configure(col)
liner=bpy.data.objects['IN2_Cassette05BodyBolt1BoreLiner'];metal=bpy.data.objects['IN2_Cassette05BackBlock'];frame=bpy.data.objects['IN2_Cassette05_Frame'];axis=(liner.matrix_world.to_3x3()@Vector((0,0,1))).normalized();center=liner.matrix_world.translation.copy();positions=[(liner.matrix_world@v.co).dot(axis) for v in liner.data.vertices];depth=max(positions)-min(positions);local=frame.matrix_world.inverted()@center;local_axis=frame.matrix_world.to_3x3().inverted()@axis;h.drill(metal,.0038,depth+.002,frame,local,local_axis)
# Recut only this source skin with the closed-manifold solver. Its exact-solver
# result had a pinched render edge beyond the opposed duplicate triangles.
skin=bpy.data.objects['IN1_FixedRearShell_05'];parent=json.loads((ROOT/'review/I_refinement/nautilus_r1/trunnion_support_r18/build.json').read_text());assert parent['source_sha256']==s['parent_source_sha256']==sha(ROOT/parent['source'])
with bpy.data.libraries.load(str(ROOT/parent['source']),link=False) as (src,dst):dst.objects=['IN1_FixedRearShell_05']
original=dst.objects[0];skin.data=original.data.copy();skin.data.materials.clear()
for material_name in s['cassette_source_skins'][skin.name][3]:skin.data.materials.append(bpy.data.materials[material_name])
bpy.data.objects.remove(original,do_unlink=True);tri.repair(skin,connected_fins=True)
mechanism=next(m for m in s['real_cassettes'] if m['panel_number']==5);matrix=frame.matrix_world;inverse=matrix.inverted()
for anchor in mechanism['anchors']:
    if anchor['source_mesh']!=skin.name:continue
    outer=inverse@Vector(anchor['outer']);inner=inverse@Vector(anchor['inner']);normal=matrix.to_3x3().inverted()@Vector(anchor['axis_world']);wall=anchor['original_thickness'];recess=anchor['bearing_recess']
    h.drill(skin,.0038,wall+.040,frame,(outer+inner)*.5,normal,solver='MANIFOLD')
    h.drill(skin,.0092,.016,frame,inner+normal*(recess-.008),normal,solver='MANIFOLD')
repairs=[]
for name in sorted(allowed):
    print('R19_TRIANGLE_REPAIR',name,flush=True)
    o=bpy.data.objects[name];r=tri.repair(o,connected_fins=True)
    if r['removed_opposed_triangles']:repairs.append({'mesh':name,**r})
assert all(fingerprint(bpy.data.objects[n])==f for n,f in protected.items())
bpy.ops.wm.save_as_mainfile(filepath=str(source),compress=True);body=bpy.data.objects['IN1_BodyRoot'];bpy.ops.object.select_all(action='DESELECT')
for o in [body,*body.children_recursive]:o.select_set(True)
bpy.context.view_layer.objects.active=body;bpy.ops.export_scene.gltf(filepath=str(component),export_format='GLB',use_selection=True,export_animations=False,export_morph=False,export_extras=True)
s['source_sha256']=sha(source);s['component_sha256']=sha(component);s['cassette_fit_repair']={'source_before':before,'saved_source':str(backup.relative_to(ROOT)),'liner':liner.name,'metal':metal.name,'relief_radius':.0038,'relief_depth':depth+.002,'recut_skin':skin.name,'recut_solver':'MANIFOLD','render_repairs':repairs,'other_meshes_preserved':len(protected)}
(OUT/'build.json').write_text(json.dumps(s,indent=2)+'\n');p=json.loads((OUT/'protected_geometry.json').read_text());p['source_sha256']=s['source_sha256'];p['post_build_repair']=True;(OUT/'protected_geometry.json').write_text(json.dumps(p,indent=2)+'\n');print('R19_REPAIRED',s['source_sha256'],[(r['mesh'],r['removed_opposed_triangles']) for r in repairs],flush=True)
