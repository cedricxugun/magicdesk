"""Two formed metal supports from the actual collar trunnions to the existing deck."""
import bpy,bmesh,json,hashlib,sys,shutil,struct,math
from pathlib import Path
from mathutils import Vector,Matrix
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(Path(__file__).parent));import i_machined_geometry as h;import i_trunnion_support_geometry as g;import i_render_triangle_cleanup as triangle_cleanup;import i_boolean_residue as residue
OUT=ROOT/'review/I_refinement/nautilus_r1/trunnion_support_r18';OUT.mkdir(parents=True,exist_ok=True);TARGET=ROOT/'blender/collection/I_nautilus_trunnion_supports_r18.blend';COMPONENT=ROOT/'app/assets/collection/components/I_nautilus_trunnion_supports_r18.glb';sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
parent_path=ROOT/'review/I_refinement/nautilus_r1/chamber04_r15/build.json';seed=json.loads(parent_path.read_text());plan=json.loads((OUT/'route_r2/route_plan.json').read_text());sections=json.loads((OUT/'route_r2/port_sections.json').read_text());assert sha(ROOT/seed['source'])==seed['source_sha256']==plan['source_sha256']==sections['source_sha256'];assert plan['complete_route_candidate'] and plan['lower_neck_included'];assert json.loads((parent_path.parent/'checkpoint.json').read_text())['source_sha256']==seed['source_sha256'];assert (ROOT/'production/I_refinement/nautilus_r1/trunnion_support_r18/trunnion_and_foot_finish_r1.png').exists()
if TARGET.exists():
    old=json.loads((OUT/'build.json').read_text());assert sha(TARGET)==old['source_sha256'],'Unrecorded support edits';archive=OUT/'iterations'/old['source_sha256'][:12];archive.mkdir(parents=True,exist_ok=True)
    for p in OUT.glob('*.json'):shutil.copy2(p,archive/p.name)
    if (OUT/'views').exists():shutil.copytree(OUT/'views',archive/'views',dirs_exist_ok=True)
    shutil.copy2(TARGET,TARGET.parent/'checkpoints'/('I-trunnion-support-'+old['source_sha256'][:12]+'.blend'))
bpy.ops.wm.open_mainfile(filepath=str(ROOT/seed['source']));scene=bpy.context.scene;scene.frame_set(1);bpy.context.view_layer.update();body=bpy.data.objects['IN1_BodyRoot'];deck=bpy.data.objects['IN1_DeckFoot'];deck_center=deck.matrix_world.translation.copy();deck_top=max((deck.matrix_world@v.co).z for v in deck.data.vertices);skin_names=sorted({p['mesh'] for row in plan['selected'] for p in row['required_fixed_shell_ports']});allowed=set(skin_names+[deck.name])
def fingerprint(o):
    d=hashlib.sha256()
    for v in o.data.vertices:d.update(struct.pack('<3f',*v.co))
    for f in o.data.polygons:d.update(struct.pack('<'+'I'*len(f.vertices),*f.vertices))
    return [d.hexdigest(),[list(r) for r in o.matrix_world],o.parent.name if o.parent else None,[m.name if m else None for m in o.data.materials]]
protected={o.name:fingerprint(o) for o in bpy.data.objects if o.type=='MESH' and o.name not in allowed};source_shapes={n:fingerprint(bpy.data.objects[n]) for n in allowed}
source_materials={n:list(bpy.data.objects[n].data.materials) for n in allowed}
col=bpy.data.collections.new('I_TRUNNION_SUPPORTS_R18');scene.collection.children.link(col);root=bpy.data.objects.new('IS18_TrunnionSupports',None);col.objects.link(root);root.parent=body;root.matrix_world=Matrix.Identity(4);g.configure(col,root);references={}
for name in allowed:
    original=bpy.data.objects[name];ref=original.copy();ref.data=original.data.copy();ref.name='IS18_Reference_'+name;col.objects.link(ref);ref.parent=None;ref.matrix_world=original.matrix_world.copy();references[name]=ref
    triangle_cleanup.repair(original)
