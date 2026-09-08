extends Node3D
## Two existing physical markings per petal: latch enamel and crown witness.
## Extracts their exact final GLB Cherry_Enamel surfaces; no hard-coded proxy
## strip, extra lamp, UI, or GLB edits. Each overlay follows its real part.

const MARKING_SHADER=preload("res://shell_marking.gdshader")
const SURFACE_OFFSET:=.00045
var host:Node3D
var clock:=0.0
var event_kind:="steady"
var event_time:=-1.0
var markings:Array[Dictionary]=[]
var diagnostics:Dictionary={"expected":12,"created":0,"missing":[],"offset":SURFACE_OFFSET,"vertices":0}
var _shutdown_power:=0.0

func setup(owner:Node3D)->void:
	if host!=null:return
	host=owner
	for i in range(6):
		for kind in ["Latch","Enamel"]:
			var target_name:="P_Petal_%02d_%s"%[i,kind]
			var target:Node3D=host.named(target_name)
			if target==null:
				diagnostics.missing.append(target_name);continue
			var created:=false
			for source_node in target.find_children("*","MeshInstance3D",true,false):
				var source:=source_node as MeshInstance3D
				if source.name.begins_with("Shell_Marking_"):continue
				for surface in range(source.mesh.get_surface_count()):
					var original:Material=source.mesh.surface_get_material(surface)
					if original==null or original.resource_name!="Cherry_Enamel":continue
					created=_make_marking(source,surface,original,i,kind=="Enamel") or created
			if not created:diagnostics.missing.append(target_name+" / Cherry_Enamel")
	set_process(false)
	tick(0.0)
	if not diagnostics.missing.is_empty():push_warning("Shell marking surfaces not found: "+str(diagnostics.missing))

func _make_marking(source:MeshInstance3D,surface:int,original:Material,petal:int,crown:bool)->bool:
	var arrays:Array=source.mesh.surface_get_arrays(surface).duplicate(true)
	var vertices:PackedVector3Array=arrays[Mesh.ARRAY_VERTEX]
	var normals:PackedVector3Array=arrays[Mesh.ARRAY_NORMAL]
	if vertices.is_empty() or normals.size()!=vertices.size():return false
	var low:=INF;var high:=-INF
	for i in range(vertices.size()):
		low=minf(low,vertices[i].y);high=maxf(high,vertices[i].y)
		vertices[i]+=normals[i].normalized()*SURFACE_OFFSET
	arrays[Mesh.ARRAY_VERTEX]=vertices
	var mesh:=ArrayMesh.new();mesh.add_surface_from_arrays(Mesh.PRIMITIVE_TRIANGLES,arrays)
	var material:=ShaderMaterial.new();material.shader=MARKING_SHADER
	if original is BaseMaterial3D:
		material.set_shader_parameter("enamel_color",original.albedo_color)
		material.set_shader_parameter("metalness",original.metallic)
		material.set_shader_parameter("roughness_value",clampf(original.roughness,.20,.48))
	material.set_shader_parameter("height_limits",Vector2(low,high))
	material.set_shader_parameter("phase_offset",petal*.72+(1.3 if crown else 0.0))
	var lamp:=MeshInstance3D.new()
	lamp.name="Shell_Marking_%s_%02d"%["Crown" if crown else "Latch",petal]
	lamp.mesh=mesh;lamp.material_override=material
	lamp.cast_shadow=GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	# Identity child of the source mesh preserves every imported transform and
	# every shell/part animation, including independent exploded components.
	source.add_child(lamp)
	markings.append({"node":lamp,"source":source,"surface":surface,"material":material,"petal":petal,"crown":crown,"energy":0.0,"shutdown_energy":0.0})
	diagnostics.created=int(diagnostics.created)+1
	diagnostics.vertices=int(diagnostics.vertices)+vertices.size()
	return true

