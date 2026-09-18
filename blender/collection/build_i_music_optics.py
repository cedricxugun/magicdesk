"""Independent optical staff carrier and attached slit projectors for IAM mouth."""
import bpy,math,json,hashlib,sys
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(Path(__file__).parent))
OUT=ROOT/'review/I_refinement/moonlight/current_mouth';OUT.mkdir(parents=True,exist_ok=True)
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
seed=json.loads((ROOT/'review/I_refinement/part_a_mouth/shutter_r2/diaphragm/build.json').read_text());source=ROOT/seed['source'];assert sha(source)==seed['source_sha256']
bpy.ops.wm.open_mainfile(filepath=str(source));bpy.context.scene.frame_set(1);bpy.context.view_layer.update()
mouth=bpy.data.objects['IAM_Mouth'];liner=bpy.data.objects['IAM_IrisOuterCase_Fitted'];m=liner.data;m.calc_loop_triangles();inv=mouth.matrix_world.inverted()
wall=BVHTree.FromPolygons([inv@liner.matrix_world@v.co for v in m.vertices],[tuple(t.vertices) for t in m.loop_triangles],all_triangles=True)
anchors=[]
for sign in [-1,1]:
    direction=Vector((sign*.72,.30,0)).normalized();hit=wall.ray_cast(Vector((0,0,.015)),direction,2);assert hit[0] is not None
    anchors.append((sign,hit[0]-direction*.006))
target=ROOT/'blender/collection/I_music_optics.blend'
if target.exists():
    previous=json.loads((OUT/'build.json').read_text());assert sha(target)==previous['source_sha256'],'Unrecorded optics edits'
    (target.parent/'checkpoints'/('I-music-optics-'+sha(target)[:12]+'.blend')).write_bytes(target.read_bytes())
# Keep only the independent optical assembly in this output. Seed is not saved.
for o in list(bpy.data.objects):bpy.data.objects.remove(o,do_unlink=True)
col=bpy.data.collections.new('MUSIC_OPTICS');bpy.context.scene.collection.children.link(col)
import i_machined_geometry as P
P.configure(col);root=P.empty('I_MusicOptics',None)
width=1.16;height=.40;center_y=.34;verts=[];faces=[];uv=[];n=48
for v in [0.,1.]:
    for i in range(n+1):
        u=i/n;verts.append(((.5-u)*width,center_y+(.5-v)*height,-.19-.035*math.sin(math.pi*u)));uv.append((u,v))
for i in range(n):faces.append((i,i+1,n+2+i,n+1+i))
mesh=bpy.data.meshes.new('I_MoonlightStaffMesh');mesh.from_pydata(verts,[],faces);mesh.update();sheet=bpy.data.objects.new('I_MoonlightStaff',mesh);col.objects.link(sheet);sheet.parent=root
layer=mesh.uv_layers.new(name='RealScoreUV')
for face in mesh.polygons:
    face.use_smooth=True
    for li in face.loop_indices:layer.data[li].uv=uv[mesh.loops[li].vertex_index]
for sign,anchor in anchors:
    suffix='L' if sign<0 else 'R';pod=Vector((sign*.603,center_y,-.19))
    radial=Vector((anchor.x,anchor.y,0)).normalized();elbow=radial*.72;elbow.z=anchor.z
    for number,(a,b) in enumerate([(anchor,elbow),(elbow,pod)]):
        vec=b-a;P.cylinder('I_StaffProjectorArm'+suffix+str(number),.0055,vec.length,root,(a+b)*.5,'A_Nickel',vec.normalized())
    foot=P.cylinder('I_StaffProjectorFoot'+suffix,.013,.006,root,anchor,'A_Bronze',radial)
    P.cylinder('I_StaffProjectorMountPin'+suffix,.002,.013,root,anchor+radial*.004,'A_Nickel',radial,bevel=.0002)
    P.cylinder('I_StaffProjectorElbow'+suffix,.008,.015,root,elbow,'A_Bronze',(0,0,1))
    housing=P.box('I_StaffProjectorHousing'+suffix,(.029,.10,.035),root,pod,'A_Nickel',.006)
    P.box('I_StaffProjectorSlit'+suffix,(.012,.067,.003),root,pod+Vector((0,0,-.019)),'A_Rubber',.001)
    P.box('I_StaffProjectorGlass'+suffix,(.0035,.052,.003),root,pod+Vector((0,0,-.021)),'A_Bronze',.0008)
    P.screw('I_StaffProjectorScrew'+suffix,root,pod+Vector((0,-.038,-.020)),.004,(0,0,-1))
bpy.ops.wm.save_as_mainfile(filepath=str(target),compress=True)
bpy.ops.object.select_all(action='DESELECT')
for o in [root,*root.children_recursive]:o.select_set(True)
bpy.context.view_layer.objects.active=root;component=ROOT/'app/assets/collection/art/I/moonlight_candidate/current_mouth/optics.glb';component.parent.mkdir(parents=True,exist_ok=True)
bpy.ops.export_scene.gltf(filepath=str(component),export_format='GLB',use_selection=True,export_animations=False,export_morph=False,export_extras=True)
report={'source':str(target.relative_to(ROOT)),'source_sha256':sha(target),'component':str(component.relative_to(ROOT)),'component_sha256':sha(component),'mouth_source_sha256':seed['source_sha256'],'mouth_component_sha256':seed['component_sha256'],'mouth_node':'IAM_Mouth','sheet':'I_MoonlightStaff','width':width,'height':height,'center_y':center_y,'anchors':[{'sign':sign,'position':list(p)} for sign,p in anchors],'scope':'Separate authored staff carrier and small slit-projector assembly, placed using current mouth/liner coordinates. Optical plane intentionally open; mount/collision/visual verification pending, no full-conch acceptance.'}
(OUT/'build.json').write_text(json.dumps(report,indent=2)+'\n');(component.parent/'layout.json').write_text(json.dumps(report,indent=2)+'\n');print('I_MUSIC_OPTICS_BUILT',flush=True)
