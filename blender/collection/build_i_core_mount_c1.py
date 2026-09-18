"""Split metal rear-flange collar, clamping hardware and load-bearing clevises.

Independent C1 candidate; current A/B3 source files are never overwritten.
"""
import bpy,bmesh,json,hashlib,math,sys
from pathlib import Path
from mathutils import Vector
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT/'blender/collection'))
import i_machined_geometry as h
OUT=ROOT/'review/I_refinement/part_c_core/mount_c1';OUT.mkdir(parents=True,exist_ok=True)
seed=json.loads((ROOT/'review/I_refinement/part_b_shell/linkage_b3/build.json').read_text());fit=json.loads((OUT/'mount_envelope.json').read_text())
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
assert seed['source_sha256']==sha(ROOT/seed['source'])==fit['source_sha256'] and not fit['contacts']
TARGET=ROOT/'blender/collection/I_core_mount_c1.blend'
if TARGET.exists():
    previous=json.loads((OUT/'build.json').read_text());assert previous['source_sha256']==sha(TARGET),'Unrecorded C1 edits'
    (TARGET.parent/'checkpoints'/('I-core-mount-c1-'+sha(TARGET)[:12]+'.blend')).write_bytes(TARGET.read_bytes())
bpy.ops.wm.open_mainfile(filepath=str(ROOT/seed['source']));scene=bpy.context.scene;scene.frame_set(1);bpy.context.view_layer.update()
col=bpy.data.collections.new('I_C_MOUNT_C1');scene.collection.children.link(col);h.configure(col)
root=h.empty('IC1_Module',None);mount=h.empty('IC1_MouthMount',root);mount.matrix_world=bpy.data.objects['IAM_MODULE'].matrix_world.copy()
profile=fit['mount_profile_mouth_local']

def finish_mesh(name,vertices,faces,parent,material='A_Nickel',bevel=.0006):
    m=bpy.data.meshes.new(name+'Mesh');m.from_pydata(vertices,[],faces);m.update();o=bpy.data.objects.new(name,m);col.objects.link(o)
    h.finish(o,name,parent,(0,0,0),material,bevel)
    # Surface positions, not the generated illustration, define cylindrical UVs.
    uv=m.uv_layers.new(name='MachinedUV') if not m.uv_layers else m.uv_layers[0]
    for polygon in m.polygons:
        for li in polygon.loop_indices:
            p=m.vertices[m.loops[li].vertex_index].co;uv.data[li].uv=(math.atan2(p.y,p.x)/math.tau,p.z*12.)
    return o

def merge(target,part):
    bpy.context.view_layer.update();bpy.context.view_layer.objects.active=target
    modifier=target.modifiers.new('Integral machined boss','BOOLEAN');modifier.operation='UNION';modifier.solver='EXACT';modifier.object=part
    bpy.ops.object.modifier_apply(modifier=modifier.name);h.parts.remove(part.name);bpy.data.objects.remove(part,do_unlink=True)

halves=[]
for half in range(2):
    begin=half*math.pi+.006;end=(half+1)*math.pi-.006;n=128;vs=[];fs=[]
    for r,z in profile:
        vs.extend((r*math.cos(begin+(end-begin)*i/n),r*math.sin(begin+(end-begin)*i/n),z) for i in range(n+1))
    count=len(profile)
    for k in range(count):
        for i in range(n):fs.append((k*(n+1)+i,k*(n+1)+i+1,((k+1)%count)*(n+1)+i+1,((k+1)%count)*(n+1)+i))
    fs.extend([tuple(k*(n+1) for k in range(count-1,-1,-1)),tuple(k*(n+1)+n for k in range(count))])
    ring=finish_mesh('IC1_CollarUpper' if half==0 else 'IC1_CollarLower',vs,fs,mount,'A_Satin')
    for sign in [-1,1]:
        tab=h.box('IC1_ClampTabTool',(.042,.055,.048),mount,(sign*.594,.036 if half==0 else -.036,.588),'A_Satin',.003)
        merge(ring,tab)
        h.drill(ring,.0056,.16,mount,(sign*.601,0,.590),(0,1,0))
    halves.append(ring)
    print('C1_COLLAR_HALF',half,flush=True)

for sign in [-1,1]:
    x=sign*.601
    h.cylinder('IC1_SeamCrossBolt_'+str(sign),.0052,.143,mount,(x,0,.590),'A_Nickel',(0,1,0))
    for side in [-1,1]:
        h.sleeve('IC1_SeamWasher_%s_%s'%(sign,side),.0094,.00565,.002,mount,(x,side*.066,.590),'A_Bronze',(0,1,0))
        h.screw('IC1_SeamRetainer_%s_%s'%(sign,side),mount,(x,side*.072,.590),.0085,(0,side,0))

