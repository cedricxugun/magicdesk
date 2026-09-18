"""Promote the proved render-triangle repair without experimental rim geometry."""
import bpy,json,hashlib,sys,struct
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(Path(__file__).parent));import i_render_triangle_cleanup as cleanup
parent=ROOT/'review/I_refinement/nautilus_r1/throat_terminations_r16/build.json';s=json.loads(parent.read_text());sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();assert sha(ROOT/s['source'])==s['source_sha256']=='f88bcfa5f6bb393ae1631da5ba5e74b485f4f9d1fe8e94807693eb5581e525c8'
out=parent.parent/'triangles';out.mkdir(parents=True,exist_ok=True);target=ROOT/'blender/collection/I_nautilus_termination_triangles_r16b.blend';component=ROOT/'app/assets/collection/components/I_nautilus_termination_triangles_r16b.glb';assert not target.exists(),'Preserve the recorded R16b source'
bpy.ops.wm.open_mainfile(filepath=str(ROOT/s['source']));bpy.context.scene.frame_set(1);bpy.context.view_layer.update()
def fingerprint(o):
    h=hashlib.sha256()
    for v in o.data.vertices:h.update(struct.pack('<3f',*v.co))
    for f in o.data.polygons:h.update(struct.pack('<'+'I'*len(f.vertices),*f.vertices))
    return [h.hexdigest(),[list(r) for r in o.matrix_world],o.parent.name if o.parent else None]
frame=bpy.data.objects['IN1_CellFrame_09'];protected={o.name:fingerprint(o) for o in bpy.data.objects if o.type=='MESH' and o!=frame};repair=cleanup.repair(frame);assert repair['removed_opposed_triangles']==4
assert all(fingerprint(bpy.data.objects[n])==value for n,value in protected.items())
bpy.ops.wm.save_as_mainfile(filepath=str(target),compress=True);body=bpy.data.objects['IN1_BodyRoot'];bpy.ops.object.select_all(action='DESELECT')
for o in [body,*body.children_recursive]:o.select_set(True)
bpy.context.view_layer.objects.active=body;bpy.ops.export_scene.gltf(filepath=str(component),export_format='GLB',use_selection=True,export_animations=False,export_morph=False,export_extras=True)
r={**s,'source':str(target.relative_to(ROOT)),'source_sha256':sha(target),'component':str(component.relative_to(ROOT)),'component_sha256':sha(component),'parent_source_sha256':s['source_sha256'],'render_triangle_repair':{'mesh':frame.name,'parent_report':str(parent.relative_to(ROOT)),**repair},'status':'closed_termination_render_triangle_fix','review_scope':'Only two proved opposed render-triangle pairs on frame09 removed; all other meshes and transforms preserved. R17 end-rim experiments are not included. Complete edge finish, chamber04, core/base support, upper mechanisms, final materials/music/native remain unfinished.'}
(out/'build.json').write_text(json.dumps(r,indent=2)+'\n');(out/'protected_geometry.json').write_text(json.dumps({'source_sha256':r['source_sha256'],'passed':True,'protected_mesh_count':len(protected),'changed_mesh':frame.name,'repair':repair},indent=2)+'\n');print('R16B_TRIANGLES_FIXED',r['source_sha256'],r['component_sha256'],flush=True)
