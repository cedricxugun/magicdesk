extends Node3D
## Authored atlas carriers, synchronized to the pressure scheduler.
const Optical=preload("res://collection/i_acoustic.gdshader")
const Atlas=preload("res://assets/collection/art/I/acoustic_atlas_r1.png")
var mouth:Node3D
var waves:Array=[]
var receivers:Array=[]
var traces:Dictionary={}
var wave_mesh:ArrayMesh
var receiver_mesh:ArrayMesh
var trace_mesh:ArrayMesh
var warm:OmniLight3D
var cool:OmniLight3D
var amplitudes:Dictionary={}

func setup(asset:Node3D,rig:Dictionary)->void:
	mouth=asset.find_child(rig.mouth,true,false) as Node3D
	wave_mesh=_sheet(true);receiver_mesh=_sheet(false)
	var curves:Array=rig.curves.filter(func(c):return str(c.name).contains("BrassReturnConductor"))
	curves.sort_custom(func(a,b):return str(a.name)<str(b.name))
	trace_mesh=_ribbon(curves[-1].points)
	warm=_light(Color(1.,.38,.10),-.14);cool=_light(Color(.12,.54,1.),-.11)

func _light(color:Color,depth:float)->OmniLight3D:
	var light:=OmniLight3D.new();mouth.add_child(light);light.position.y=depth
	light.light_color=color;light.light_energy=0.;light.omni_range=1.1
	light.shadow_enabled=true;light.omni_attenuation=2.;light.light_size=.10
	return light

func _mesh(vertices:PackedVector3Array,uvs:PackedVector2Array,indices:PackedInt32Array)->ArrayMesh:
	var arrays:Array=[];arrays.resize(Mesh.ARRAY_MAX);arrays[Mesh.ARRAY_VERTEX]=vertices;arrays[Mesh.ARRAY_TEX_UV]=uvs;arrays[Mesh.ARRAY_INDEX]=indices
	var result:=ArrayMesh.new();result.add_surface_from_arrays(Mesh.PRIMITIVE_TRIANGLES,arrays);return result

func _sheet(curved:bool)->ArrayMesh:
	var vertices:=PackedVector3Array();var uv:=PackedVector2Array();var indices:=PackedInt32Array();var n:=24 if curved else 1
	for y in range(n+1):
		for x in range(n+1):
			var a:=float(x)/n*2.-1.;var b:=float(y)/n*2.-1.
			vertices.append(Vector3(a,.04*(a*a+b*b) if curved else 0.,-b));uv.append(Vector2(float(x)/n,1.-float(y)/n))
	for y in range(n):
		for x in range(n):
			var a:=y*(n+1)+x;indices.append_array([a,a+1,a+n+2,a,a+n+2,a+n+1])
	return _mesh(vertices,uv,indices)

func _ribbon(raw:Array)->ArrayMesh:
	var points:=PackedVector3Array();var lengths:Array[float]=[0.]
	for p in raw:points.append(Vector3(p[0],p[1],p[2]))
	for i in range(1,points.size()):lengths.append(lengths[-1]+points[i].distance_to(points[i-1]))
	var vertices:=PackedVector3Array();var uv:=PackedVector2Array();var indices:=PackedInt32Array()
	for i in range(points.size()):
		var tangent:Vector3=(points[mini(i+1,points.size()-1)]-points[maxi(i-1,0)]).normalized()
		var normal:=Vector3.BACK-tangent*tangent.dot(Vector3.BACK)
		if normal.length()<.1:normal=Vector3.UP-tangent*tangent.y
		normal=normal.normalized();var side:=normal.cross(tangent).normalized()
		for sign in [-1.,1.]:vertices.append(points[i]+normal*.010+side*sign*.023);uv.append(Vector2(lengths[i]/lengths[-1],1.-(sign+1.)/2.))
		if i<points.size()-1:
			var a:=i*2;indices.append_array([a,a+1,a+3,a,a+3,a+2])
	return _mesh(vertices,uv,indices)

func _carrier(mesh:ArrayMesh,parent:Node3D,is_flow:bool,color:Color)->Dictionary:
	var material:=ShaderMaterial.new();material.shader=Optical;material.set_shader_parameter("atlas",Atlas)
	material.set_shader_parameter("tint",Vector3(color.r,color.g,color.b));material.set_shader_parameter("flow",is_flow)
	material.set_shader_parameter("tile",Vector2(1.,0.) if is_flow else Vector2.ZERO)
	var node:=MeshInstance3D.new();node.mesh=mesh;node.material_override=material;node.cast_shadow=GeometryInstance3D.SHADOW_CASTING_SETTING_OFF;parent.add_child(node)
	return {"node":node,"material":material}

static func envelope(age:float,duration:float)->float:
	return pow(sin(PI*age/duration),1.2) if age>0. and age<duration else 0.

func update(time:float,state:Dictionary,events:Array,schedule:Array)->void:
	for event in events:
		var outgoing:bool=event.kind=="outgoing"
		var carrier:Dictionary=_carrier(wave_mesh if outgoing else receiver_mesh,mouth,false,Color(1.,.38,.065) if outgoing else Color(.12,.54,1.))
		carrier.event=event.duplicate(true)
		if outgoing:waves.append(carrier)
		else:receivers.append(carrier)
	var valid:Array=[]
	for echo in schedule:
		var key:String=str(echo.due);valid.append(key)
		if not traces.has(key):traces[key]=_carrier(trace_mesh,self,true,Color(.12,.54,1.))
		traces[key].event=echo
	for key in traces.keys():
		if not valid.has(key):traces[key].node.queue_free();traces.erase(key)
	var outgoing_amount:=0.;var return_amount:=0.;var trace_amount:=0.
	for kind in range(2):
		var list:Array=waves if kind==0 else receivers
		for item in list.duplicate():
			var outgoing:bool=kind==0;var duration:=1.1 if outgoing else .70;var age:float=time-float(item.event.time)
			if age>duration:item.node.queue_free();list.erase(item);continue
			var amount:float=float(item.event.gain)*envelope(age,duration)*float(state.gain)
			var progress:=clampf(age/duration,0.,1.)
			var radius:float=(.34+.51*progress)/.82 if outgoing else (.49+.035*exp(-maxf(0.,age)*7.))/.82
			item.node.scale=Vector3.ONE*radius;item.node.position=Vector3(0.,-.14-.75*progress if outgoing else -.119,0.)
			item.material.set_shader_parameter("gain",amount);item.node.visible=amount>.0001
			if outgoing:outgoing_amount+=amount
			else:return_amount+=amount
	for item in traces.values():
		var age:float=time-(float(item.event.due)-.45);var amount:float=float(item.event.gain)*envelope(age,.45)*float(state.gain)
		item.material.set_shader_parameter("gain",amount);item.material.set_shader_parameter("head",1.-clampf(age/.45,0.,1.));item.node.visible=amount>.0001;trace_amount+=amount
	# Real local lights illuminate the mouth; transparent artwork keeps depth testing.
	warm.light_energy=outgoing_amount*.00045;cool.light_energy=return_amount*.00030
	amplitudes={"outgoing":outgoing_amount,"return":return_amount,"trace":trace_amount,"live_carriers":waves.size()+receivers.size()+traces.size()}

func _exit_tree()->void:
	for item in waves+receivers:if is_instance_valid(item.node):item.node.queue_free()
	if is_instance_valid(warm):warm.queue_free()
	if is_instance_valid(cool):cool.queue_free()
