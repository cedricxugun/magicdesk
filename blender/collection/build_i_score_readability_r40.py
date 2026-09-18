"""Enlarge the centered real grand staff without moving its axis or hardware."""
import bpy,json,hashlib,struct,sys
from pathlib import Path
REFINED='--refined'in sys.argv;ROOT=Path(__file__).resolve().parents[2];OUT=ROOT/'review/I_refinement/nautilus_r1/light_score_r40/score';ART=ROOT/'app/assets/collection/art/I/light_score_r40/score'
if REFINED:OUT=OUT.parent/'score_refined';ART=ART.parent/'score_refined'
for p in [OUT,ART]:p.mkdir(parents=True,exist_ok=True)
s=json.loads((ROOT/'app/assets/collection/art/I/moonlight_candidate/oblique_score_r34/layout.json').read_text());sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();assert sha(ROOT/s['source'])==s['source_sha256'];bpy.ops.wm.open_mainfile(filepath=str(ROOT/s['source']));bpy.context.scene.frame_set(1);bpy.context.view_layer.update()
allowed={'I_MoonlightStaff','I_CentralReadingLine'}
def fingerprint(o):
 h=hashlib.sha256()
 for v in o.data.vertices:h.update(struct.pack('<3f',*v.co))
 for f in o.data.polygons:h.update(struct.pack('<'+'I'*len(f.vertices),*f.vertices))
 return [h.hexdigest(),[list(r)for r in o.matrix_world]]
protected={o.name:fingerprint(o)for o in bpy.data.objects if o.type=='MESH'and o.name not in allowed}
for name in allowed:
 o=bpy.data.objects[name]
 for v in o.data.vertices:
  v.co.y*=.72/s['height']
  if REFINED and name=='I_MoonlightStaff':v.co.x*=1.20/s['width']
 o.data.update()
assert all(fingerprint(bpy.data.objects[n])==value for n,value in protected.items())
source=ROOT/('blender/collection/I_score_readability_r40b.blend'if REFINED else 'blender/collection/I_score_readability_r40.blend');component=ART/'optics.glb';assert not source.exists();bpy.ops.wm.save_as_mainfile(filepath=str(source),compress=True);root=bpy.data.objects['I_MusicOptics'];bpy.ops.object.select_all(action='DESELECT')
for o in [root,*root.children_recursive]:o.select_set(True)
bpy.context.view_layer.objects.active=root;bpy.ops.export_scene.gltf(filepath=str(component),export_format='GLB',use_selection=True,export_animations=False,export_morph=False,export_extras=True)
d={**s,'source':str(source.relative_to(ROOT)),'source_sha256':sha(source),'component':str(component.relative_to(ROOT)),'component_sha256':sha(component),'parent_source_sha256':s['source_sha256'],'height':.72,'width':1.20 if REFINED else s['width'],'optical_backing':.88,'correct_alpha':True,'score_gain':1.35,'scan_gain':1.25,'scanner':{**s['scanner'],'line_end':[0,-.36,s['scanner']['focus'][2]]},'scope':'Centered grand staff increased vertically from .50 to .72 at unchanged width, depth and scanner focus. Projector hardware, tine endpoints and connecting rays preserved; real source engraving unchanged. New opacity compositing and subdued backing require visual review.'};(ART/'layout.json').write_text(json.dumps(d,indent=2)+'\n');(OUT/'build.json').write_text(json.dumps(d,indent=2)+'\n');(OUT/'protected_hardware.json').write_text(json.dumps({'passed':True,'source_sha256':d['source_sha256'],'protected_mesh_count':len(protected),'scope':'All meshes except staff and scan-line vertical size preserved exactly. No full aperture/pose or visual acceptance.'},indent=2)+'\n');print('R40_SCORE',d['source_sha256'],flush=True)
