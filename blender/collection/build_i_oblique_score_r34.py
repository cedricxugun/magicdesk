"""A centered, larger score close to the real tine tips; keep emitter hardware."""
import bpy,json,hashlib,math,struct
from pathlib import Path
from mathutils import Vector
ROOT=Path(__file__).resolve().parents[2];OUT=ROOT/'review/I_refinement/moonlight/oblique_score_r34';OUT.mkdir(parents=True,exist_ok=True);ART=ROOT/'app/assets/collection/art/I/moonlight_candidate/oblique_score_r34';ART.mkdir(parents=True,exist_ok=True)
seed=json.loads((ROOT/'review/I_refinement/moonlight/central_scan_r1/build.json').read_text());sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();assert sha(ROOT/seed['source'])==seed['source_sha256'];bpy.ops.wm.open_mainfile(filepath=str(ROOT/seed['source']));bpy.context.scene.frame_set(1);bpy.context.view_layer.update()
allowed={'I_MoonlightStaff','I_CentralReadingLine',*[t['ray']for t in seed['scanner']['tips']]}
def fingerprint(o):
    h=hashlib.sha256()
    for v in o.data.vertices:h.update(struct.pack('<3f',*v.co))
    for p in o.data.polygons:h.update(struct.pack('<'+'I'*len(p.vertices),*p.vertices))
    return [h.hexdigest(),[list(r)for r in o.matrix_world]]
protected={o.name:fingerprint(o)for o in bpy.data.objects if o.type=='MESH'and o.name not in allowed}
width=1.42;height=.50;focus=Vector((0,0,-.352));sheet=bpy.data.objects['I_MoonlightStaff']
for v in sheet.data.vertices:
    u=.5-v.co.x/seed['width'];v.co.x=(.5-u)*width;v.co.y*=height/seed['height'];v.co.z=-.340-.008*math.sin(math.pi*u)
sheet.data.update()
line=bpy.data.objects[seed['scanner']['line']]
for v in line.data.vertices:v.co.y*=height/seed['height'];v.co.z=focus.z
line.data.update()
old_focus=Vector(seed['scanner']['focus'])
for tip in seed['scanner']['tips']:
    mesh=bpy.data.objects[tip['ray']];start=Vector(tip['mouth_point']);delta=old_focus-start
    for v in mesh.data.vertices:
        # Every authored two-vertex row shares its original axial coordinate.
        t=(v.co.z-start.z)/delta.z;center=start.lerp(old_focus,t);lateral=v.co-center;v.co=start.lerp(focus,t)+lateral
    mesh.data.update()
assert all(fingerprint(bpy.data.objects[n])==value for n,value in protected.items())
source=ROOT/'blender/collection/I_oblique_score_r34.blend';component=ART/'optics.glb';assert not source.exists(),'Archive existing candidate before rebuilding';bpy.ops.wm.save_as_mainfile(filepath=str(source),compress=True);bpy.ops.object.select_all(action='DESELECT');root=bpy.data.objects['I_MusicOptics']
for o in [root,*root.children_recursive]:o.select_set(True)
bpy.context.view_layer.objects.active=root;bpy.ops.export_scene.gltf(filepath=str(component),export_format='GLB',use_selection=True,export_animations=False,export_morph=False,export_extras=True)
d={**seed,'source':str(source.relative_to(ROOT)),'source_sha256':sha(source),'component':str(component.relative_to(ROOT)),'component_sha256':sha(component),'parent_source_sha256':seed['source_sha256'],'width':width,'height':height,'center_y':0.,'scan_gain':1.8,'score_gain':1.35,'filament_u_span':.14,'scanner':{**seed['scanner'],'focus':list(focus),'line_end':[0,-height/2,focus.z]},'scope':'Centered score close to existing physical tines for current oblique whole-body view. Sheet/scan strips only; projectors/arms/screws and measured tip endpoints preserved. Existing authored filament and real LilyPond score retained. Candidate source clearance/readability not acceptance.'}
(ART/'layout.json').write_text(json.dumps(d,indent=2)+'\n');(OUT/'build.json').write_text(json.dumps(d,indent=2)+'\n');(OUT/'protected_hardware.json').write_text(json.dumps({'source_sha256':d['source_sha256'],'passed':True,'protected_mesh_count':len(protected)},indent=2)+'\n')
whole=json.loads((ROOT/'review/I_refinement/nautilus_r1/uniform_precision_r29/build.json').read_text());whole['music_optics_layout']='res://'+str((ART/'layout.json').relative_to(ROOT/'app'));whole['optics_candidate_source_sha256']=d['source_sha256'];view=OUT/'whole_view';view.mkdir(parents=True,exist_ok=True);(view/'build.json').write_text(json.dumps(whole,indent=2)+'\n');print('OBLIQUE_SCORE_SOURCE',d['source_sha256'],flush=True)