# Forward-offset trunnion clevises attach to the metal ring. The outline stays
# ahead of B's rear taper; lugs do not push the supports through the porcelain.
outline=[(-.555,.582),(-.583,.582),(-.653,.533),(-.653,.493),(-.606,.493),(-.555,.552)]
anchors=[]
for sign in [-1,1]:
    center_x=sign*.17
    for cheek in [-1,1]:
        x=center_x+cheek*.021;depth=.010;vs=[(x+side*depth/2,y,z) for side in [-1,1] for y,z in outline];n=len(outline)
        fs=[tuple(range(n-1,-1,-1)),tuple(range(n,2*n))]+[(i,(i+1)%n,(i+1)%n+n,i+n) for i in range(n)]
        lug=finish_mesh('IC1_TrunnionCheekTool',vs,fs,mount,'A_Satin',.002)
        merge(halves[1],lug)
    location=Vector((center_x,-.627,.519));h.drill(halves[1],.0092,.11,mount,location,(1,0,0))
    for cheek in [-1,1]:h.sleeve('IC1_TrunnionBush_%s_%s'%(sign,cheek),.00905,.0061,.010,mount,location+Vector((cheek*.021,0,0)),'A_Bronze',(1,0,0))
    h.cylinder('IC1_TrunnionPin_'+str(sign),.0058,.080,mount,location,'A_Nickel',(1,0,0))
    for side in [-1,1]:h.screw('IC1_TrunnionRetainer_%s_%s'%(sign,side),mount,location+Vector((side*.043,0,0)),.009,(side,0,0))
    anchors.append({'name':'IC1_TrunnionPin_'+str(sign),'mouth_local':list(location),'world':list(mount.matrix_world@location),'axis_world':list((mount.matrix_world.to_3x3()@Vector((1,0,0))).normalized())})

# Re-machine the bore after joining seam tabs. A union must not put the tab's
# inside corner back into the real flange volume cleared by the original ring.
original=bpy.data.objects['IAM_RearMountFlange_0074'];tool=original.copy();tool.data=original.data.copy();col.objects.link(tool);tool.name='IC1_ActualFlangeReliefTool'
for vertex in tool.data.vertices:vertex.co+=vertex.normal*.0015
tool.data.update();bpy.context.view_layer.update()
for collar in halves:
    bpy.context.view_layer.objects.active=collar;modifier=collar.modifiers.new('Actual flange fit relief','BOOLEAN');modifier.operation='DIFFERENCE';modifier.solver='EXACT';modifier.object=tool
    bpy.ops.object.modifier_apply(modifier=modifier.name)
bpy.data.objects.remove(tool,do_unlink=True)
for o in halves:
    bm=bmesh.new();bm.from_mesh(o.data);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces))
    for face in bm.faces:face.smooth=True
    for edge in bm.edges:edge.smooth=edge.is_manifold and edge.calc_face_angle(0.)<.55
    bm.to_mesh(o.data);bm.free()
bpy.context.view_layer.update();bpy.ops.wm.save_as_mainfile(filepath=str(TARGET),compress=True)
bpy.ops.object.select_all(action='DESELECT')
for collection in [bpy.data.collections['I_B_PANELS_B2'],col]:
    for o in collection.objects:o.select_set(True)
bpy.context.view_layer.objects.active=root
component=ROOT/'app/assets/collection/components/I_core_mount_c1.glb'
bpy.ops.export_scene.gltf(filepath=str(component),export_format='GLB',use_selection=True,export_animations=False,export_extras=True)
report={**seed,'source':str(TARGET.relative_to(ROOT)),'source_sha256':sha(TARGET),'component':str(component.relative_to(ROOT)),'component_sha256':sha(component),'seed_source_sha256':seed['source_sha256'],'mount_hardware':list(h.parts),'mount_profile':profile,'mount_anchors':anchors,'hardware':seed['hardware']+list(h.parts),'status':'split_metal_mount_candidate_requires_checks','scope':'Two machined halves around the existing rear metal flange, integral clamp tabs and bored trunnion clevises. Preserves A and B3 mechanism. Support arms still provisional and C continuous core not built. No finite mount clearance or art acceptance yet.'}
report['review_scope']=report['scope']
(OUT/'build.json').write_text(json.dumps(report,indent=2)+'\n');print('C1_MOUNT_BUILD_COMPLETE',len(h.parts),flush=True)