red=bpy.data.objects['IN1_HubInsetFront'].data.materials[0];supports=[];ports=[];fasteners=[]
for index,row in enumerate(plan['selected']):
    pre='IS18_Leg%02d_'%(index+1);top=Vector(row['top']);foot=Vector(row['foot']);axis=Vector(row['pin_axis']).normalized();direction=(foot-top).normalized();length=(foot-top).length;assert abs(direction.dot(axis))<1e-6
    leg=g.profile_body(pre+'FormedBody',top,foot,axis);upper=h.sleeve(pre+'UpperEye',.0145,.00435,.0184,root,top,'A_Nickel',axis);lower=h.sleeve(pre+'LowerEye',.024,.0061,.030,root,foot,'A_Nickel',axis);g.boolean(leg,upper);g.boolean(leg,lower)
    # Spotfaces keep the forged neck out of the thrust-washer seating planes.
    for sign in [-1,1]:h.drill(leg,.0125,.014,root,top+axis*(sign*(.0091+.007)),axis*sign)
    upper_washers=[]
    for sign in [-1,1]:upper_washers.append(h.sleeve(pre+'UpperThrust_'+str(sign),.0122,.00435,.0018,root,top+axis*(sign*.0102),'A_Bronze',axis).name)
    inlays=[]
    for j,distance in enumerate([.100,length-.095]):
        location=top+direction*distance;tool=h.sleeve(pre+'GrooveTool',.033,.0260,.0058,root,location,'A_Dark',direction);g.boolean(leg,tool,'DIFFERENCE');ring=h.sleeve(pre+'BronzeInlay_%d'%j,.0276,.0262,.0054,root,location,'A_Bronze',direction);ring.data.materials.append(red)
        for face in ring.data.polygons:
            if face.index in [8,9]:face.material_index=1
        inlays.append(ring.name)
    shoe_frame,radial,tangent=g.foot_frame(pre+'ShoeFrame',foot,axis,deck_top,deck_center);bpy.context.view_layer.update();shoe,gasket=g.formed_foot(pre+'FormedShoe',references[deck.name],shoe_frame);fork_frame,cheeks=g.foot_fork(pre+'FootFork',foot,axis,deck_top+.0182)
    for cheek in cheeks:g.boolean(shoe,cheek)
    lower_washers=[]
    for sign in [-1,1]:
        lower_washers.append(h.sleeve(pre+'LowerThrust_'+str(sign),.012,.0060,.0008,root,foot+axis*(sign*.0155),'A_Bronze',axis).name)
        h.sleeve(pre+'FootBush_'+str(sign),.00618,.0060,.0060,root,foot+axis*(sign*.019),'A_Bronze',axis)
    pin=h.cylinder(pre+'FootPin',.0058,.0508,root,foot,'A_Nickel',axis,.0001)
    for sign in [-1,1]:
        h.sleeve(pre+'FootPinWasher_'+str(sign),.0105,.0060,.0012,root,foot+axis*(sign*.0227),'A_Bronze',axis)
        head=h.screw(pre+'FootPinCap_'+str(sign),root,foot+axis*(sign*.0254),.0095,axis*sign);g.boolean(pin,head)
    for sign in [-1,1]:
        xy=Vector((foot.x,foot.y,0))+tangent*(sign*.052);head_plane=deck_top+.0182;h.drill(shoe,.0032,.08,root,(xy.x,xy.y,head_plane-.020));h.drill(gasket,.0032,.04,root,(xy.x,xy.y,deck_top));h.drill(deck,.0032,.032,root,(xy.x,xy.y,deck_top-.015))
        washer=h.sleeve(pre+'DeckWasher_'+str(sign),.0060,.00325,.0012,root,(xy.x,xy.y,head_plane+.0007),'A_Bronze');head_center=head_plane+.0034;bottom=deck_top-.025;bolt=h.cylinder(pre+'DeckBolt_'+str(sign),.00285,head_center-bottom,root,(xy.x,xy.y,(head_center+bottom)/2),'A_Nickel',bevel=.0001);head=h.screw(pre+'DeckBoltHead_'+str(sign),root,(xy.x,xy.y,head_center),.0058);g.boolean(bolt,head);fasteners.append({'mesh':bolt.name,'target':deck.name,'xy':[xy.x,xy.y],'shaft_bottom_z':bottom,'expected_blind_floor_z':deck_top-.031,'deck_top_z':deck_top})
    section=next(r for r in sections['rows'] if r['anchor']==row['anchor']);port_frame=h.empty(pre+'PortFrame',root);port_frame.matrix_world=Matrix(section['matrix_blender']);bpy.context.view_layer.update();skins=[bpy.data.objects[n] for n in section['source_skins']];skin_refs=[references[n] for n in section['source_skins']]
    depth_values=[hit['depth'] for sample in section['samples'] if sample['radius']<=.036 for hit in sample['hits']];start=min(depth_values)-.003;end=max(depth_values)+.006
    lip,lip_fit=g.formed_port_lip(pre+'FormedPortLip',skin_refs,port_frame)
    liner=h.sleeve(pre+'PortLiner',.0336,.0295,end-start,port_frame,(0,0,(start+end)/2),'A_Satin');g.boolean(liner,lip)
    h.drill(liner,.0306,.010,port_frame,(0,0,end-.003));seal=h.sleeve(pre+'PortSeal',.0304,.0280,.0055,port_frame,(0,0,end-.0037),'A_Rubber')
    for skin in skins:h.drill(skin,.0340,length+.10,port_frame,(0,0,length/2))
    ports.append({'frame':port_frame.name,'matrix_blender':[list(r) for r in port_frame.matrix_world],'liner':liner.name,'seal':seal.name,'skins':section['source_skins'],'source_lip_fit':lip_fit,'shaft_clearance_radius':.0295,'cut_radius':.0340,'liner_outer_radius':.0336,'axial_limits':[start,end]})
    supports.append({**row,'body':leg.name,'shoe':shoe.name,'shoe_gasket':gasket.name,'shoe_frame':shoe_frame.name,'foot_pin':pin.name,'upper_thrust_washers':upper_washers,'lower_thrust_washers':lower_washers,'inlays':inlays,'top_eye_radius':.0145,'top_eye_bore':.00435,'top_eye_width':.0184,'foot_eye_bore':.0061,'foot_pin_radius':.0058,'foot_shoe_top_z':deck_top+.0182});print('TRUNNION_SUPPORT_BUILT',index+1,flush=True)
