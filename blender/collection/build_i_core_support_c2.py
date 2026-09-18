"""C2 metal load path and deliberately formed coaming ports, in a new source."""
import bpy,bmesh,json,hashlib,math,sys
from pathlib import Path
from mathutils import Vector,Matrix
from mathutils.bvhtree import BVHTree
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT/'blender/collection'))
import i_machined_geometry as h
OUT=ROOT/'review/I_refinement/part_c_core/support_c2';OUT.mkdir(parents=True,exist_ok=True)
seed=json.loads((ROOT/'review/I_refinement/part_c_core/mount_c1/build.json').read_text());layout=json.loads((ROOT/'review/I_refinement/part_c_core/mount_c1/support_layout_ports.json').read_text())
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
assert seed['source_sha256']==sha(ROOT/seed['source'])==layout['source_sha256'] and layout['complete'] and layout['requires_coaming_ports']
TARGET=ROOT/'blender/collection/I_core_support_c2.blend'
if TARGET.exists():
    old=json.loads((OUT/'build.json').read_text());assert old['source_sha256']==sha(TARGET),'Unrecorded C2 edits'
    (TARGET.parent/'checkpoints'/('I-core-support-c2-'+sha(TARGET)[:12]+'.blend')).write_bytes(TARGET.read_bytes())
bpy.ops.wm.open_mainfile(filepath=str(ROOT/seed['source']));scene=bpy.context.scene;scene.frame_set(1);bpy.context.view_layer.update()
col=bpy.data.collections.new('I_C_SUPPORT_C2');scene.collection.children.link(col);h.configure(col);root=h.empty('IC2_Module',None)
coaming=bpy.data.objects[seed['fixed_collar']]
cleanup_records=[]
def clean_coaming(stage):
    bm=bmesh.new();bm.from_mesh(coaming.data)
    before=sum(not e.is_manifold for e in bm.edges)
    bmesh.ops.remove_doubles(bm,verts=list(bm.verts),dist=.000005)
    bmesh.ops.dissolve_degenerate(bm,edges=list(bm.edges),dist=.000001)
    loose=[e for e in bm.edges if not e.link_faces]
    if loose:bmesh.ops.delete(bm,geom=loose,context='EDGES')
    bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces))
    cleanup_records.append({'stage':stage,'nonmanifold_before':before,'nonmanifold_after':sum(not e.is_manifold for e in bm.edges),'tiny_faces_after':sum(f.calc_area()<1e-12 for f in bm.faces)})
    bm.to_mesh(coaming.data);bm.free()
clean_coaming('inherited_fixed_cover')
coaming.data.calc_loop_triangles()
coaming_tree=BVHTree.FromPolygons([coaming.matrix_world@v.co for v in coaming.data.vertices],[tuple(t.vertices) for t in coaming.data.loop_triangles],all_triangles=True)

def beam(name,a,b,r,mat='A_Nickel',r2=None):
    a,b=Vector(a),Vector(b);delta=b-a
    if r2 is None:return h.cylinder(name,r,delta.length,root,(a+b)/2,mat,delta,.0005)
    bpy.ops.mesh.primitive_cone_add(vertices=64,radius1=r,radius2=r2,depth=delta.length)
    o=h.finish(bpy.context.object,name,root,(a+b)/2,mat,.0005);o.rotation_mode='QUATERNION';o.rotation_quaternion=delta.to_track_quat('Z','Y')
    for p in o.data.polygons:p.use_smooth=abs(p.normal.z)<.98
    return o

def frame(name,origin,direction,axis):
    d=Vector(direction).normalized();n=Vector(axis).normalized();o=h.empty(name,root,origin);o.rotation_mode='QUATERNION';o.rotation_quaternion=Matrix((d,n.cross(d),n)).transposed().to_quaternion();return o

def cheek(name,parent,length,offset,r=.023):
    n=32;outline=[]
    for end,start in [(length,-math.pi/2),(0,math.pi/2)]:
        for i in range(n+1):
            angle=start+i*math.pi/n;outline.append((end+r*math.cos(angle),r*math.sin(angle)))
    count=len(outline);vs=[(x,y,offset+z) for z in [-.004,.004] for x,y in outline]
    fs=[tuple(range(count-1,-1,-1)),tuple(range(count,2*count))]+[(i,(i+1)%count,(i+1)%count+count,i+count) for i in range(count)]
    mesh=bpy.data.meshes.new(name+'Mesh');mesh.from_pydata(vs,[],fs);mesh.update();o=bpy.data.objects.new(name,mesh);col.objects.link(o);h.finish(o,name,parent,(0,0,0),'A_Satin',.001)
    h.drill(o,.0072,.02,parent,(length,0,offset),(0,0,1));return o

