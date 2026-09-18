"""Centered score carrier and authored scan strips on measured A tips."""
import bpy,math,json,hashlib,sys
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(Path(__file__).parent))
OUT=ROOT/'review/I_refinement/moonlight/central_scan_r1';OUT.mkdir(parents=True,exist_ok=True)
ART=ROOT/'app/assets/collection/art/I/moonlight_candidate/central_scan_r1';ART.mkdir(parents=True,exist_ok=True)
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
seed=json.loads((ROOT/'review/I_refinement/part_a_mouth/shutter_r2/collar_clamps/build.json').read_text())
source=ROOT/seed['source'];assert sha(source)==seed['source_sha256']
bpy.ops.wm.open_mainfile(filepath=str(source));bpy.context.scene.frame_set(1);bpy.context.view_layer.update()
mouth=bpy.data.objects['IAM_Mouth'];inverse=mouth.matrix_world.inverted()
liner=bpy.data.objects['IAM_IrisOuterCase_Fitted'];liner.data.calc_loop_triangles()
wall=BVHTree.FromPolygons([inverse@liner.matrix_world@v.co for v in liner.data.vertices],[tuple(t.vertices) for t in liner.data.loop_triangles],all_triangles=True)
anchors=[];tips=[]
for sign in [-1,1]:
    direction=Vector((sign*.72,-.30,0)).normalized();hit=wall.ray_cast(Vector((0,0,.015)),direction,2);assert hit[0] is not None
    anchors.append((sign,hit[0]-direction*.006))
for index in range(3):
    o=bpy.data.objects[f'IAM_TineRoundedAxial_{index}'];points=[inverse@o.matrix_world@v.co for v in o.data.vertices]
    z=min(v.z for v in points);tip=Vector((sum(v.x for v in points)/len(points),sum(v.y for v in points)/len(points),z))
    tips.append({'node':o.name,'mouth_point':list(tip),'local_point':list(o.matrix_world.inverted()@mouth.matrix_world@tip)})
target=ROOT/'blender/collection/I_central_scan_optics.blend'
if target.exists():
    prior=json.loads((OUT/'build.json').read_text());assert sha(target)==prior['source_sha256'],'Unrecorded optics edits'
    checkpoint=OUT/'iterations'/prior['source_sha256'][:12];checkpoint.mkdir(parents=True,exist_ok=True)
    (checkpoint/'build.json').write_text(json.dumps(prior,indent=2)+'\n')
    (ROOT/'blender/collection/checkpoints'/('I-central-scan-'+prior['source_sha256'][:12]+'.blend')).write_bytes(target.read_bytes())
for o in list(bpy.data.objects):bpy.data.objects.remove(o,do_unlink=True)
col=bpy.data.collections.new('CENTRAL_SCORE_READER');bpy.context.scene.collection.children.link(col)
import i_machined_geometry as P
P.configure(col);root=P.empty('I_MusicOptics',None)
width=1.16;height=.40;center_y=0.
def strip(name,points,strip_width):
    verts=[];uvs=[];faces=[]
    for i,p in enumerate(points):
        for side in [-1,1]:verts.append(tuple(Vector(p)+Vector((strip_width*.5*side,0,0))));uvs.append(((side+1)*.5,i/(len(points)-1)))
    for i in range(len(points)-1):faces.append((i*2,i*2+1,i*2+3,i*2+2))
    mesh=bpy.data.meshes.new(name+'Mesh');mesh.from_pydata(verts,[],faces);mesh.update()
    o=bpy.data.objects.new(name,mesh);col.objects.link(o);o.parent=root
    layer=mesh.uv_layers.new(name='AuthoredFilamentUV')
    for face in mesh.polygons:
        for li in face.loop_indices:layer.data[li].uv=uvs[mesh.loops[li].vertex_index]
    return o
verts=[];uvs=[];faces=[];n=64
for v in [0.,1.]:
    for i in range(n+1):
        u=i/n;verts.append(((.5-u)*width,center_y+(.5-v)*height,-.40-.035*math.sin(math.pi*u)));uvs.append((u,v))
