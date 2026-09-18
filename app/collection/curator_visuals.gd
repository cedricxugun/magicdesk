extends Node3D
## Optical capture and fabrication use real 3D paths and authored intensity maps.
var module:Node3D
var player:RefCounted
var atlas:Texture2D
var strands:Texture2D
var groove_texture:Texture2D
var force_warm:=false
var print_root:Node3D
var surface_sets:Array=[]
var heights:Array=[]
var wires:Array=[]
var paths:Array=[]
var capture_lines:Array=[]
var feed_lines:Array=[]
var contacts:Array=[]
var spark_mesh:MultiMeshInstance3D
var groove:MeshInstance3D
var scan_line:MeshInstance3D
var lamp:OmniLight3D
var accent:OmniLight3D
var capture_lamp:OmniLight3D
var face_lamp:OmniLight3D
var field_volume:MeshInstance3D
var gold:=Color(1.,.57,.20)
var blue:=Color(.19,.57,1.)
var seam:=Color(1.,.84,.57)
var effect_levels:={"capture":0.,"read":0.,"build":0.,"wire":0.,"particles":0.}
var glints:Array=[]
var glint_atlas:Texture2D
var flow_phase:=0.0
var observatory_performance:Node3D
var butterfly_fabrication:Node3D
var ship_fabrication:Node3D

func glint_material(instanced:bool=false)->ShaderMaterial:
	var mat:=ShaderMaterial.new();mat.shader=load("res://collection/curator_glint.gdshader");mat.set_shader_parameter("atlas",glint_atlas);mat.set_shader_parameter("instanced",instanced);return mat

func light_material(color:Color)->ShaderMaterial:
	var m:=ShaderMaterial.new();m.shader=load("res://collection/curator_light.gdshader");m.set_shader_parameter("pattern",strands);m.set_shader_parameter("color",Vector3(color.r,color.g,color.b));return m
func line(radius:float,color:Color)->MeshInstance3D:
	var mesh:=MeshInstance3D.new();var cylinder:=CylinderMesh.new();cylinder.top_radius=radius;cylinder.bottom_radius=radius;cylinder.height=1;cylinder.radial_segments=6;mesh.mesh=cylinder;mesh.material_override=light_material(color);mesh.cast_shadow=GeometryInstance3D.SHADOW_CASTING_SETTING_OFF;add_child(mesh);return mesh
func segment(node:MeshInstance3D,a:Vector3,b:Vector3,gain:float)->void:
	var direction:=b-a;node.visible=gain>.002 and direction.length_squared()>.0000001
	if not node.visible:return
	node.global_transform=Transform3D(Basis(Quaternion(Vector3.UP,direction.normalized()))*Basis.from_scale(Vector3(1,direction.length(),1)),(a+b)*.5)
	node.material_override.set_shader_parameter("gain",gain);node.material_override.set_shader_parameter("time",player.time)
func prepare(node:Node,materials:Array,root:Node3D,height:Array)->void:
	if node is MeshInstance3D:
		var box:AABB=node.mesh.get_aabb();var transform:Transform3D=root.global_transform.affine_inverse()*node.global_transform
		for i in range(8):height[0]=maxf(float(height[0]),(transform*box.get_endpoint(i)).y)
		for s in range(node.mesh.get_surface_count()):
			var original:Material=node.get_active_material(s)
			if original is ShaderMaterial:
				var m:ShaderMaterial=original.duplicate();node.set_surface_override_material(s,m);m.set_shader_parameter("record_print",true);materials.append(m);module.materials.append(m)
	for child in node.get_children():
		if not child is StaticBody3D:prepare(child,materials,root,height)
