extends Node3D

var host:Node3D
var clock:=0.0
var event_time:=-1.0
var event_kind:=""
var channels:Array=[]
var material:ShaderMaterial
var lift:Node3D
var support:Node3D

func setup(owner:Node3D)->void:
	host=owner;lift=host.named("CORE_LIFT");support=host.named("P_Core_Support_Post")
	var shader:=Shader.new()
	shader.code="""
shader_type spatial;
render_mode unshaded;
uniform float energy=0.0;
void fragment(){ALBEDO=vec3(.055,.006,.003);EMISSION=vec3(2.8,.045,.016)*energy;}
"""
	material=ShaderMaterial.new();material.shader=shader
	var slit:=BoxMesh.new();slit.size=Vector3(.010,.075,.003)
	# Thin axial insets on the steel lift post; they occupy a physical metal face.
	for side in range(3):
		var angle:=TAU*float(side)/3.0
		for i in range(4):
			var n:=MeshInstance3D.new();n.mesh=slit
			var m:=material.duplicate() as ShaderMaterial;n.material_override=m
			n.cast_shadow=GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
			support.add_child(n)
			n.position=Vector3(sin(angle)*.076,-.17+float(i)*.105,cos(angle)*.076)
			n.rotation.y=angle
			channels.append({"mat":m,"height":.36+float(i)*.13,"kind":0})
	# Recessed vertical pin lights sit inside the upper cradle's mechanical gaps.
	var stator_slit:=BoxMesh.new();stator_slit.size=Vector3(.012,.058,.004)
	var turn:Node3D=host.named("P_Lower_Stator")
	for i in range(12):
		var angle:=TAU*(float(i)+.5)/12.0
		var n:=MeshInstance3D.new();n.mesh=stator_slit
		var m:=material.duplicate() as ShaderMaterial;n.material_override=m
		n.cast_shadow=GeometryInstance3D.SHADOW_CASTING_SETTING_OFF;turn.add_child(n)
		n.position=Vector3(sin(angle)*.453,.88,cos(angle)*.453);n.rotation.y=angle
		channels.append({"mat":m,"height":.12+float(i%3)*.03,"kind":1})
	tick(0.0)

func trigger(kind:String)->void:event_kind=kind;event_time=0.0

func tick(delta:float)->void:
	clock+=delta
	if event_time>=0.0:event_time+=delta
	var power:=float(host.power)
	var assembled:=1.0-smoothstep(.02,.18,float(host.explosion))
	var open:=float(host.openness)
	var shutdown:=1.0
	if event_kind=="shutdown":shutdown=1.0-smoothstep(.15,1.8,event_time)
	var energy:=.14+.035*sin(clock*1.6)
	var boost:=0.0
	if event_kind=="open":boost=smoothstep(.45,.76,open)*(1.0-smoothstep(3.8,5.5,event_time))
	var overload_left:=clampf(float(host.get("overload")),0.0,7.0)
	var overload_envelope:=pow(sin(overload_left/7.0*PI),2.0) if overload_left>0.0 else 0.0
	boost=maxf(boost,overload_envelope)
	for c in channels:
		var travel:=0.0
		if event_kind in ["ignition","open"] and event_time<1.55:
			travel=exp(-pow((float(c.height)-event_time*.85)*6.0,2.0))*1.7
		if overload_left>5.45:
			var charge_time:=7.0-overload_left
			travel=maxf(travel,exp(-pow((float(c.height)-charge_time*.70)*6.0,2.0))*.75*charge_time)
		var brightness:float=(energy+travel+boost*.95)*power*assembled*shutdown
		c.mat.set_shader_parameter("energy",brightness)
