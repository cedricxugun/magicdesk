extends Node3D
## Dedicated F art: authored solid metal swarf, interference/ribbon atlas and
## emissive hardware. All pools and shader variants are prepared before reveal.
var module:Node3D
var instrument:RefCounted
var atlas:Texture2D
var foil:MultiMeshInstance3D
var ticks:MultiMeshInstance3D
var glints:MultiMeshInstance3D
var ribbons:Array[MultiMeshInstance3D]=[]
var filament:MeshInstance3D
var receiver_waves:Array[MeshInstance3D]=[]
var seed:MeshInstance3D
var lights:Array[OmniLight3D]=[]
var contacts:Array[Node3D]=[]
var receiver:Node3D
var plumb:Node3D
var prism:Node3D
var positions:Array[Vector3]=[]
var velocities:Array[Vector3]=[]
var orientations:Array[Quaternion]=[]
var initialized:=false
var force_warm:=false
var draw_gain:=0.0
var calibration_audio:AudioStreamPlayer
var heard_peak_count:=0
const COUNT:=112
const SEGMENTS:=28

func material(tile:float,instanced:bool=false,segments:bool=false)->ShaderMaterial:
	var m:=ShaderMaterial.new();m.shader=load("res://collection/f_atlas.gdshader")
	m.set_shader_parameter("atlas",atlas);m.set_shader_parameter("tile",tile);m.set_shader_parameter("instanced",instanced);m.set_shader_parameter("segment_uv",segments)
	return m

func pool(mesh:Mesh,mat:Material,count:int)->MultiMeshInstance3D:
	var node:=MultiMeshInstance3D.new();var multi:=MultiMesh.new()
	multi.transform_format=MultiMesh.TRANSFORM_3D;multi.use_custom_data=true;multi.mesh=mesh;multi.instance_count=count
	node.multimesh=multi;node.material_override=mat;node.cast_shadow=GeometryInstance3D.SHADOW_CASTING_SETTING_OFF;add_child(node)
	return node

func quad(tile:float,size:Vector2)->MeshInstance3D:
	var node:=MeshInstance3D.new();var mesh:=QuadMesh.new();mesh.size=size
	node.mesh=mesh;node.material_override=material(tile);node.cast_shadow=GeometryInstance3D.SHADOW_CASTING_SETTING_OFF;add_child(node);return node

func setup(owner:Node3D)->void:
	top_level=true;global_transform=Transform3D.IDENTITY
	module=owner;instrument=module.play.instrument;atlas=load(str(module.data.f_fx.atlas))
	for name in module.data.f_fx.contacts:contacts.append(module.named(name))
	receiver=module.named(module.data.f_fx.receiver);plumb=module.named(module.data.f_physics.plumb_pivot);prism=module.named(module.data.f_physics.prism_pivot)
	var prototype:MeshInstance3D=module.named(module.data.f_fx.prototype);prototype.hide()
	var metal:=ShaderMaterial.new();metal.shader=load("res://collection/f_foil.gdshader")
	foil=pool(prototype.mesh,metal,COUNT)
	var tick_prototype:MeshInstance3D=module.named(module.data.f_fx.tick_prototype);tick_prototype.hide()
	ticks=pool(tick_prototype.mesh,metal,28)
	var glint_mesh:=QuadMesh.new();glint_mesh.size=Vector2(.17,.17);glints=pool(glint_mesh,material(2,true),COUNT)
	for i in range(COUNT):positions.append(Vector3.ZERO);velocities.append(Vector3.ZERO);orientations.append(Quaternion.IDENTITY)
	var ribbon_mesh:=QuadMesh.new();ribbon_mesh.size=Vector2.ONE
	for i in range(3):ribbons.append(pool(ribbon_mesh,material(3,true,true),SEGMENTS))
	filament=quad(1,Vector2.ONE)
	for i in range(2):receiver_waves.append(quad(0,Vector2.ONE))
	seed=quad(2,Vector2(.20,.20))
	for i in range(4):
		var light:=OmniLight3D.new();light.light_color=Color(1,.64,.29);light.omni_range=1.8;light.light_energy=0;light.shadow_enabled=false;add_child(light);lights.append(light)
	lights[3].omni_range=.48;lights[3].light_color=Color(1,.34,.10)
	calibration_audio=AudioStreamPlayer.new();calibration_audio.stream=load("res://assets/collection/art/F/calibration.wav");calibration_audio.volume_db=-14;add_child(calibration_audio)

func bezier(a:Vector3,b:Vector3,c:Vector3,t:float)->Vector3:return a*(1-t)*(1-t)+b*2*t*(1-t)+c*t*t