func setup(owner:Node3D)->void:
	module=owner;player=module.play.g_instrument
	strands=load("res://assets/collection/art/G_AI/field_strands.png");atlas=strands;groove_texture=load("res://assets/collection/art/G_AI/groove_traces.png")
	glint_atlas=load("res://assets/collection/art/G_AI/optical_field_atlas.png")
	print_root=module.named(module.data.record_player.print_root)
	for i in range(player.content.size()):
		var materials:Array=[];var height:Array=[.1];prepare(player.content[i].node,materials,print_root,height);surface_sets.append(materials);heights.append(float(height[0])+.012)
		var edges:Array=module.data.g_archive.contents[i].get("structure_edges",[])
		var wire:=MultiMeshInstance3D.new();var mm:=MultiMesh.new();mm.transform_format=MultiMesh.TRANSFORM_3D;var cylinder:=CylinderMesh.new();cylinder.height=1;cylinder.top_radius=.0023;cylinder.bottom_radius=.0023;cylinder.radial_segments=4;mm.mesh=cylinder;mm.instance_count=edges.size();wire.multimesh=mm
		var mat:=light_material(blue);mat.set_shader_parameter("print_wire",true);wire.material_override=mat;wire.cast_shadow=GeometryInstance3D.SHADOW_CASTING_SETTING_OFF;print_root.add_child(wire)
		var targets:Array=[]
		for j in range(edges.size()):
			var a:Vector3=module.v3(edges[j][0]);var b:Vector3=module.v3(edges[j][1]);var d:=b-a
			mm.set_instance_transform(j,Transform3D(Basis(Quaternion(Vector3.UP,d.normalized()))*Basis.from_scale(Vector3(1,maxf(.00001,d.length()),1)),(a+b)*.5))
			if j%maxi(1,edges.size()/100)==0:targets.append((a+b)*.5)
		wires.append(wire);paths.append(targets)
	if player.observatory_enabled and not get_tree().has_meta("observatory_material_baseline"):
		load("res://collection/observatory_materials.gd").apply(surface_sets[0])
	for i in range(18):capture_lines.append(line(.0024 if i%3 else .0030,gold))
	field_volume=MeshInstance3D.new();var cone:=CylinderMesh.new();cone.top_radius=.036;cone.bottom_radius=.185;cone.height=1.;cone.radial_segments=64;cone.rings=12;cone.cap_top=false;cone.cap_bottom=false;field_volume.mesh=cone
	var field_mat:=ShaderMaterial.new();field_mat.shader=load("res://collection/curator_field_volume.gdshader");field_mat.set_shader_parameter("strands",strands);field_volume.material_override=field_mat;field_volume.cast_shadow=GeometryInstance3D.SHADOW_CASTING_SETTING_OFF;add_child(field_volume)
	for i in range(6*12):
		var strand:=line(.0036,seam);strand.material_override.set_shader_parameter("path_start",float(i%12)/12.0);strand.material_override.set_shader_parameter("path_span",1./12.)
		feed_lines.append(strand)
	for i in range(6):
		var contact:=MeshInstance3D.new();var ring:=TorusMesh.new();ring.inner_radius=.021;ring.outer_radius=.025;ring.rings=24;ring.ring_segments=6;contact.mesh=ring;contact.material_override=light_material(gold);contact.cast_shadow=GeometryInstance3D.SHADOW_CASTING_SETTING_OFF;add_child(contact);contacts.append(contact)
	groove=MeshInstance3D.new();var quad:=QuadMesh.new();quad.size=Vector2(.83,.83);groove.mesh=quad;var mat:=ShaderMaterial.new();mat.shader=load("res://collection/curator_groove.gdshader");mat.set_shader_parameter("traces",groove_texture);groove.material_override=mat;groove.cast_shadow=GeometryInstance3D.SHADOW_CASTING_SETTING_OFF;add_child(groove)
	scan_line=line(.003,seam)
	spark_mesh=MultiMeshInstance3D.new();var mm:=MultiMesh.new();mm.transform_format=MultiMesh.TRANSFORM_3D;mm.use_custom_data=true;var particle:=QuadMesh.new();particle.size=Vector2(.035,.035);mm.mesh=particle;mm.instance_count=144;spark_mesh.multimesh=mm
	mat=glint_material(true);spark_mesh.material_override=mat;spark_mesh.cast_shadow=GeometryInstance3D.SHADOW_CASTING_SETTING_OFF;add_child(spark_mesh)
	for i in range(13):
		var glint:=MeshInstance3D.new();var q:=QuadMesh.new();q.size=Vector2(.16,.16);glint.mesh=q;glint.material_override=glint_material();glint.cast_shadow=GeometryInstance3D.SHADOW_CASTING_SETTING_OFF;add_child(glint);glints.append(glint)
	lamp=OmniLight3D.new();lamp.light_color=gold;lamp.omni_range=.65;add_child(lamp)
	accent=OmniLight3D.new();accent.light_color=seam;accent.omni_range=.85;add_child(accent)
	capture_lamp=OmniLight3D.new();capture_lamp.light_color=gold;capture_lamp.omni_range=.55;add_child(capture_lamp)
	face_lamp=OmniLight3D.new();face_lamp.light_color=Color(1.,.46,.08);face_lamp.omni_range=.28;face_lamp.shadow_enabled=true;face_lamp.shadow_bias=.01;face_lamp.shadow_normal_bias=.005;face_lamp.light_size=.018;face_lamp.light_specular=0.;add_child(face_lamp)
	if player.observatory_enabled:
		observatory_performance=load("res://collection/observatory_performance.gd").new();add_child(observatory_performance);observatory_performance.setup(module,surface_sets[0])
	if player.butterfly_drive:
		if not get_tree().has_meta("butterfly_finish_baseline"):
			load("res://collection/finish_profile.gd").apply(surface_sets[1],"res://assets/collection/butterfly_materials.json","butterfly_finish")
		butterfly_fabrication=load("res://collection/butterfly_fabrication.gd").new();add_child(butterfly_fabrication);butterfly_fabrication.setup(module)
	if player.ship_drive:
		ship_fabrication=load("res://collection/ship_fabrication.gd").new();add_child(ship_fabrication);ship_fabrication.setup(module)
	tick(0,0)

