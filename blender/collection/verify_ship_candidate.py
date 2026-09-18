"""Check the saved source animation against sampled runtime transforms."""
import bpy,json,hashlib,math,sys
from pathlib import Path
from mathutils import Matrix,Vector,Quaternion
ROOT=Path(__file__).resolve().parents[2]
C=Matrix(((1,0,0,0),(0,0,1,0),(0,-1,0,0),(0,0,0,1)));CI=C.inverted()
revision='r3' if '--r3' in sys.argv else 'r2'
review=ROOT/('review/G_optical_curator/ship_'+revision+'/full_take')
take=json.loads((review/'curator_take.json').read_text())
for ext,key in [('glb','model_sha256'),('json','metadata_sha256')]:assert hashlib.sha256((ROOT/f'app/assets/collection/models/G_optical_curator_ship_candidate.{ext}').read_bytes()).hexdigest()==take[key]
bpy.ops.wm.open_mainfile(filepath=str(ROOT/'blender/collection/G_ship_runtime_candidate.blend'))
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
widget_position=0.;widget_basis=0.;widget_samples=0
for sample in take['samples'][::93]+[take['samples'][-1]]:
    bpy.context.scene.frame_set(sample['frame'])
    for widget in sample['widgets']:
        name='GCTRL_'+('slider_x' if widget['gesture']=='slider' else widget['gesture']);root=bpy.data.objects[name]
        targets=[(root.matrix_world,pose(widget['pose']))]
        children={child.name.replace('.','_'):child for child in root.children}
        targets.extend((children[name].matrix_basis,pose(p)) for name,p in zip(widget['moving_names'],widget['moving']))
        for actual,expected in targets:
            widget_position=max(widget_position,(expected.translation-actual.translation).length);widget_basis=max(widget_basis,max(abs(expected[i][j]-actual[i][j]) for i in range(3) for j in range(3)));widget_samples+=1
assert widget_position<.00001 and widget_basis<.00001,(widget_position,widget_basis)
rope_error=0.;rope_samples=0
for sample in take['samples'][::93]+[take['samples'][-1]]:
    bpy.context.scene.frame_set(sample['frame'])
    for name,item in {**sample.get('ship_ropes',{}),**sample.get('ship_springs',{})}.items():
        obj=bpy.data.objects[name]
        assert len(obj.data.splines[0].points)==len(item['points'])
        for point,p in zip(obj.data.splines[0].points,item['points']):
            expected=Vector((p[0],-p[2],p[1]));rope_error=max(rope_error,(point.co.xyz-expected).length);rope_samples+=1
assert rope_error<1e-5,rope_error
missing_textures=[]
for image in bpy.data.images:
    if image.source=='FILE' and not image.packed_file and image.filepath and not Path(bpy.path.abspath(image.filepath)).exists():missing_textures.append(image.filepath)
report={'passed':not missing and not missing_textures and max_position<.00001 and max_basis<.00001,'sampled_transforms':checked,'max_position_error':max_position,'max_basis_error':max_basis,'missing_nodes':sorted(set(missing)),'missing_textures':missing_textures,'model_sha256':take['model_sha256'],'metadata_sha256':take['metadata_sha256']}
(review/'source_animation_report.json').write_text(json.dumps(report,indent=2));print('CURATOR_SOURCE_ANIMATION',json.dumps(report),flush=True)
assert report['passed'],'Saved source differs from runtime take'
fields=[]
active_g1=bpy.data.objects['GB2_Butterfly']
used_g1={slot.material for obj in active_g1.children_recursive for slot in obj.material_slots if slot.material}
for mat in used_g1:
    if not mat.name.startswith('CandidateFormation_1_'):continue
    textures=[n for n in mat.node_tree.nodes if n.type=='TEX_IMAGE' and n.image and 'butterfly_' in n.image.name and '_seal' in n.image.name]
    if textures:
        coords=[n.object.name for n in mat.node_tree.nodes if n.type=='TEX_COORD' and n.object and n.object.name.startswith('GB2_Wing')]
        fields.append({'material':mat.name,'field':textures[-1].image.name,'coordinates':coords})
assert len(fields)==8,fields
report['ship_ropes']={'samples':rope_samples,'max_point_error':rope_error}
report['widgets']={'samples':widget_samples,'max_position_error':widget_position,'max_basis_error':widget_basis};report['butterfly_panel_materials']=fields;report['source_sha256']=hashlib.sha256((ROOT/'blender/collection/G_ship_runtime_candidate.blend').read_bytes()).hexdigest()
(review/'source_animation_report.json').write_text(json.dumps(report,indent=2)+'\n')
ship_materials={slot.material for obj in bpy.data.objects['GS2_Ship'].children_recursive for slot in obj.material_slots if slot.material and slot.material.name.startswith('ShipFormation_')}
report['ship_material_fields']={kind:len([m for m in ship_materials if m.get('ship_material_kind')==kind]) for kind in ['hull','sail','metal']}
assert report['ship_material_fields']['hull']>0 and report['ship_material_fields']['sail']>=2
(review/'source_animation_report.json').write_text(json.dumps(report,indent=2)+'\n')
if '--verify-only' in sys.argv:raise SystemExit(0)
scene=bpy.context.scene;scene.render.resolution_x=1400;scene.render.resolution_y=1050;scene.render.resolution_percentage=100;scene.cycles.samples=32
camera=scene.camera;camera.data.type='PERSP';camera.data.sensor_fit='VERTICAL';camera.data.sensor_height=32;camera.data.lens=32/(2*math.tan(math.radians(43)*.5))
frames=[('source_hull_seal',next(s['frame'] for s in take['samples'] if s['state']['loaded_index']==2 and s['state']['stage']=='printing' and s['state']['print_amount']>.42)),('source_weave',next(s['frame'] for s in take['samples'] if s['state']['loaded_index']==2 and s['state']['stage']=='printing' and s['state']['print_amount']>.78)),('source_play',next(s['frame'] for s in take['samples'] if s['state']['loaded_index']==2 and s['state']['stage']=='playing'))]
for name,frame in frames:
    scene.frame_set(frame);target=bpy.data.objects['GR_PrintRoot'].matrix_world.translation+Vector((0,0,.52));camera.location=target+Vector((.16,-2.,.4));camera.rotation_euler=(target-camera.location).to_track_quat('-Z','Y').to_euler()
    scene.render.filepath=str(review/f'{name}.png');bpy.ops.render.render(write_still=True)
print('SHIP_SOURCE_VERIFIED',len(fields),'panel materials',flush=True)
