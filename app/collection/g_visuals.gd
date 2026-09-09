extends Node3D
## Generated optical atlas + Blender-authored 3D contour relief. No generic cloud.
var module:Node3D
var instrument:RefCounted
var atlas:Texture2D
var force_warm:=false
var bores:Array=[]
var beams:Array=[]
var scans:Array=[]
var relays:Array=[]
var engravings:Array=[]
var relief:Array=[]
var relief_materials:Array=[]
var relief_batch:MeshInstance3D
var relief_material:ShaderMaterial
var glints:MultiMeshInstance3D
var lights:Array=[]
var audio:AudioStreamPlayer
var heard_peak:=0

func mat(tile:float)->ShaderMaterial:
	var m:=ShaderMaterial.new();m.shader=load("res://collection/g_atlas.gdshader");m.set_shader_parameter("atlas",atlas);m.set_shader_parameter("tile",tile);return m

func quad(tile:float)->MeshInstance3D:
	var node:=MeshInstance3D.new();var mesh:=QuadMesh.new();mesh.size=Vector2.ONE
	node.mesh=mesh;node.material_override=mat(tile);node.cast_shadow=GeometryInstance3D.SHADOW_CASTING_SETTING_OFF;add_child(node);return node

func setup(owner:Node3D)->void:
	top_level=true;global_transform=Transform3D.IDENTITY;module=owner;instrument=module.play.g_instrument
	atlas=load(str(module.data.g_fx.atlas))
	for i in range(6):bores.append(quad(0));scans.append(quad(1));engravings.append(quad(3))
	for i in range(2):beams.append(quad(1))
	for i in range(4):relays.append(quad(1))
	var relief_root:Node3D=module.named(module.data.g_mechanism.relief)
	var batch:=SurfaceTool.new();batch.begin(Mesh.PRIMITIVE_TRIANGLES)
	for name in module.data.g_mechanism.relief_layers:
		var node:Node3D=module.named(name);relief.append(node)
		for child in node.get_children():
			if child is MeshInstance3D:
				for surface in range(child.mesh.get_surface_count()):batch.append_from(child.mesh,surface,relief_root.global_transform.affine_inverse()*child.global_transform)
		node.hide()
	relief_material=ShaderMaterial.new();relief_material.shader=load("res://collection/g_relief.gdshader");relief_material.set_shader_parameter("atlas",atlas)
	relief_batch=MeshInstance3D.new();relief_batch.mesh=batch.commit();relief_batch.material_override=relief_material;relief_batch.cast_shadow=GeometryInstance3D.SHADOW_CASTING_SETTING_OFF;relief_root.add_child(relief_batch)
	glints=MultiMeshInstance3D.new();var mm:=MultiMesh.new();mm.transform_format=MultiMesh.TRANSFORM_3D;mm.use_custom_data=true
	var mesh:=QuadMesh.new();mesh.size=Vector2(.075,.075);mm.mesh=mesh;mm.instance_count=64;glints.multimesh=mm
	var gm:=mat(2);gm.set_shader_parameter("instanced",true);glints.material_override=gm;glints.cast_shadow=GeometryInstance3D.SHADOW_CASTING_SETTING_OFF;add_child(glints)
	for i in range(3):
		var light:=OmniLight3D.new();light.light_color=Color(1,.64,.28);light.omni_range=1.15;light.shadow_enabled=false;add_child(light);lights.append(light)
	if ResourceLoader.exists("res://assets/collection/art/G/inscription.wav"):
		audio=AudioStreamPlayer.new();audio.stream=load("res://assets/collection/art/G/inscription.wav");audio.volume_db=-19;add_child(audio)

func gain(node:MeshInstance3D,value:float)->void:
	node.visible=value>.002;node.material_override.set_shader_parameter("gain",value)

func segment(node:MeshInstance3D,a:Vector3,b:Vector3,width:float)->void:
	var x:Vector3=(b-a).normalized();var z:Vector3=(module.host.camera.global_position-(a+b)*.5).normalized()
	var y:=z.cross(x).normalized();z=x.cross(y)
	node.global_transform=Transform3D(Basis(x*(b-a).length()*1.22,y*width,z),(a+b)*.5)

