extends Node3D
## Sealed-window reading and reconstruction on a real platen. The six authored
## solid miniatures carry the result; optical art only connects the actions.
var module:Node3D
var instrument:RefCounted
var atlas:Texture2D
var force_warm:=false
var scans:Array=[]
var contacts:Array=[]
var transfer:MeshInstance3D
var platen:MeshInstance3D
var glints:MultiMeshInstance3D
var light:OmniLight3D
var sound:AudioStreamPlayer
var heard_action:=0
var content_materials:Array=[]

func mat(tile:int)->ShaderMaterial:
	var material:=ShaderMaterial.new();material.shader=load("res://collection/g_atlas.gdshader");material.set_shader_parameter("atlas",atlas);material.set_shader_parameter("tile",float(tile));return material
func quad(tile:int)->MeshInstance3D:
	var o:=MeshInstance3D.new();var mesh:=QuadMesh.new();mesh.size=Vector2.ONE;o.mesh=mesh;o.material_override=mat(tile);o.cast_shadow=GeometryInstance3D.SHADOW_CASTING_SETTING_OFF;add_child(o);return o
func setup(owner:Node3D)->void:
	top_level=true;global_transform=Transform3D.IDENTITY;module=owner;instrument=module.play.g_instrument;atlas=load(str(module.data.g_archive.atlas))
	for i in range(6):scans.append(quad(1));contacts.append(quad(0))
	transfer=quad(1);platen=quad(0)
	light=OmniLight3D.new();light.light_color=Color(1,.66,.33);light.omni_range=1.1;light.shadow_enabled=false;add_child(light)
	glints=MultiMeshInstance3D.new();var multi:=MultiMesh.new();multi.transform_format=MultiMesh.TRANSFORM_3D;multi.use_custom_data=true
	var mesh:=QuadMesh.new();mesh.size=Vector2(.045,.045);multi.mesh=mesh;multi.instance_count=36;glints.multimesh=multi
	var material:=mat(2);material.set_shader_parameter("instanced",true);material.set_shader_parameter("gain",1.0);glints.material_override=material;glints.cast_shadow=GeometryInstance3D.SHADOW_CASTING_SETTING_OFF;add_child(glints)
	for item in instrument.content:
		var materials:Array=[];prepare_materials(item.node,materials);content_materials.append(materials)
	sound=AudioStreamPlayer.new();sound.stream=load("res://assets/collection/art/G/inscription.wav");sound.volume_db=-23;add_child(sound)

func prepare_materials(node:Node,materials:Array)->void:
	if node is MeshInstance3D:
		for s in range(node.mesh.get_surface_count()):
			var original:Material=node.get_active_material(s)
			if original is ShaderMaterial:
				var material:ShaderMaterial=original.duplicate();node.set_surface_override_material(s,material);materials.append(material);module.materials.append(material)
	for child in node.get_children():
		if not child is StaticBody3D:prepare_materials(child,materials)
func gain(o:MeshInstance3D,amount:float)->void:o.visible=amount>.002;o.material_override.set_shader_parameter("gain",amount)
func segment(o:MeshInstance3D,a:Vector3,b:Vector3,width:float)->void:
	var x:Vector3=(b-a).normalized();var z:Vector3=(module.host.camera.global_position-(a+b)*.5).normalized();var y:=z.cross(x).normalized()
	o.global_transform=Transform3D(Basis(x*(b-a).length()*1.22,y*width,x.cross(y)),(a+b)*.5)
func tick(_delta:float,quiet_gain:float)->void:
	var active:float=module.power*(1-module.explosion)*quiet_gain
	var reading:float=1.0 if instrument.stage=="reading" else 0.0
	var forming:float=sin(instrument.display_amount*PI)
	var selected:int=instrument.selected;var platform:Node3D=module.named(module.data.g_archive.platform)
	if force_warm:active=1;reading=1;forming=1
	for i in range(6):
		var leaf:Dictionary=instrument.leaves[i];var writer:Node3D=leaf.writer;var side:float=leaf.side
		segment(scans[i],writer.to_global(Vector3(.255,0,.146*side)),writer.to_global(Vector3(.685,0,.146*side)),.12)
		gain(scans[i],active*(1.25*reading if i==selected else 0.0))
		contacts[i].global_transform=leaf.face.global_transform*Transform3D(Basis.from_scale(Vector3(.26,.26,1)),Vector3(.47,-.09,.067*side))
		gain(contacts[i],active*(.25+reading*.8+forming*.7) if i==selected else 0.0)
		for material in content_materials[i]:material.set_shader_parameter("formation",instrument.display_amount if i==instrument.loaded_index else 0.0)
		if force_warm:instrument.content[i].node.show();instrument.content[i].node.scale=Vector3.ONE
	var origin:Vector3=module.named(module.data.g_archive.receivers[selected]).global_position
	var target:Vector3=platform.to_global(Vector3(0,.055,0))
	segment(transfer,origin,target,.13);gain(transfer,active*(reading*smoothstep(.30,.55,instrument.read_progress)*.65+forming*.7))
	platen.global_transform=platform.global_transform*Transform3D(Basis(Vector3.RIGHT,-PI/2)*Basis.from_scale(Vector3(.83,.83,1)),Vector3(0,.051,0))
	gain(platen,active*instrument.platform_amount*(.13+forming*.8+instrument.action_energy*.20))
	light.global_position=target+Vector3(0,.22,.18);light.light_energy=active*(.18*instrument.display_amount+forming*.35+instrument.action_energy*.17)
	light.light_color=Color(1,.66,.33).lerp(Color(1,.16,.035),instrument.action_energy*.8 if selected==4 else 0.0)
	var camera:Basis=module.host.camera.global_basis
	for i in range(36):
		var t:float=fposmod(instrument.time*.7+float(i)/36,1);var a:float=i*2.39996
		var p:Vector3=target+module.global_basis*Vector3(.30*cos(a)*sqrt(t),t*.62,.23*sin(a)*sqrt(t))
		var energy:float=forming*(1-t)*.6
		if selected==3:energy+=instrument.action_energy*(1-t)*.28
		glints.multimesh.set_instance_transform(i,Transform3D(camera,p));glints.multimesh.set_instance_custom_data(i,Color(active*energy,0,0,0))
	glints.visible=active>.001
	if instrument.action_count>heard_action:
		heard_action=instrument.action_count
		if not module.host.muted and not force_warm:sound.pitch_scale=1.0+selected*.075;sound.play()
	if module.host.muted:sound.stop()
	sound.volume_db=-23+linear_to_db(maxf(.001,active))

func state()->Dictionary:
	var quads:Array=[]
	for o in scans+contacts+[transfer,platen]:quads.append({"pose":pack(o.global_transform),"tile":o.material_override.get_shader_parameter("tile"),"gain":o.material_override.get_shader_parameter("gain")})
	var particles:Array=[]
	for i in range(36):particles.append({"pose":pack(glints.multimesh.get_instance_transform(i)),"gain":glints.multimesh.get_instance_custom_data(i).r})
	return {"read":instrument.read_progress,"display":instrument.display_amount,"selected":instrument.loaded_index,"energy":instrument.action_energy,"quads":quads,"particles":particles}

func pack(t:Transform3D)->Dictionary:
	var q:=t.basis.get_rotation_quaternion();var s:=t.basis.get_scale();return {"p":[t.origin.x,t.origin.y,t.origin.z],"q":[q.x,q.y,q.z,q.w],"s":[s.x,s.y,s.z]}