func path(which:int,t:float)->Vector3:
	var start:Vector3=contacts[[0,4,8][which]].global_position
	var finish:Vector3=plumb.to_global(Vector3(0,-.55,0)) if which!=1 else prism.to_global(Vector3(0,-.53,0))
	var middle:Vector3=(start+finish)*.5+module.global_basis*Vector3(-.12,.08,.22 if which%2==0 else -.20)
	return bezier(start,middle,finish,t)

func update_ribbon(node:MultiMeshInstance3D,which:int,gain:float)->void:
	var camera:Vector3=module.host.camera.global_position
	for i in range(SEGMENTS):
		var a:=path(which,float(i)/SEGMENTS);var b:=path(which,float(i+1)/SEGMENTS)
		var x:Vector3=(b-a).normalized();var z:Vector3=(camera-(a+b)*.5).normalized();var y:=z.cross(x).normalized();z=x.cross(y)
		node.multimesh.set_instance_transform(i,Transform3D(Basis(x*(b-a).length(),y*.18,z),(a+b)*.5))
		node.multimesh.set_instance_custom_data(i,Color(gain,float(i)/SEGMENTS,float(i+1)/SEGMENTS,0))
	node.visible=gain>.002

func tick(delta:float,quiet_gain:float)->void:
	if calibration_audio:
		if module.host.muted:calibration_audio.stop()
		calibration_audio.volume_db=-14.0+linear_to_db(maxf(.001,quiet_gain))
		if instrument.peak_count>heard_peak_count:
			heard_peak_count=instrument.peak_count
			if not module.host.muted and not force_warm:calibration_audio.play()
	var active:float=module.openness*(1.0-module.explosion)*module.power*quiet_gain
	if force_warm:active=1.0
	var peak:float=1.0 if force_warm else instrument.peak()
	var crest:float=1.0 if force_warm else instrument.crest()
	var charge:float=instrument.charge
	var release:float=instrument.release_flash()
	var idle:float=.14 if instrument.peak_latched and instrument.peak_time<0 and instrument.coherence>.8 else 1.0
	var bias:float=clampf(absf(instrument.physics.omega)*1.2+absf(instrument.preload_value)*.35+absf(instrument.physics.polarity)*.2,0,1)
	draw_gain=active*(.35+bias*1.8+charge*.8+peak*2.2+crest*1.4)*idle
	var alignment:float=clampf(charge*.80+peak,0,1)
	var center:Vector3=plumb.to_global(Vector3(0,-.49,0))
	var scale:float=module.data.display_calibration.scale
	var orient:Basis=module.global_basis
	var camera:Basis=module.host.camera.global_basis
	for i in range(COUNT):
		var t:float=fposmod(module.clock*.30+float(i)/COUNT,1.0)
		var stream:Vector3=path(i%3,t)
		var layer:int=(i%28)/14
		var angle:float=float(i%14)/13.0*TAU*.82-PI*.82
		angle+=module.clock*.38*(1.0-alignment)
		var normal:Vector3=Vector3(.12,.18,1).normalized() if layer==0 else Vector3(-.23,.31,1).normalized()
		var circle:Basis=orient*Basis(Quaternion(Vector3.UP,normal))
		var radial:Vector3=circle*Vector3(cos(angle),0,sin(angle))
		var target:Vector3=center+radial*(.28+layer*.095)*scale+Vector3(0,(layer-.5)*.16*scale,0)
		var destination:=stream.lerp(target,alignment)
		if i>=28:destination=stream+orient*Vector3(sin(i*5.2+module.clock)*.035,cos(i*2.1+module.clock)*.025,sin(i*3.7-module.clock)*.050)
		if not initialized:positions[i]=destination
		var dt:=minf(delta,.04)
		velocities[i]+=(destination-positions[i])*dt*58.0
		velocities[i]*=exp(-dt*12.0);positions[i]+=velocities[i]*dt
		var direction:Vector3=radial if alignment>.65 else velocities[i].normalized() if velocities[i].length()>.001 else Vector3.UP
		var size:float=(.35+.65*alignment)*scale*(.8+.2*sin(i*17.0))
		if i>=28:size*=.26
		orientations[i]=orientations[i].slerp(Quaternion(Vector3.UP,direction),1.0-exp(-dt*8.0)).normalized()
		var basis:=Basis(orientations[i])*Basis.from_scale(Vector3.ONE*size)
		foil.multimesh.set_instance_transform(i,Transform3D(basis if i>=28 else Basis.from_scale(Vector3.ONE*.00001),positions[i]))
		var intensity:float=draw_gain*(.42+.58*sin(float(i)*12.7)*sin(float(i)*12.7))
		if i>=28:intensity*=.40*(1.0-alignment*.75)
		foil.multimesh.set_instance_custom_data(i,Color(intensity,.45+.45*sin(float(i)*3.7),0,0))
		if i<28:ticks.multimesh.set_instance_transform(i,Transform3D(basis*Basis.from_scale(Vector3(1.2,1.2,1.2)),positions[i]));ticks.multimesh.set_instance_custom_data(i,Color(intensity*.85,.65,0,0))
		glints.multimesh.set_instance_transform(i,Transform3D(camera*Basis.from_scale(Vector3.ONE*scale*(.4 if i>=28 else .8)),positions[i]))
		glints.multimesh.set_instance_custom_data(i,Color(intensity*.55,0,0,0))
	initialized=true;foil.visible=active>.01;ticks.visible=active>.01;glints.visible=draw_gain>.025
	for i in range(3):update_ribbon(ribbons[i],i,active*(.08+bias*.8+charge*.30+peak*1.7+release*.6)*idle)
	var tip:Vector3=module.named(module.data.sockets.weight_tip).global_position
	var foot:=Vector3(tip.x,receiver.global_position.y+.048*scale,tip.z)
	var beam:=foot-tip;var y:=beam.normalized();var x:=y.cross(module.host.camera.global_position-(tip+foot)*.5).normalized()
	filament.global_transform=Transform3D(Basis(x*.16,y*beam.length(),x.cross(y)),(tip+foot)*.5)
	var focus:float=active*(instrument.coherence*.25+charge*.65+peak*1.6+crest)
	filament.visible=module.openness>.98 and focus>.005 and foot.distance_to(receiver.global_position)<.39*scale
	filament.material_override.set_shader_parameter("gain",focus)
	for i in range(receiver_waves.size()):
		var phase:float=fposmod(maxf(instrument.peak_time,0)*.32+i*.5,1.0)
		var radius:float=(.30+phase*.65)*scale
		var wave:MeshInstance3D=receiver_waves[i]
		wave.global_transform=Transform3D(Basis(Vector3.RIGHT,-PI/2)*Basis.from_scale(Vector3(radius,radius,1)),foot+Vector3(0,.009+i*.003,0))
		wave.material_override.set_shader_parameter("gain",active*peak*(.65+crest)*(1.0-phase));wave.visible=active*peak>.005
	var returning:float=smoothstep(3.4,5.5,instrument.peak_time) if instrument.peak_time>=0 else 0.0
	if instrument.aborting:returning=maxf(returning,1.0-instrument.abort_gain)
	var seed_angle:=deg_to_rad(90.0+returning*(51.0-instrument.preload_value*28.0))
	var upper:Node3D=module.named(module.data.upper)
	seed.global_transform=Transform3D(camera,upper.to_global(Vector3(-.1+.887*cos(seed_angle),1.8+.887*sin(seed_angle),.125)))
	seed.material_override.set_shader_parameter("gain",active*(release+peak*(1.0-smoothstep(.92,1.0,returning))));seed.visible=active*(release+peak)>.01
	for material in module.instrument_materials:
		material.set_shader_parameter("instrument_gain",module.power*quiet_gain*(.04+active*(.30+bias*.55+charge+.8*peak+crest*2+release)))
		material.set_shader_parameter("instrument_time",module.clock)
	lights[0].global_position=center+Vector3(0,.04,.10);lights[0].light_energy=active*(.10+charge*.5+peak*1.2+crest*1.2)
	lights[1].global_position=foot+Vector3(0,.09,0);lights[1].light_energy=active*(charge*.4+peak*.8+crest*.8)
	lights[2].global_position=contacts[0].global_position;lights[2].light_energy=active*(release*1.8+peak*.7)
	lights[3].global_position=module.named(module.data.f_physics.brake_rotor).to_global(Vector3(0,0,.15));lights[3].light_energy=active*instrument.braking_heat*.55

func state()->Dictionary:
	var shards:Array=[]
	for i in range(COUNT):
		var node:MultiMeshInstance3D=ticks if i<28 else foil
		var tr:Transform3D=node.multimesh.get_instance_transform(i)
		var q:=tr.basis.get_rotation_quaternion();var s:=tr.basis.get_scale();var p:=tr.origin
		shards.append({"p":[p.x,p.y,p.z],"q":[q.x,q.y,q.z,q.w],"s":[s.x,s.y,s.z],"glow":node.multimesh.get_instance_custom_data(i).r,"kind":"tick" if i<28 else "swarf"})
	return {"solid_foil_instances":COUNT,"allocated_once":true,"gain":draw_gain,"visible":foil.visible,"stage":instrument.stage,"peak_time":instrument.peak_time,"shards":shards}