def pin(name,point,axis,length=.084):
    h.cylinder(name,.0067,length,root,point,'A_Nickel',axis)
    for sign in [-1,1]:
        h.sleeve(name+'_Washer_'+str(sign),.012,.007,.002,root,point+axis*(sign*.037),'A_Bronze',axis)
        h.screw(name+'_Retainer_'+str(sign),root,point+axis*(sign*(length/2+.003)),.011,axis*sign)

ports=[];supports=[]
for index,row in enumerate(layout['supports']):
    pre='IC2_Leg_%02d_'%(index+1);top=Vector(row['top']);knee=Vector(row['knee']);foot=Vector(row['foot']);axis=Vector(row['axis']);upper=(knee-top).normalized();lower=(foot-knee).normalized()
    # Bearing eye and neck fit between the real C1 clevis cheeks and share its pin.
    h.sleeve(pre+'TopEye',.0177,.00525,.023,root,top,'A_Nickel',axis)
    beam(pre+'ForgedNeck',top+upper*.013,top+upper*.11,.0115,'A_Nickel',.026)
    beam(pre+'UpperBarrel',top+upper*.108,knee-upper*.060,.026,'A_Nickel')
    for distance in [.14,(knee-top).length-.085]:
        p=top+upper*distance;h.sleeve(pre+'BarrelCollar_'+str(round(distance,3)),.029,.0257,.012,root,p,'A_Satin',upper)
        h.sleeve(pre+'BronzeSeal_'+str(round(distance,3)),.0294,.0261,.003,root,p+upper*.009,'A_Bronze',upper)
    yoke=frame(pre+'KneeForkFrame',knee-upper*.058,upper,axis)
    for sign in [-1,1]:cheek(pre+'KneeFork_'+str(sign),yoke,.058,sign*.030)
    h.box(pre+'KneeCrossBridge',(.021,.033,.065),yoke,(0,0,0),'A_Nickel',.002)
    h.sleeve(pre+'KneeEye',.024,.0071,.030,root,knee,'A_Dark',axis);pin(pre+'KneePin',knee,axis)
    beam(pre+'LowerPiston',knee+lower*.018,foot-lower*.026,.021,'A_Nickel')
    beam(pre+'LowerSleeve',knee+lower*.09,foot-lower*.062,.031,'A_Dark')
    for t in [.10,(foot-knee).length-.078]:
        p=knee+lower*t;h.sleeve(pre+'LowerSeal_'+str(round(t,3)),.034,.031,.010,root,p,'A_Nickel',lower)
    h.sleeve(pre+'FootEye',.023,.0071,.030,root,foot,'A_Nickel',axis)
    base_frame=frame(pre+'FootForkFrame',foot-Vector((0,0,.042)),Vector((0,0,1)),axis)
    for sign in [-1,1]:cheek(pre+'FootFork_'+str(sign),base_frame,.042,sign*.028,.022)
    pin(pre+'FootPin',foot,axis,.080)
    floor=Vector((foot.x,foot.y,.5625));radial=Vector((foot.x,foot.y,0)).normalized();tangent=Vector((-radial.y,radial.x,0));shoe_rotation=Matrix((radial,tangent,Vector((0,0,1)))).transposed().to_quaternion()
    shoe=h.cylinder(pre+'DeckSeat',.075,.030,root,floor+Vector((0,0,.015)),'A_Satin')
    pad=h.sleeve(pre+'DeckIsolationRing',.073,.057,.003,root,floor+Vector((0,0,.0015)),'A_Rubber')
    for o in [shoe,pad]:
        o.rotation_mode='QUATERNION';o.rotation_quaternion=shoe_rotation;o.scale=(.034/.075,1,1);bpy.context.view_layer.objects.active=o
        bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
    for sign in [-1,1]:
        p=floor+tangent*(sign*.050)+Vector((0,0,.034));h.screw(pre+'DeckFastener_'+str(sign),root,p,.0065)

    # The old fixed cover had no intentional leg exits. Cut only that cover,
    # preserving A porcelain, then fit a real sleeve through each formed port.
    def crossings(origin):
        found=[];start=origin.copy();travel=0.
        for _ in range(8):
            hit=coaming_tree.ray_cast(start,upper,(knee-top).length-travel)
            if hit[0] is None:break
            depth=(hit[0]-origin).dot(upper);found.append(depth);travel=depth+.0001;start=origin+upper*travel
        return found
    center_hits=crossings(top);assert len(center_hits)>=2,('Missing intended cover port',index)
    tangent=axis.normalized();second=upper.cross(tangent).normalized();depths=[]
    for i in range(64):
        a=i*math.tau/64;hits=crossings(top+(tangent*math.cos(a)+second*math.sin(a))*.050)
        if len(hits)>=2:depths.extend(hits)
    assert depths
    back_depth=min(depths)-.012;front_depth=max(depths)+.006
    tool=beam('IC2_CoamingPortTool',top,knee,.0320,'A_Dark');bpy.context.view_layer.update();bpy.context.view_layer.objects.active=coaming
    mod=coaming.modifiers.new('Formed support passage','BOOLEAN');mod.operation='DIFFERENCE';mod.solver='EXACT';mod.object=tool;bpy.ops.object.modifier_apply(modifier=mod.name)
    h.parts.remove(tool.name);bpy.data.objects.remove(tool,do_unlink=True)
    mid=top+upper*((back_depth+front_depth)/2)
    h.sleeve(pre+'PortLiner',.0315,.027,front_depth-back_depth,root,mid,'A_Satin',upper)
    for tag,depth in [('Rear',back_depth),('Front',front_depth)]:
        h.sleeve(pre+'PortLip'+tag,.039,.027,.004,root,top+upper*depth,'A_Nickel',upper)
        h.sleeve(pre+'PortSeal'+tag,.0271,.0255,.008,root,top+upper*(depth+(.003 if tag=='Front' else -.003)),'A_Rubber',upper)
    ports.append({'axis':list(upper),'origin':list(top),'center_crossings':center_hits,'ferrule_limits':[back_depth,front_depth],'cut_radius':.0320,'liner_outer_radius':.0315})
    supports.append({**row,'actual_eye':pre+'TopEye','actual_knee_pin':pre+'KneePin','actual_foot_pin':pre+'FootPin'})
    print('C2_SUPPORT_BUILT',index+1,flush=True)

