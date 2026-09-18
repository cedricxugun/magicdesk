"""Assemble a sibling comparison GLB; never overwrite the live registry/source."""
import bpy,json,sys,math
from pathlib import Path
from mathutils import Matrix
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(Path(__file__).parent))
from optimize_runtime_meshes import optimize
models=ROOT/'app/assets/collection/models';components=ROOT/'app/assets/collection/components'
data=json.loads((models/'G_optical_curator.json').read_text());entry=json.loads((components/'G_observatory_r2.json').read_text())
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=str(models/'G_optical_curator.glb'))
old=bpy.data.objects[data['g_archive']['contents'][0]['root']];parent=old.parent
for obj in list(old.children_recursive)+[old]:bpy.data.objects.remove(obj,do_unlink=True)
before=set(bpy.data.objects);bpy.ops.import_scene.gltf(filepath=str(components/'G_observatory_r2.glb'));added=set(bpy.data.objects)-before
root=next(o for o in added if o.name==entry['root']);root.parent=parent;offset=entry['mount_offset_y']
alignment=json.loads((ROOT/'production/G_optical_curator/observatory_r2/playback_alignment.json').read_text());yaw=alignment['mount_yaw'];entry['mount_yaw']=yaw
root.matrix_basis=Matrix.Translation((0,0,offset))@Matrix.Rotation(yaw,4,'Z')
keep={root,*root.children_recursive}
for obj in added-keep:bpy.data.objects.remove(obj,do_unlink=True)
# The renderer's fabrication paths are expressed in the platter print frame.
def mount(point):
    x,y,z=point;return [math.cos(yaw)*x+math.sin(yaw)*z,y+offset,-math.sin(yaw)*x+math.cos(yaw)*z]
entry['structure_edges']=[[mount(point) for point in edge] for edge in entry['structure_edges']]
for guide in entry['build_guides']:
    guide['points']=[mount(point) for point in guide['points']]
data['g_archive']['contents'][0]=entry
data['record_player']['design']='production/G_record_player/r3_fx/README.md'
data['record_player']['source_atlas']='res://assets/collection/art/G_AI/optical_field_atlas.png'
data['source_blend']='blender/collection/G_optical_curator_observatory_candidate.blend'
data['development_status']='Observatory comparison candidate; live registry unchanged, source animation not merged'
path=models/'G_optical_curator_observatory_candidate.glb'
path.with_suffix('.json').write_text(json.dumps(data,separators=(',',':')),encoding='utf-8')
assert not any(o.name.startswith('BASE_FIXED') for o in bpy.data.objects),'Candidate imported an extra pedestal'
bpy.ops.object.select_all(action='SELECT')
bpy.ops.export_scene.gltf(filepath=str(path),export_format='GLB',use_selection=True,export_apply=True,export_animations=False)
# prepare_observatory_source.py creates the editable candidate by copying the
# animated source, so rebuilding a runtime comparison cannot erase its tracks.
optimize(path)
print('OBSERVATORY_CANDIDATE_ASSEMBLED',flush=True)