for i in range(n):faces.append((i,i+1,n+2+i,n+1+i))
mesh=bpy.data.meshes.new('I_MoonlightStaffMesh');mesh.from_pydata(verts,[],faces);mesh.update()
sheet=bpy.data.objects.new('I_MoonlightStaff',mesh);col.objects.link(sheet);sheet.parent=root
layer=mesh.uv_layers.new(name='RealScoreUV')
for face in mesh.polygons:
    face.use_smooth=True
    for li in face.loop_indices:layer.data[li].uv=uvs[mesh.loops[li].vertex_index]
for sign,anchor in anchors:
    # Physical side projectors keep their already checked lower mount positions.
    # Only the nonphysical score plane moves to the mouth center.
    suffix='L' if sign<0 else 'R';pod=Vector((sign*.603,-.34,-.36))
    radial=Vector((anchor.x,anchor.y,0)).normalized();elbow=radial*.72;elbow.z=anchor.z
    for number,(a,b) in enumerate([(anchor,elbow),(elbow,pod)]):
        vec=b-a;P.cylinder('I_StaffProjectorArm'+suffix+str(number),.0055,vec.length,root,(a+b)*.5,'A_Nickel',vec.normalized())
    P.cylinder('I_StaffProjectorFoot'+suffix,.013,.006,root,anchor,'A_Bronze',radial)
    P.cylinder('I_StaffProjectorMountPin'+suffix,.002,.013,root,anchor+radial*.004,'A_Nickel',radial,bevel=.0002)
    P.cylinder('I_StaffProjectorElbow'+suffix,.008,.015,root,elbow,'A_Bronze',(0,0,1))
    P.box('I_StaffProjectorHousing'+suffix,(.029,.10,.035),root,pod,'A_Nickel',.006)
    P.box('I_StaffProjectorSlit'+suffix,(.012,.067,.003),root,pod+Vector((0,0,-.019)),'A_Rubber',.001)
    P.box('I_StaffProjectorGlass'+suffix,(.0035,.052,.003),root,pod+Vector((0,0,-.021)),'A_Bronze',.0008)
    P.screw('I_StaffProjectorScrew'+suffix,root,pod+Vector((0,.038,-.020)),.004,(0,0,-1))
focus=Vector((0,center_y,-.442));scan_start=Vector((0,center_y+height*.5,-.442));scan_end=Vector((0,center_y-height*.5,-.442))
strip('I_CentralReadingLine',[scan_start.lerp(scan_end,i/16) for i in range(17)],.30)
for index,tip in enumerate(tips):
    start=Vector(tip['mouth_point']);strip(f'I_TipReadingRay_{index}',[start.lerp(focus,i/16) for i in range(17)],.18)
    tip['ray']=f'I_TipReadingRay_{index}'
bpy.ops.wm.save_as_mainfile(filepath=str(target),compress=True)
bpy.ops.object.select_all(action='DESELECT')
for o in [root,*root.children_recursive]:o.select_set(True)
bpy.context.view_layer.objects.active=root;component=ART/'optics.glb'
bpy.ops.export_scene.gltf(filepath=str(component),export_format='GLB',use_selection=True,export_animations=False,export_morph=False,export_extras=True)
report={'source':str(target.relative_to(ROOT)),'source_sha256':sha(target),'component':str(component.relative_to(ROOT)),'component_sha256':sha(component),'mouth_source_sha256':seed['source_sha256'],'mouth_component_sha256':seed['component_sha256'],'mouth_node':'IAM_Mouth','sheet':'I_MoonlightStaff','width':width,'height':height,'center_y':center_y,'anchors':[{'sign':sign,'position':list(p)} for sign,p in anchors],'scanner':{'line':'I_CentralReadingLine','tips':tips,'focus':list(focus),'line_end':list(scan_end),'mask':'res://assets/collection/art/I/moonlight_candidate/central_scan_r1/filament_mask.png'},'scope':'New lower score carrier and measured-tip authored scan strips; same A geometry retained. Physical mount/motion and runtime visual review pending, not new complete nautilus.'}
report['scope']='User correction: center score in mouth, in front of measured tips. Physical lower side mounts unchanged; scan converges at score center. Same A geometry, independent optical candidate, not complete nautilus.'
(OUT/'build.json').write_text(json.dumps(report,indent=2)+'\n');(ART/'layout.json').write_text(json.dumps(report,indent=2)+'\n');print('I_CENTRAL_SCAN_OPTICS_BUILT',flush=True)
