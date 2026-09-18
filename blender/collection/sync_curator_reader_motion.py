"""Apply a constant reader-height correction to the existing baked source.

The correction is derived from a newly recorded runtime take. Every other
object/action is preserved; the full source is backed up before saving.
"""
import bpy,json,hashlib,shutil
from pathlib import Path
from mathutils import Matrix,Vector,Quaternion
ROOT=Path(__file__).resolve().parents[2]
C=Matrix(((1,0,0,0),(0,0,1,0),(0,-1,0,0),(0,0,0,1)));CI=C.inverted()
take=json.loads((ROOT/'review/G_optical_curator/curator_take.json').read_text())
for ext,key in [('glb','model_sha256'),('json','metadata_sha256')]:assert hashlib.sha256((ROOT/f'app/assets/collection/models/G_optical_curator.{ext}').read_bytes()).hexdigest()==take[key],'Stale runtime take'
source=ROOT/'blender/collection/G_optical_curator.blend'
bpy.ops.wm.open_mainfile(filepath=str(source));scene=bpy.context.scene;node=bpy.data.objects['GR_Tonearm']
def pose(p):return CI@Matrix.LocRotScale(Vector(p['p']),Quaternion((p['q'][3],*p['q'][:3])),Vector(p['s']))@C
delta=None
for sample in take['samples'][::61]+[take['samples'][-1]]:
    scene.frame_set(sample['frame']);expected=pose(sample['poses']['GR_Tonearm']);difference=expected.translation-node.matrix_basis.translation
    if delta is None:delta=difference
    assert (difference-delta).length<.00001,'Reader update is not a constant origin correction'
    assert max(abs(expected[i][j]-node.matrix_basis[i][j]) for i in range(3) for j in range(3))<.00001,'Reader orientation changed'
assert abs(delta.x)<.000001 and abs(delta.y)<.000001 and abs(delta.z)<.03,'Unexpected reader offset'
backup=ROOT/'blender/collection/checkpoints'/('G_optical_curator-before-reader-'+hashlib.sha256(source.read_bytes()).hexdigest()[:12]+'.blend')
backup.parent.mkdir(exist_ok=True)
if not backup.exists():shutil.copy2(source,backup)
action=node.animation_data.action;assert len(action.slots)==1,'Shared custom action needs a dedicated update'
changed=0
for layer in action.layers:
    for strip in layer.strips:
        for bag in strip.channelbags:
            for curve in bag.fcurves:
                if curve.data_path=='location' and curve.array_index==2:
                    for key in curve.keyframe_points:key.co.y+=delta.z;key.handle_left.y+=delta.z;key.handle_right.y+=delta.z;changed+=1
assert changed>0,'No recorded reader height channel'
scene.frame_set(1);bpy.ops.wm.save_as_mainfile(filepath=str(source))
report={'reader_height_delta':delta.z,'keyframes_updated':changed,'other_actions_preserved':True,'backup':str(backup.relative_to(ROOT)),'model_sha256':take['model_sha256'],'metadata_sha256':take['metadata_sha256']}
(ROOT/'review/G_optical_curator/operating/reader_source_sync.json').write_text(json.dumps(report,indent=2)+'\n');print('CURATOR_READER_SOURCE_SYNC',json.dumps(report),flush=True)