clean_coaming('after_formed_ports')
removed=[]
for name in seed['hardware']:
    if name.startswith('IB3_ProvisionalFrontStrut_') or name.startswith('IB3_ProvisionalFoot_'):
        obj=bpy.data.objects.get(name)
        if obj:bpy.data.objects.remove(obj,do_unlink=True);removed.append(name)

# B3's back rail will receive its own real flange adapter with the continuous core.
# Keep it visible and flagged until that connection has been authored.
for name in ['IC1_CollarUpper','IC1_CollarLower']:
    o=bpy.data.objects[name];bm=bmesh.new();bm.from_mesh(o.data)
    for face in bm.faces:face.smooth=True
    for edge in bm.edges:edge.smooth=edge.is_manifold and edge.calc_face_angle(0.)<.55
    bm.to_mesh(o.data);bm.free()
bpy.context.view_layer.update();bpy.ops.wm.save_as_mainfile(filepath=str(TARGET),compress=True)
bpy.ops.object.select_all(action='DESELECT')
for collection in [bpy.data.collections['I_B_PANELS_B2'],bpy.data.collections['I_C_MOUNT_C1'],col]:
    for o in collection.objects:o.select_set(True)
bpy.context.view_layer.objects.active=root;component=ROOT/'app/assets/collection/components/I_core_support_c2.glb'
bpy.ops.export_scene.gltf(filepath=str(component),export_format='GLB',use_selection=True,export_animations=False,export_extras=True)
report={**seed,'source':str(TARGET.relative_to(ROOT)),'source_sha256':sha(TARGET),'component':str(component.relative_to(ROOT)),'component_sha256':sha(component),'seed_source_sha256':seed['source_sha256'],'hardware':[name for name in seed['hardware'] if name not in removed]+list(h.parts),'support_hardware':list(h.parts),'support_layout':supports,'formed_ports':ports,'coaming_cleanup':cleanup_records,'removed_provisional':removed,'provisional_supports':[],'status':'metal_support_candidate_requires_checks','scope':'Two actual articulated metal support legs connect the existing C1 rear-flange collar to base deck seats; deliberate lined passages cut only in B fixed cover, A porcelain unchanged. B3 rail root is still provisional and continuous C core absent. Detailed collision/base-fit and art checks pending.'}
report['review_scope']=report['scope'];(OUT/'build.json').write_text(json.dumps(report,indent=2)+'\n');print('C2_SUPPORT_BUILD_COMPLETE',len(h.parts),flush=True)