func tick(delta:float,_quiet:float)->void:
	if observatory_performance:observatory_performance.tick(delta,force_warm)
	var active:float=module.power*(1-module.explosion)
	var index:int=maxi(0,player.loaded_index);var progress:float=player.print_amount
	var capture:float=player.beam_gain*active
	var reading:float=1.0 if player.stage=="reading" else 0.0
	var printing:float=1.0 if player.stage in ["printing","erasing"] else 0.0
	# Reversing changes velocity, not absolute phase: no jump when a user
	# cancels halfway through formation or starts returning a finished object.
	if printing>0.:flow_phase+=minf(delta,.2)*.48*(-1.0 if player.stage=="erasing" else 1.0)
	var releasing:bool=player.stage in ["releasing_field","return_release"]
	var locking:bool=player.stage in ["locking_optical_field","return_lock_field"]
	var capture_span:float=capture if releasing else 1.0
	var contact_gain:float=capture*smoothstep(.40,.85,capture) if releasing else smoothstep(0.,.28,capture)*active if locking else capture
	var strand_gain:float=smoothstep(.16,.80,capture)*active if locking else capture
	var volume_gain:float=smoothstep(.35,1.,capture)*active if locking else capture
	var climax:float=exp(-pow((progress-.77)/.16,2))
	var building:float=printing*smoothstep(0.,.07,progress)*(1.-smoothstep(.88,1.,progress))*active
	if force_warm:capture=1.;reading=1.;building=1.;progress=.5;contact_gain=1.;strand_gain=1.;volume_gain=1.;capture_span=1.
	var physical_progress:float=player.physical_print_progress()
	var wire_reveal:float=smoothstep(.0,.35,progress)
	effect_levels={"capture":capture,"capture_contacts":contact_gain,"capture_span":capture_span,"read":reading*active,"build":building,"wire":building,"particles":building*(.25+climax)}
	var origin:Vector3=print_root.global_position;var basis:Basis=print_root.global_basis.orthonormalized()
	# Read/write contacts sit above the actual enlarged original record. The
	# print pivot is below that surface and must not be used as a decal plane.
	var disc:Node3D=player.media[index]
	var disc_surface:Vector3=disc.global_position+disc.global_basis.orthonormalized().y*(float(module.data.record_player.record_thickness)*.5+.0015)
	var disc_local_height:float=print_root.to_local(disc_surface).y
	var camera:=get_viewport().get_camera_3d();var facing:Basis=camera.global_basis if camera else Basis.IDENTITY
	var screen:Node3D=module.named(module.data.optical_curator.screen)
	face_lamp.global_position=screen.to_global(Vector3(0,0,.185));face_lamp.light_energy=module.power*.045*(.12+.88*player.iris_open)
	for i in range(surface_sets.size()):
		for mat in surface_sets[i]:
			mat.set_shader_parameter("print_progress",physical_progress if i==index else 0.);mat.set_shader_parameter("print_height",heights[i]);mat.set_shader_parameter("print_origin",origin);mat.set_shader_parameter("print_x",basis.x);mat.set_shader_parameter("print_y",basis.y);mat.set_shader_parameter("print_z",basis.z);mat.set_shader_parameter("print_power",active);mat.set_shader_parameter("build_gain",.45+climax*1.8)
		wires[i].visible=(i==index and building>.002) or force_warm
		var mat:ShaderMaterial=wires[i].material_override;mat.set_shader_parameter("origin",origin);mat.set_shader_parameter("up",basis.y);mat.set_shader_parameter("height",heights[i]);mat.set_shader_parameter("progress",physical_progress);mat.set_shader_parameter("reveal",wire_reveal);mat.set_shader_parameter("gain",building*1.1);mat.set_shader_parameter("time",player.time)
		if force_warm:player.content[i].node.show()
	if butterfly_fabrication:
		paths[1]=butterfly_fabrication.tick(building if index==1 else 0.,flow_phase/.48,force_warm);wires[1].visible=false
	if ship_fabrication:
		paths[2]=ship_fabrication.tick(building if index==2 else 0.,flow_phase/.48,force_warm);wires[2].visible=false
	var emitter:Node3D=module.named(module.data.optical_curator.emitter)
	var record_basis:=Basis(player.wrist_q);var record_center:Vector3=module.to_global(player.wrist_virtual);var world_basis:Basis=module.global_basis*record_basis
	for i in range(capture_lines.size()):
		var a:=i/18.0*TAU;var destination:Vector3=record_center+world_basis*Vector3(cos(a)*.185,.015,sin(a)*.185)
		var source:Vector3=emitter.global_position+world_basis*Vector3(cos(a)*.033,0,sin(a)*.033)
		segment(capture_lines[i],source,source.lerp(destination,capture_span),strand_gain*(.55 if i%3 else .9))
	for i in range(6):
		var a:=i/6.0*TAU;contacts[i].global_transform=Transform3D(world_basis,record_center+world_basis*Vector3(cos(a)*.185,.015,sin(a)*.185));contacts[i].visible=contact_gain>.002;contacts[i].material_override.set_shader_parameter("gain",contact_gain)
		glints[i].global_transform=Transform3D(facing,contacts[i].global_position+world_basis.y*.003);glints[i].visible=contact_gain>.002;glints[i].material_override.set_shader_parameter("gain",contact_gain*.85)
	capture_lamp.global_position=record_center+world_basis.y*.075;capture_lamp.light_energy=contact_gain*.30
	var destination:Vector3=emitter.global_position.lerp(record_center+world_basis.y*.015,capture_span);var field_axis:Vector3=emitter.global_position-destination
	field_volume.visible=capture>.002 and field_axis.length()>.001
	if field_volume.visible:
		field_volume.global_transform=Transform3D(Basis(Quaternion(Vector3.UP,field_axis.normalized()))*Basis.from_scale(Vector3(1,field_axis.length(),1)),(destination+emitter.global_position)*.5)
		field_volume.material_override.set_shader_parameter("strength",volume_gain);field_volume.material_override.set_shader_parameter("clock",player.time);field_volume.material_override.set_shader_parameter("length_fraction",capture_span)
	var scan:Node3D=module.named(module.data.record_player.scan_point)
	var on_disc:Vector3=scan.global_position-basis.y*((scan.global_position-disc_surface).dot(basis.y))
	segment(scan_line,scan.global_position,on_disc,reading*active*1.3)
	glints[12].global_transform=Transform3D(facing,on_disc+basis.y*.004);glints[12].visible=reading*active>.002;glints[12].material_override.set_shader_parameter("gain",reading*active*1.2)
	groove.global_transform=Transform3D(basis*Basis(Vector3.RIGHT,-PI/2),disc_surface);groove.visible=reading*active>.002
	groove.material_override.set_shader_parameter("gain",reading*active*1.4);groove.material_override.set_shader_parameter("progress",player.read_progress);groove.material_override.set_shader_parameter("rotation",player.platter_angle)
	var ship_feed:bool=ship_fabrication!=null and index==2
	var butterfly_feed:bool=butterfly_fabrication!=null and index==1
	var endpoints:Array=[]
	for i in range(6):
		var angle:=i/6.0*TAU;var start:=Vector3(.36*cos(angle),disc_local_height+.001,.36*sin(angle));var desired:=Vector3(.23*cos(angle),maxf(.06,physical_progress)*float(heights[index]),.23*sin(angle))
		var best:=INF;var end:Vector3=desired
		for point in paths[index]:
			var score:float=absf(point.y-desired.y)*2.0+Vector2(point.x-desired.x,point.z-desired.z).length()
			if score<best:best=score;end=point
		if butterfly_feed:
			start=Vector3(-.12 if i%2==0 else .12,disc_local_height+.001,0);end=Vector3(-.023 if i%2==0 else .023,.07225,0)
		if ship_feed:
			start=Vector3(-.11 if i%2==0 else .11,disc_local_height+.001,0);end=Vector3(-.04 if i%2==0 else .04,.03425,0)
		var feed_gain:float=building*(.14 if ship_feed and i<2 else 0.0 if ship_feed else .24 if butterfly_feed and i<2 else 0.0 if butterfly_feed else 1.0)
		endpoints.append([start,end])
		glints[6+i].global_transform=Transform3D(facing,print_root.to_global(end));glints[6+i].visible=feed_gain>.002;glints[6+i].material_override.set_shader_parameter("gain",feed_gain*(.75+climax*1.4))
		for j in range(12):
			var from:=feed_point(start,end,j/12.0);var to:=feed_point(start,end,(j+1)/12.0)
			segment(feed_lines[i*12+j],print_root.to_global(from),print_root.to_global(to),feed_gain*(.65+climax))
			feed_lines[i*12+j].material_override.set_shader_parameter("color",Vector3(1.,.38,.04) if butterfly_feed else Vector3(seam.r,seam.g,seam.b))
			feed_lines[i*12+j].material_override.set_shader_parameter("time",flow_phase/.48)
	for i in range(144):
		var path:Array=endpoints[i%6];var t:float=fposmod(flow_phase+float(i)/144,1);var point:Vector3=feed_point(path[0],path[1],t)
		spark_mesh.multimesh.set_instance_transform(i,Transform3D(facing,print_root.to_global(point)))
		spark_mesh.multimesh.set_instance_custom_data(i,Color(building*(.25+climax)*sin(t*PI)*(.10 if ship_feed else .18 if butterfly_feed else 1.0),0,0,0))
	spark_mesh.visible=building>.002;spark_mesh.material_override.set_shader_parameter("gain",1.);spark_mesh.material_override.set_shader_parameter("time",player.time)
	lamp.global_position=on_disc+basis.y*.04;lamp.light_energy=reading*active*.22
	accent.global_position=origin+basis.y*(physical_progress*float(heights[index]))+basis.z*.18;accent.light_energy=building*(.04+climax*.08 if ship_feed else .1+climax*.45)

func feed_point(start:Vector3,end:Vector3,t:float)->Vector3:
	return start.lerp(end,t)+Vector3(0,sin(t*PI)*.045,0)
func state()->Dictionary:
	return {"print":player.print_amount,"loaded":player.loaded_index,"heights":heights,"levels":effect_levels,"flow_phase":flow_phase,"flow_direction":-1 if player.stage=="erasing" else 1 if player.stage=="printing" else 0,"wire_edges":wires.map(func(w):return w.multimesh.instance_count),"ship":ship_fabrication.state() if ship_fabrication else {},"observatory":observatory_performance.state() if observatory_performance else {}}
