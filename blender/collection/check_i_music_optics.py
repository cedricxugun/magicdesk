"""Check independent optical hardware against current mouth, including open/close."""
import bpy,bmesh,json,hashlib,sys
from pathlib import Path
from mathutils.bvhtree import BVHTree
ROOT=Path(__file__).resolve().parents[2];OUT=ROOT/'review/I_refinement/moonlight/current_mouth'
args=sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else []
custom_optics=next((a.split('=',1)[1] for a in args if a.startswith('--optics-report=')),None)
args=[a for a in args if not a.startswith('--optics-report=')]
if custom_optics:OUT=(ROOT/custom_optics).parent
opt=json.loads((OUT/'build.json').read_text())
base_report=ROOT/(args[0] if args else 'review/I_refinement/part_a_mouth/shutter_r2/diaphragm/build.json')
base=json.loads(base_report.read_text());source=ROOT/base['source'];assert hashlib.sha256(source.read_bytes()).hexdigest()==base['source_sha256']
assert hashlib.sha256((ROOT/opt['source']).read_bytes()).hexdigest()==opt['source_sha256']
assert hashlib.sha256((ROOT/opt['component']).read_bytes()).hexdigest()==opt['component_sha256']
if not args:assert base['source_sha256']==opt['mouth_source_sha256']
bpy.ops.wm.open_mainfile(filepath=str(source));scene=bpy.context.scene;scene.frame_set(1);mouth=bpy.data.objects['IAM_Mouth'];existing=[o for o in bpy.data.objects if o.type=='MESH']
with bpy.data.libraries.load(str(ROOT/opt['source']),link=False) as (src,dst):dst.objects=[n for n in src.objects if n.startswith('I_')]
loaded=[o for o in dst.objects if o is not None]
for o in loaded:bpy.context.collection.objects.link(o)
root=next(o for o in loaded if o.name=='I_MusicOptics');root.parent=mouth
nonphysical=[opt['sheet']]
if 'scanner' in opt:nonphysical+=[opt['scanner']['line']]+[t['ray'] for t in opt['scanner']['tips']]
hardware=[o for o in loaded if o.type=='MESH' and o.name not in nonphysical];solids=[]
for o in hardware:
 bm=bmesh.new();bm.from_mesh(o.data);bm.normal_update();solids.append({'name':o.name,'nonmanifold':sum(not e.is_manifold for e in bm.edges),'volume':bm.calc_volume(signed=True)});bm.free()
deps=bpy.context.evaluated_depsgraph_get()
def geometry(o):
 e=o.evaluated_get(deps);m=e.to_mesh();m.calc_loop_triangles();v=[e.matrix_world@x.co for x in m.vertices];tri=[tuple(x.vertices) for x in m.loop_triangles];e.to_mesh_clear();return BVHTree.FromPolygons(v,tri,all_triangles=True),[min(p[i] for p in v) for i in range(3)],[max(p[i] for p in v) for i in range(3)]
bpy.context.view_layer.update();built=[(o.name,*geometry(o)) for o in hardware];contacts=[]
for frame in ([1,55,109,163,217,271,325,379,433] if custom_optics else [1,45,65,85,105,125,145,165,181]):
 scene.frame_set(frame);bpy.context.view_layer.update()
 for obj in existing:
  tree,lo,hi=geometry(obj)
  for name,t,a,b in built:
   if any(hi[i]<a[i] or b[i]<lo[i] for i in range(3)):continue
   overlaps=t.overlap(tree)
   if overlaps:contacts.append({'frame':frame,'optic':name,'mouth':obj.name,'triangles':len(overlaps)})
 print('MUSIC_OPTICS_CONTACT',frame,len(contacts),flush=True)
unexpected=[r for r in contacts if not (r['optic'] in ['I_StaffProjectorMountPinL','I_StaffProjectorMountPinR'] and r['mouth']=='IAM_IrisOuterCase_Fitted')]
passed=not unexpected and all(r['nonmanifold']==0 and r['volume']>0 for r in solids)
output=OUT/'mount_check.json' if custom_optics else base_report.with_name('optics_mount_check.json') if args else OUT/'mount_check.json'
output.write_text(json.dumps({'source_sha256':opt['source_sha256'],'optics_component_sha256':opt['component_sha256'],'mouth_source_sha256':base['source_sha256'],'mouth_component_sha256':base['component_sha256'],'passed':passed,'solids':solids,'contacts':contacts,'unexpected_contacts':unexpected,'scope':'Nine current source poses, physical slit-projector parts versus all mouth meshes. Mount pins seating into fitted liner are listed intentional contacts. Optical staff surface excluded as nonphysical; optical clipping/readability separately rendered. Not continuous collision or art acceptance.'},indent=2)+'\n')
print('I_MUSIC_OPTICS_MOUNT_CHECK',passed,flush=True)