for ref in references.values():bpy.data.objects.remove(ref,do_unlink=True)
cleanup=[]
for name in list(h.parts)+sorted(allowed):
    o=bpy.data.objects.get(name)
    if o is None or o.type!='MESH':continue
    bm=bmesh.new();bm.from_mesh(o.data);boundary_vertices=[v for v in bm.verts if any(e.is_boundary for e in v.link_edges)]
    if boundary_vertices:bmesh.ops.remove_doubles(bm,verts=boundary_vertices,dist=2e-7)
    bmesh.ops.remove_doubles(bm,verts=list(bm.verts),dist=1e-7);bmesh.ops.dissolve_degenerate(bm,edges=list(bm.edges),dist=1e-7);repair=residue.repair(bm);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces))
    if bm.calc_volume(signed=True)<0:bmesh.ops.reverse_faces(bm,faces=list(bm.faces))
    cleanup.append({'mesh':name,'nonmanifold_edges':sum(not e.is_manifold for e in bm.edges),'tiny_faces':sum(f.calc_area()<1e-12 for f in bm.faces),'signed_volume':bm.calc_volume(signed=True),**repair});bm.to_mesh(o.data);bm.free()
for name,materials in source_materials.items():
    mesh=bpy.data.objects[name].data
    for face in mesh.polygons:
        if face.material_index>=len(materials):face.material_index=0
    mesh.materials.clear()
    for material in materials:mesh.materials.append(material)
bpy.context.view_layer.update();changed=[n for n,value in protected.items() if fingerprint(bpy.data.objects[n])!=value];assert not changed,changed
bpy.ops.wm.save_as_mainfile(filepath=str(TARGET),compress=True);bpy.ops.object.select_all(action='DESELECT')
for o in [body,*body.children_recursive]:o.select_set(True)
bpy.context.view_layer.objects.active=body;bpy.ops.export_scene.gltf(filepath=str(COMPONENT),export_format='GLB',use_selection=True,export_animations=False,export_morph=False,export_extras=True)
r={**seed,'source':str(TARGET.relative_to(ROOT)),'source_sha256':sha(TARGET),'component':str(COMPONENT.relative_to(ROOT)),'component_sha256':sha(COMPONENT),'parent_source_sha256':seed['source_sha256'],'metal_supports':{'root':root.name,'supports':supports,'ports':ports,'deck_fasteners':fasteners,'new_meshes':list(h.parts),'modified_meshes':sorted(allowed),'source_shapes':source_shapes,'cleanup':cleanup,'route_plan':'review/I_refinement/nautilus_r1/trunnion_support_r18/route_r2/route_plan.json','art':'production/I_refinement/nautilus_r1/trunnion_support_r18/trunnion_and_foot_finish_r1.png'},'status':'formed_trunnion_support_candidate_checks_pending','review_scope':'Two real metal struts use existing collar pins and the existing device deck. Fitted foot soles, actual pins/eyes, machined inlays, shaped port lips and source shell passages built. Joint contact, port fit, outside-skin preservation, motion, final finish and native/art acceptance remain pending.'}
(OUT/'build.json').write_text(json.dumps(r,indent=2)+'\n');(OUT/'protected_geometry.json').write_text(json.dumps({'source_sha256':r['source_sha256'],'passed':not changed,'protected_mesh_count':len(protected),'allowed_changes':sorted(allowed),'changed_protected':changed},indent=2)+'\n');print('TRUNNION_SUPPORT_SOURCE',r['source_sha256'],flush=True)
