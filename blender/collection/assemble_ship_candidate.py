"""Assemble isolated G2 geometry/PBR review; no main assets or animated sources overwritten."""
import bpy,json,sys,hashlib
from pathlib import Path
from mathutils import Matrix,Vector
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(Path(__file__).parent))
from geometry import C,pose
from optimize_runtime_meshes import optimize
models=ROOT/'app/assets/collection/models';components=ROOT/'app/assets/collection/components'
revision='r3' if '--r3' in sys.argv else 'r2'
author=json.loads((components/('G_ship_'+revision+'.json')).read_text());source=ROOT/author['source_blend']
bpy.ops.wm.open_mainfile(filepath=str(source));bpy.context.scene.frame_set(1)
rig_names=[author['rig']['pitch'],author['rig']['roll']]+author['rig']['sails']+author['rig']['waves']+author['rig']['cams']
if revision=='r3':rig_names += [author['rig']['shaft'],author['rig']['pinion']]+author['rig']['rockers']+author['rig']['rollers']+author['rig']['rods']
sheets=[]
carrier=bpy.data.objects[author['rig']['roll']]
for name in author['rig']['sails']:
    sail=bpy.data.objects[name];rope=bpy.data.objects[sail['sheet_name']]
    end=carrier.matrix_world.inverted()@rope.matrix_world@Vector(rope.data.splines[0].points[-1].co[:3])
    sheets.append({'node':rope.name,'sail':name,'side':float(sail['side']),'length':float(sail['length']),'winch_x':float(end.x-.008),'winch_y':float(end.y),'winch_lift':float(end.z-.189)})
guides=[]
for obj in bpy.data.objects[author['root']].children_recursive:
    if obj.type!='CURVE' or not any(k in obj.name for k in ['Gunwale','InternalHullRib','KeelSpine','RibbonRolledEdge','SailSewnEdge','FixedPitchFork']):continue
    points=[]
    for spline in obj.data.splines:
        points.extend(list((C@(obj.matrix_basis@Vector(p.co[:3])).to_4d()).xyz) for p in spline.points)
    if len(points)>1:guides.append({'node':obj.parent.name,'points':points,'source_curve':obj.name,'radius':float(obj.data.bevel_depth)})
data=json.loads((models/'G_optical_curator.json').read_text());main_before=hashlib.sha256((models/'G_optical_curator.glb').read_bytes()).hexdigest()
bpy.ops.wm.read_factory_settings(use_empty=True);bpy.ops.import_scene.gltf(filepath=str(models/'G_optical_curator.glb'))
old=bpy.data.objects[data['g_archive']['contents'][2]['root']];parent=old.parent
for obj in list(old.children_recursive)+[old]:bpy.data.objects.remove(obj,do_unlink=True)
before=set(bpy.data.objects);bpy.ops.import_scene.gltf(filepath=str(components/('G_ship_'+revision+'.glb')));added=set(bpy.data.objects)-before
root=bpy.data.objects[author['root']];root.parent=parent;root.matrix_basis=Matrix.Translation((0,0,author['mount_offset_z']))
keep={root,*root.children_recursive}
for obj in added-keep:bpy.data.objects.remove(obj,do_unlink=True)
carrier=bpy.data.objects[author['rig']['roll']]
fittings=bpy.data.objects.new('GS2_HullFittings',None);bpy.context.scene.collection.objects.link(fittings);fittings.parent=carrier
for obj in list(carrier.children):
    if obj.type=='MESH' and any(k in obj.name for k in ['Porthole','CaptiveBolt','BoltSlot']):
        matrix=obj.matrix_basis.copy();obj.parent=fittings;obj.matrix_basis=matrix
rig=[{'name':name,'kind':'ship_kinematic','home':pose(bpy.data.objects[name].matrix_basis)} for name in rig_names]
entry={'id':2,'title':'潮汐帆船','parameter':'调整风帆','action':'起航','root':root.name,'source_blend':author['source_blend'],'rig':rig,'structure_edges':[],
    'ship':{'rig':author['rig'],'guides':guides,'mount_offset_y':author['mount_offset_z'],'source_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),'sheets':sheets,'fittings_node':fittings.name,'wave_drive_version':author.get('wave_drive_version',2),'springs':author.get('springs',[])},
    'review_scope':'Isolated ship mechanism/PBR and authored fabrication candidate; full source take and native review pending'}
data['g_archive']['contents'][2]=entry
# No claim that a complete editable candidate source has been created.
data['source_blend']='blender/collection/G_ship_runtime_candidate.blend'
data['development_status']='Isolated G2 mechanism/PBR review; authored formation integrated, full source bake/native review pending; do not promote'
path=models/'G_optical_curator_ship_candidate.glb';path.with_suffix('.json').write_text(json.dumps(data,separators=(',',':'))+'\n')
assert not any(o.name.startswith('BASE_FIXED') for o in bpy.data.objects)
bpy.ops.object.select_all(action='SELECT');bpy.ops.export_scene.gltf(filepath=str(path),export_format='GLB',use_selection=True,export_apply=True,export_animations=False)
optimize(path,[s['node'] for s in sheets]+[s['node'] for s in author.get('springs',[])])
assert hashlib.sha256((models/'G_optical_curator.glb').read_bytes()).hexdigest()==main_before
print('SHIP_CANDIDATE',json.dumps({'guides':len(guides),'scope':entry['review_scope'],'main_unchanged':True}),flush=True)
