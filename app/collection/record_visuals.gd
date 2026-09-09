extends Node3D
## Authored optical atlas and actual gold skeletons form the print effect.
## Print coordinates are attached to the same pivot as the physical record.
var module:Node3D
var player:RefCounted
var atlas:Texture2D
var force_warm:=false
var surface_sets:Array=[]
var heights:Array[float]=[]
var print_root:Node3D
var scan:MeshInstance3D
var layer:MeshInstance3D
var seed:MeshInstance3D
var filament:MeshInstance3D
var sparks:MultiMeshInstance3D
var lamp:OmniLight3D
var accent:OmniLight3D
var read_sound:AudioStreamPlayer
var last_cycle:=0
func material(tile:int)->ShaderMaterial:
	var m:=ShaderMaterial.new();m.shader=load("res://collection/g_atlas.gdshader");m.set_shader_parameter("atlas",atlas);m.set_shader_parameter("tile",float(tile));return m
func quad(tile:int)->MeshInstance3D:
	var n:=MeshInstance3D.new();var mesh:=QuadMesh.new();mesh.size=Vector2.ONE;n.mesh=mesh;n.material_override=material(tile);n.cast_shadow=GeometryInstance3D.SHADOW_CASTING_SETTING_OFF;add_child(n);return n
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
	top_level=true;global_transform=Transform3D.IDENTITY;module=owner;player=module.play.g_instrument;atlas=load(str(module.data.record_player.source_atlas));print_root=module.named(module.data.record_player.print_root)
	for item in player.content:
		var materials:Array=[];var height:Array=[.1];prepare(item.node,materials,print_root,height);surface_sets.append(materials);heights.append(float(height[0])+.025)
	scan=quad(2);layer=quad(0);seed=quad(2);filament=quad(1)
	sparks=MultiMeshInstance3D.new();var mm:=MultiMesh.new();mm.transform_format=MultiMesh.TRANSFORM_3D;mm.use_custom_data=true;var mesh:=QuadMesh.new();mesh.size=Vector2(.045,.045);mm.mesh=mesh;mm.instance_count=32;sparks.multimesh=mm
	var spark_material:=material(2);spark_material.set_shader_parameter("instanced",true);spark_material.set_shader_parameter("gain",1.0);sparks.material_override=spark_material;sparks.cast_shadow=GeometryInstance3D.SHADOW_CASTING_SETTING_OFF;add_child(sparks)
	lamp=OmniLight3D.new();lamp.light_color=Color(1,.40,.14);lamp.omni_range=.85;lamp.shadow_enabled=false;add_child(lamp)
	accent=OmniLight3D.new();accent.light_color=Color(1,.65,.34);accent.omni_range=1.1;accent.shadow_enabled=false;add_child(accent)
	read_sound=AudioStreamPlayer.new();read_sound.stream=load("res://assets/collection/art/G/inscription.wav");read_sound.volume_db=-23;add_child(read_sound)
func gain(n:MeshInstance3D,value:float)->void:n.visible=value>.002;n.material_override.set_shader_parameter("gain",value)
func segment(n:MeshInstance3D,a:Vector3,b:Vector3,width:float)->void:
	if a.distance_squared_to(b)<.00000001:n.global_transform=Transform3D(Basis.from_scale(Vector3(.0001,width,1)),a);return
	var x:Vector3=(b-a).normalized();var z:Vector3=(module.host.camera.global_position-(a+b)*.5).normalized();var y:=z.cross(x).normalized();n.global_transform=Transform3D(Basis(x*(b-a).length()*1.22,y*width,x.cross(y)),(a+b)*.5)
func tick(_delta:float,quiet_gain:float)->void:
	var active:float=module.power*(1-module.explosion)
	var reading:float=1.0 if player.stage=="reading" else 0.0
	var printing:float=1.0 if player.stage in ["printing","erasing"] else 0.0
	var index:int=maxi(0,player.loaded_index);var progress:float=player.print_amount
	if force_warm:active=1;reading=1;printing=1;progress=.5
	var basis:Basis=print_root.global_basis.orthonormalized();var origin:Vector3=print_root.global_position
	for i in range(surface_sets.size()):
		for m in surface_sets[i]:
			m.set_shader_parameter("print_progress",progress if i==index else 0.0);m.set_shader_parameter("print_height",heights[i]);m.set_shader_parameter("print_origin",origin);m.set_shader_parameter("print_x",basis.x);m.set_shader_parameter("print_y",basis.y);m.set_shader_parameter("print_z",basis.z);m.set_shader_parameter("print_power",active);m.set_shader_parameter("power",active)
		if force_warm:player.content[i].node.show()
	var needle:Node3D=module.named(module.data.record_player.scan_point)
	scan.global_transform=Transform3D(module.host.camera.global_basis*Basis.from_scale(Vector3.ONE*.14),needle.global_position)
	gain(scan,active*reading*1.4)
	var h:float=progress*heights[index];var tip:Vector3=origin+basis.y*h
	layer.global_transform=Transform3D(basis*Basis(Vector3.RIGHT,-PI/2)*Basis.from_scale(Vector3(1.0,1.0,1.0)),tip)
	gain(layer,active*printing*(.35+.45*sin(clampf(progress,0,1)*PI)))
	seed.global_transform=Transform3D(module.host.camera.global_basis*Basis.from_scale(Vector3.ONE*.11),origin)
	gain(seed,active*(reading*.35+printing*.55))
	segment(filament,origin,tip,.09);gain(filament,active*printing*.27)
	for i in range(32):
		var a:float=i*2.39996+player.platter_angle;var t:float=fposmod(player.time*.55+float(i)/32,1)
		var radius:float=.16+.24*float(i%7)/6;var point:=tip+module.global_basis*Vector3(radius*cos(a),t*.10,radius*sin(a))
		sparks.multimesh.set_instance_transform(i,Transform3D(module.host.camera.global_basis,point));sparks.multimesh.set_instance_custom_data(i,Color(active*printing*(1-t)*.40,0,0,0))
	sparks.visible=printing>.001
	lamp.global_position=needle.global_position;lamp.light_energy=active*reading*.28
	accent.global_position=origin+basis.y*.25+module.global_basis*Vector3(.2,.1,.22);accent.light_energy=active*(printing*.24+player.display_amount*.15+player.action_energy*.14)
	if player.cycle_count>last_cycle:
		last_cycle=player.cycle_count
		if not module.host.muted and not force_warm:read_sound.play()
	if module.host.muted:read_sound.stop()
	read_sound.volume_db=-23+linear_to_db(maxf(.001,active*quiet_gain))
func pack(t:Transform3D)->Dictionary:
	var q:=t.basis.get_rotation_quaternion();var s:=t.basis.get_scale();return {"p":[t.origin.x,t.origin.y,t.origin.z],"q":[q.x,q.y,q.z,q.w],"s":[s.x,s.y,s.z]}
func state()->Dictionary:
	var quads:Array=[]
	for n in [scan,layer,seed,filament]:quads.append({"pose":pack(n.global_transform),"tile":n.material_override.get_shader_parameter("tile"),"gain":n.material_override.get_shader_parameter("gain")})
	return {"quads":quads,"print":player.print_amount,"loaded":player.loaded_index,"heights":heights}
