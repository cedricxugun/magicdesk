"""Build only the new observatory, leaving the current animated app source intact."""
import bpy,json,sys,math,hashlib
from pathlib import Path
from mathutils import Vector
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(Path(__file__).parent))
from geometry import Builder
from observatory_component import Observatory
from optimize_runtime_meshes import optimize
b=Builder('GO2','Observatory component');author=Observatory(b);entry=author.build()
scene=bpy.context.scene;scene.render.fps=30
assets=ROOT/'app/assets/collection/components';assets.mkdir(exist_ok=True)
source=ROOT/'blender/collection/G_observatory_r2.blend'
if source.exists():
    backup=ROOT/'blender/collection/checkpoints'/('G_observatory_r2-'+hashlib.sha256(source.read_bytes()).hexdigest()[:12]+'.blend');backup.parent.mkdir(exist_ok=True)
    if not backup.exists():backup.write_bytes(source.read_bytes())
bpy.context.view_layer.update();deps=bpy.context.evaluated_depsgraph_get();vertices=[];triangles=0
inverse=author.root.matrix_world.inverted()
for obj in author.root.children_recursive:
    if obj.type not in ['MESH','CURVE','FONT']:continue
    ev=obj.evaluated_get(deps);mesh=ev.to_mesh();mesh.calc_loop_triangles();triangles+=len(mesh.loop_triangles)
    vertices.extend(inverse@obj.matrix_world@v.co for v in mesh.vertices);ev.to_mesh_clear()
bounds={'min':[min(v[k] for v in vertices) for k in range(3)],'max':[max(v[k] for v in vertices) for k in range(3)],'radial_max':max(math.hypot(v.x,v.y) for v in vertices),'triangles':triangles}
assert bounds['radial_max']<=.351,bounds
assert abs(bounds['max'][2]-1.215)<.001,bounds
assert bounds['min'][2]>=-.001,bounds
entry['bounds']=bounds;entry['mount_offset_y']=.0128
(assets/'G_observatory_r2.json').write_text(json.dumps(entry,separators=(',',':')),encoding='utf-8')
bpy.ops.object.select_all(action='DESELECT')
for obj in b.col.all_objects:obj.select_set(True)
bpy.context.view_layer.objects.active=b.root
path=assets/'G_observatory_r2.glb'
bpy.ops.export_scene.gltf(filepath=str(path),export_format='GLB',use_selection=True,export_apply=True,export_animations=False)
# A reference record in a separate collection is not part of the component.
reference=bpy.data.collections.new('Reference_media_only');scene.collection.children.link(reference)
disc=b.cyl('ReferenceOriginalDisc',.420,.02352,'ObservatoryInk',b.root,(0,0,-.0143),n=160)
for col in list(disc.users_collection):col.objects.unlink(disc)
reference.objects.link(disc)
scene.render.engine='CYCLES';scene.cycles.samples=32;scene.cycles.use_denoising=True
scene.render.resolution_x=1000;scene.render.resolution_y=1200;scene.render.resolution_percentage=100;scene.render.film_transparent=True
world=bpy.data.worlds.new('ComponentStudio');world.use_nodes=True;scene.world=world
node=world.node_tree.nodes.new('ShaderNodeTexEnvironment');node.image=bpy.data.images.load(str(ROOT/'app/assets/studio_small_09_4k.exr'),check_existing=True)
background=next(n for n in world.node_tree.nodes if n.type=='BACKGROUND');background.inputs['Strength'].default_value=.24;world.node_tree.links.new(node.outputs['Color'],background.inputs['Color'])
for index,(position,energy,size) in enumerate([((-2,-3,4),150,2.5),((2,1,3),200,2),((0,-3,1.3),30,1.5)]):
    data=bpy.data.lights.new('ComponentArea'+str(index),'AREA');data.energy=energy;data.shape='DISK';data.size=size
    obj=bpy.data.objects.new(data.name,data);scene.collection.objects.link(obj);obj.location=position;obj.rotation_euler=(Vector((0,0,.55))-obj.location).to_track_quat('-Z','Y').to_euler()
camera=bpy.data.cameras.new('ComponentCamera');obj=bpy.data.objects.new(camera.name,camera);scene.collection.objects.link(obj);scene.camera=obj
camera.type='ORTHO';camera.ortho_scale=1.42;obj.location=(.55,-3.6,1.55);obj.rotation_euler=(Vector((0,0,.60))-obj.location).to_track_quat('-Z','Y').to_euler()
scene['component_status']='Independent geometry candidate; not integrated or visually accepted'
scene['reference']='production/G_optical_curator/observatory_r2/modeling_reference.png'
scene['rig_spec']=json.dumps(entry['rig']);scene['gear_train']=json.dumps(entry['gear_train'])
scene['design_dimensions']='height1.215 base0.630 footprint<=0.70 record0.840 reader0.900'
bpy.ops.file.make_paths_relative();bpy.ops.wm.save_as_mainfile(filepath=str(source))
review=ROOT/'review/G_optical_curator/observatory_r2';review.mkdir(exist_ok=True)
(review/'component_report.json').write_text(json.dumps({'bounds':bounds,'guides':len(entry['build_guides']),'guide_segments':len(entry['structure_edges']),'rig_nodes':len(entry['rig']),'source':str(source.relative_to(ROOT)),'app_integrated':False},indent=2)+'\n')
scene.render.filepath=str(review/'component_three_quarter.png');bpy.ops.render.render(write_still=True)
for label,position in [('front',(0,-4,.60)),('side',(4,0,.60)),('rear',(0,4,.60))]:
    obj.location=position;obj.rotation_euler=(Vector((0,0,.60))-obj.location).to_track_quat('-Z','Y').to_euler();scene.render.filepath=str(review/('component_'+label+'.png'));bpy.ops.render.render(write_still=True)
optimize(path)
print('OBSERVATORY_COMPONENT_BUILT',json.dumps(bounds),flush=True)