func trigger(kind:String)->void:
	event_kind="open" if kind=="core_open" else kind;event_time=0.0
	if kind=="shutdown":
		_shutdown_power=_host_float("power",1.0)
		for marking in markings:marking.shutdown_energy=marking.energy

func _host_float(property:String,fallback:float=0.0)->float:
	var value:Variant=host.get(property)
	return fallback if value==null else float(value)

func tick(delta:float)->void:
	if host==null:return
	clock+=maxf(0.0,delta)
	if event_time>=0.0:event_time+=maxf(0.0,delta)
	var power:=clampf(_host_float("power"),0.0,1.0)
	var explosion:=clampf(_host_float("explosion"),0.0,1.0)
	var connected:=1.0-smoothstep(.025,.20,explosion)
	var activation:=clampf(_host_float("activation_energy"),0.0,1.0)
	var overload_left:=maxf(0.0,_host_float("overload"))
	var overload_envelope:=sin(clampf(overload_left/7.0,0.0,1.0)*PI)
	if event_kind=="overload" and event_time<5.0:overload_envelope=maxf(overload_envelope,sin(clampf(event_time/5.0,0.0,1.0)*PI))
	for marking in markings:
		var crown:bool=marking.crown
		var petal:int=marking.petal
		var energy:=.45*power*connected
		var fill:=1.0;var scan:=-2.0;var scan_energy:=0.0;var heat:=.06
		if event_kind in ["ignition","open","assemble"] and event_time<1.7:
			var delay:=petal*.055+(.30 if crown else .0)
			var progress:=(event_time-delay)/.64
			scan=progress
			fill=clampf(progress+.10,0.0,1.0)
			scan_energy=3.15*power*connected if progress>-.18 and progress<1.18 else 0.0
			heat=.58 if event_kind=="open" else .30
			if event_kind=="assemble":scan_energy*=.65
		energy+=activation*1.35*power*connected
		if activation>.02:heat=maxf(heat,activation*.85)
		if overload_envelope>.001:
			var pulse:=.69+.31*sin(clock*8.4+petal*.18+(0.4 if crown else 0.0))
			energy+=2.3*overload_envelope*pulse*power*connected
			heat=maxf(heat,overload_envelope*.94)
		if event_kind=="shutdown":
			# Reverse circuit: crown first, then lower latch, descending within
			# each physical inlay. Never produce a new ignition flash on shutdown.
			var delay:=(5-petal)*.045+(.0 if crown else .22)
			var progress:=clampf((event_time-delay)/.65,0.0,1.0)
			fill=1.0-progress;scan=-2.0;scan_energy=0.0;heat=.0
			energy=float(marking.shutdown_energy)*connected*(1.0-progress*.45)
			if event_time>1.15:energy=0.0;fill=0.0
		if event_kind=="explode":
			energy*=1.0-smoothstep(.0,.3,event_time);scan_energy=0.0
		# The original crown inlay is only ~3mm wide; a modest local emissive
		# gain keeps it readable without outlining the rest of the enamel shell.
		var crown_gain:=1.5 if crown else 1.0
		marking.energy=energy
		var material:ShaderMaterial=marking.material
		material.set_shader_parameter("energy",energy*crown_gain)
		material.set_shader_parameter("fill",fill)
		material.set_shader_parameter("scan",scan)
		material.set_shader_parameter("scan_energy",scan_energy*crown_gain)
		material.set_shader_parameter("heat",heat)
		material.set_shader_parameter("flow_clock",clock)

func get_diagnostics()->Dictionary:
	var result:=diagnostics.duplicate(true)
	result.event=event_kind;result.event_time=event_time
	result.part_parent_errors=0
	for marking in markings:
		if marking.node.get_parent()!=marking.source:result.part_parent_errors=int(result.part_parent_errors)+1
	return result

func _exit_tree()->void:
	for marking in markings:
		if is_instance_valid(marking.node):marking.node.queue_free()
