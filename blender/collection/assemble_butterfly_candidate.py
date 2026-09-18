"""Build an isolated G1 runtime candidate; leave live G and animated source alone."""
import bpy,json,sys,hashlib
from pathlib import Path
from mathutils import Matrix,Vector
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(Path(__file__).parent))
from geometry import C,pose
from optimize_runtime_meshes import optimize
models=ROOT/'app/assets/collection/models';components=ROOT/'app/assets/collection/components'
author=json.loads((components/'G_butterfly_r2.json').read_text())
source=ROOT/author['source_blend'];bpy.ops.wm.open_mainfile(filepath=str(source));bpy.context.scene.frame_set(120)
guides=[];spans={};deps=bpy.context.evaluated_depsgraph_get()
wing_names={r['wing']:r for r in author['rig']}
for name,r in wing_names.items():
    node=bpy.data.objects[name];inverse=node.matrix_world.inverted();span=0.
    for obj in node.children_recursive:
        if obj.type not in ['MESH','CURVE','FONT']:continue
        ev=obj.evaluated_get(deps);mesh=ev.to_mesh()
        span=max(span,max(abs((inverse@obj.matrix_world@v.co).x) for v in mesh.vertices));ev.to_mesh_clear()
    spans[name]=span+.001
for obj in bpy.data.objects[author['root']].children_recursive:
    if obj.type!='CURVE' or not any(k in obj.name for k in ['CurvedWingSpar','WingRolledGoldRim','CurvedInlaySeat','PerchBranch','ThoraxRail','SpringAntenna']):continue
    points=[]
    for spline in obj.data.splines:
        points.extend(list((C@(obj.matrix_basis@Vector(p.co[:3])).to_4d()).xyz+Vector((0,0,.005))) for p in spline.points)
    if len(points)<2:continue
    wing=wing_names.get(obj.parent.name);start=.30 if wing and wing['upper'] else .38 if wing else .03;end=.88 if wing and wing['upper'] else .90 if wing else .44
    guides.append({'node':obj.parent.name,'points':points,'start':start,'end':end,'wing':wing is not None,'span':spans.get(obj.parent.name,1.01425)})
data=json.loads((models/'G_optical_curator.json').read_text());bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=str(models/'G_optical_curator.glb'))
old=bpy.data.objects[data['g_archive']['contents'][1]['root']];parent=old.parent
for obj in list(old.children_recursive)+[old]:bpy.data.objects.remove(obj,do_unlink=True)
before=set(bpy.data.objects);bpy.ops.import_scene.gltf(filepath=str(components/'G_butterfly_r2.glb'));added=set(bpy.data.objects)-before
root=bpy.data.objects[author['root']];root.parent=parent;root.matrix_basis=Matrix.Translation((0,0,author['mount_offset_z']))
keep={root,*root.children_recursive}
for obj in added-keep:bpy.data.objects.remove(obj,do_unlink=True)
rig=[]
for r in author['rig']:
    for key in ['wing','crank','rod']:
        obj=bpy.data.objects[r[key]];rig.append({'name':obj.name,'kind':'butterfly_linkage','home':pose(obj.matrix_basis)})
entry={'id':1,'title':'瓷翼机械蝶','parameter':'展开蝶翼','action':'振翅','root':root.name,'source_blend':author['source_blend'],'rig':rig,'structure_edges':[],
       'butterfly':{'drive':author['drive'],'linkages':author['rig'],'wing_spans':spans,'guides':guides,'mount_offset_y':author['mount_offset_z'],'source_sha256':hashlib.sha256(source.read_bytes()).hexdigest()}}
data['g_archive']['contents'][1]=entry;data['source_blend']='blender/collection/G_butterfly_runtime_candidate.blend'
data['development_status']='Isolated butterfly candidate; assembled source geometry only, full animation not merged, live registry unchanged'
path=models/'G_optical_curator_butterfly_candidate.glb';path.with_suffix('.json').write_text(json.dumps(data,separators=(',',':'))+'\n')
assert not any(o.name.startswith('BASE_FIXED') for o in bpy.data.objects)
bpy.ops.object.select_all(action='SELECT');bpy.ops.export_scene.gltf(filepath=str(path),export_format='GLB',use_selection=True,export_apply=True,export_animations=False)
# Never replace the editable animation source when reassembling runtime meshes.
# prepare_butterfly_source.py owns the backed-up source copy; baking is separate.
optimize(path)
print('BUTTERFLY_CANDIDATE',json.dumps({'guides':len(guides),'segments':sum(len(g['points'])-1 for g in guides),'wing_spans':spans}),flush=True)
