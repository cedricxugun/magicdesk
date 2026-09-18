"""Check the saved source animation against sampled runtime transforms."""
import bpy,json,hashlib
from pathlib import Path
from mathutils import Matrix,Vector,Quaternion
ROOT=Path(__file__).resolve().parents[2]
C=Matrix(((1,0,0,0),(0,0,1,0),(0,-1,0,0),(0,0,0,1)));CI=C.inverted()
take=json.loads((ROOT/'review/G_optical_curator/curator_take.json').read_text())
for ext,key in [('glb','model_sha256'),('json','metadata_sha256')]:assert hashlib.sha256((ROOT/f'app/assets/collection/models/G_optical_curator.{ext}').read_bytes()).hexdigest()==take[key]
bpy.ops.wm.open_mainfile(filepath=str(ROOT/'blender/collection/G_optical_curator.blend'))
def pose(p):return CI@Matrix.LocRotScale(Vector(p['p']),Quaternion((p['q'][3],*p['q'][:3])),Vector(p['s']))@C
max_position=0.;max_basis=0.;checked=0;missing=[]
for sample in take['samples'][::93]+[take['samples'][-1]]:
    bpy.context.scene.frame_set(sample['frame'])
    for name,p in sample['poses'].items():
        obj=bpy.data.objects.get(name)
        if not obj:missing.append(name);continue
        expected=pose(p);actual=obj.matrix_basis
        max_position=max(max_position,(expected.translation-actual.translation).length)
        max_basis=max(max_basis,max(abs(expected[i][j]-actual[i][j]) for i in range(3) for j in range(3)));checked+=1
missing_textures=[]
for image in bpy.data.images:
    if image.source=='FILE' and not image.packed_file and image.filepath and not Path(bpy.path.abspath(image.filepath)).exists():missing_textures.append(image.filepath)
report={'passed':not missing and not missing_textures and max_position<.00001 and max_basis<.00001,'sampled_transforms':checked,'max_position_error':max_position,'max_basis_error':max_basis,'missing_nodes':sorted(set(missing)),'missing_textures':missing_textures,'model_sha256':take['model_sha256'],'metadata_sha256':take['metadata_sha256']}
(ROOT/'review/G_optical_curator/source_animation_report.json').write_text(json.dumps(report,indent=2));print('CURATOR_SOURCE_ANIMATION',json.dumps(report),flush=True)
assert report['passed'],'Saved source differs from runtime take'
scene=bpy.context.scene;scene.frame_set(next(s['frame'] for s in take['samples'] if s['explosion']>.999))
scene.render.resolution_x=1280;scene.render.resolution_y=1000;scene.render.resolution_percentage=100;scene.cycles.samples=24
scene.render.filepath=str(ROOT/'review/G_optical_curator/source_service.png');bpy.ops.render.render(write_still=True)