func tick(delta:float,quiet_gain:float)->void:
	instrument.update_optics()
	var active:float=smoothstep(.65,1,module.openness)*(1-module.explosion)*module.power
	var lit:float=active*quiet_gain
	var projection:float=instrument.projection*active
	var peak:float=instrument.crest()
	if force_warm:active=1;lit=1;projection=1;peak=1
	for i in range(6):
		var leaf:Dictionary=instrument.leaves[i];var face:Node3D=leaf.face
		var side:float=leaf.side
		bores[i].global_transform=face.global_transform*Transform3D(Basis.from_scale(Vector3(.34,.34,1)),Vector3(.47,-.09,.073*side))
		gain(bores[i],lit*(.14+instrument.bank_quality[0 if i<3 else 1]*(.26+peak*.8)+instrument.selection[i]*.18))
		var writer:Node3D=leaf.writer
		var a:Vector3=writer.to_global(Vector3(.255,0,.145*side));var b:Vector3=writer.to_global(Vector3(.685,0,.145*side))
		segment(scans[i],a,b,.11)
		gain(scans[i],lit*(1.7 if (instrument.writing and i==instrument.selected) or force_warm else .03))
		engravings[i].global_transform=face.global_transform*Transform3D(Basis.from_scale(Vector3(.51,1.0,1)),Vector3(.47,.0,.027*side))
		gain(engravings[i],lit*instrument.records[i]*.43)
	for bank in range(2):
		var ray:Dictionary=instrument.rays[bank]
		segment(beams[bank],ray.start,ray.end,.10)
		gain(beams[bank],lit*(.17+float(ray.quality)*(.30+projection*.90+peak*.55)))
		lights[bank].global_position=(ray.start+ray.end)*.5;lights[bank].light_energy=lit*(.03+projection*.20+peak*.18)
	relief_batch.visible=projection>.001
	relief_material.set_shader_parameter("reveal",projection)
	relief_material.set_shader_parameter("gain",active*(.75+peak*1.8))
	relief_material.set_shader_parameter("travel",instrument.time)
	var root:Node3D=module.named(module.data.g_mechanism.relief)
	for bank in range(2):
		var face:Node3D=instrument.leaves[bank*3].face
		var a:Vector3=face.to_global(Vector3(.47,-.09,.08*float(instrument.leaves[bank*3].side)))
		var b:Vector3=module.named(module.data.sockets.field).global_position+module.global_basis*Vector3((-.23 if bank==0 else .23),-.20,0)
		var c:Vector3=root.to_global(Vector3((-.28 if bank==0 else .28),.01,-.16))
		segment(relays[bank*2],a,b,.08);segment(relays[bank*2+1],b,c,.065)
		var relay_gain:float=projection*instrument.bank_quality[bank]*(.18+peak*.65)
		gain(relays[bank*2],relay_gain);gain(relays[bank*2+1],relay_gain)
	# Rotation belongs to the object, not the camera-facing optical accents.
	root.rotation.y=sin(instrument.time*.28)*.12
	lights[2].global_position=root.global_position;lights[2].light_energy=projection*(.15+peak*.36)
	var current:Dictionary=instrument.leaves[instrument.selected]
	var camera:Basis=module.host.camera.global_basis
	var emission:float=lit*(1.0 if instrument.writing else .0)
	for i in range(64):
		var t:float=fposmod(instrument.time*.72+float(i)/64,1)
		var p:Vector3
		var strength:float
		if i<40:
			# The chips originate on the actual writer, fall under 9.81m/s² at
			# millimetric scale, and expire locally. They do not orbit the base.
			var age:float=t*.24
			p=current.writer.to_global(Vector3(.27+fposmod(i*.173,.40),-.5*9.81*age*age,(.145+age*.16)*float(current.side)))
			strength=emission*(1-t)*.60
		else:
			var angle:float=(i-40)*TAU/24
			p=root.to_global(Vector3(.43*cos(angle),.03+t*.40,.23*sin(angle)))
			strength=projection*(.16+peak*.64)*(1-absf(t-.5)*2)
		glints.multimesh.set_instance_transform(i,Transform3D(camera*Basis.from_scale(Vector3.ONE*(.34 if i<40 else .62)),p))
		glints.multimesh.set_instance_custom_data(i,Color(1.0 if force_warm else strength,0,0,0))
	glints.material_override.set_shader_parameter("gain",1.0);glints.visible=active>.001
	if audio:
		if module.host.muted:audio.stop()
		audio.volume_db=-19+linear_to_db(maxf(.001,active*quiet_gain))
		if instrument.peak_count>heard_peak:
			heard_peak=instrument.peak_count
			if not module.host.muted and not force_warm:audio.play()

func state()->Dictionary:
	var quads:Array=[]
	for group in [bores,beams,scans,engravings,relays]:
		for node in group:quads.append({"name":str(node.name),"tile":node.material_override.get_shader_parameter("tile"),"pose":pack(node.global_transform),"gain":node.material_override.get_shader_parameter("gain")})
	var particles:Array=[]
	for i in range(64):particles.append({"pose":pack(glints.multimesh.get_instance_transform(i)),"gain":glints.multimesh.get_instance_custom_data(i).r})
	return {"projection":instrument.projection,"peak":instrument.crest(),"quads":quads,"particles":particles}

func pack(t:Transform3D)->Dictionary:
	var q:=t.basis.get_rotation_quaternion();var s:=t.basis.get_scale();return {"p":[t.origin.x,t.origin.y,t.origin.z],"q":[q.x,q.y,q.z,q.w],"s":[s.x,s.y,s.z]}
