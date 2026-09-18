extends Node3D
var module:Node3D
var player:RefCounted
var spec:Dictionary
var profile:Dictionary
var surfaces:Array=[]
var strokes:Array=[]
var ship_root:Node3D

func setup(owner:Node3D)->void:
	module=owner;player=module.play.g_instrument;spec=module.data.g_archive.contents[2].ship
	profile=JSON.parse_string(FileAccess.get_file_as_string("res://assets/collection/ship_fabrication.json"))
	assert(profile.source_sha256==spec.source_sha256,"Ship fabrication fields do not match the source")
	ship_root=module.named(module.data.g_archive.contents[2].root)
	for mesh in ship_root.find_children("*","MeshInstance3D",true,false):
		var branch:Node3D=mesh.get_parent();var name:=str(branch.name)
		var wave:bool=name in spec.rig.waves
		var sail_branch:bool=name in spec.rig.sails
		var mast:bool=name=="GS2_Mast" or sail_branch
		var hull:bool=name==str(spec.rig.roll)
		var fittings:bool=name==str(spec.fittings_node)
		var phase:=Vector2(.02,.28)
		if wave:phase=Vector2(.10,.32)
		elif mast:phase=Vector2(.32,.52)
		elif fittings:phase=Vector2(.52,.68)
		elif hull or name=="GS2_Deck":phase=Vector2(.22,.48)
		var bounds:AABB=(branch.global_transform.affine_inverse()*mesh.global_transform)*mesh.get_aabb()
		for i in range(mesh.mesh.get_surface_count()):
			var mat:Material=mesh.get_active_material(i)
			if not mat is ShaderMaterial:continue
			var source:String=mat.get_meta("source_material","")
			var cloth:bool=source.contains("ShipMainSail") or source.contains("ShipJibSail")
			var porcelain:bool=hull and source.contains("Porcelain")
			mat.set_meta("ship_fabrication",true)
			mat.set_shader_parameter("ship_part",not cloth and not porcelain)
			mat.set_shader_parameter("ship_sail",cloth);mat.set_shader_parameter("ship_hull",porcelain)
			mat.set_shader_parameter("ship_phase",phase);mat.set_shader_parameter("ship_center_out",wave)
			mat.set_shader_parameter("build_gain",.22)
			mat.set_shader_parameter("build_color",Vector3(1.,.55,.20))
			if porcelain:
				mat.set_shader_parameter("ship_seal_map",load(profile.hull.texture));mat.set_shader_parameter("ship_phase",Vector2(profile.hull.phase[0],profile.hull.phase[1]))
			if cloth:
				var settings:Dictionary=profile.sails["main" if source.contains("Main") else "jib"]
				mat.set_shader_parameter("ship_weft_map",load(settings.texture));mat.set_shader_parameter("ship_phase",Vector2(settings.cloth_phase[0],settings.cloth_phase[1]))
				mat.set_shader_parameter("ship_warp_phase",Vector2(settings.warp_phase[0],settings.warp_phase[1]));mat.set_shader_parameter("ship_crest_phase",Vector2(settings.crest_phase[0],settings.crest_phase[1]))
				mat.set_shader_parameter("ship_plain_cloth",load("res://assets/collection/art/G_AI/ship/jib_albedo.png"))
			surfaces.append({"mat":mat,"branch":branch,"axis":Vector3.RIGHT if wave else Vector3.UP,"bounds":Vector2(0,maxf(absf(bounds.position.x),absf(bounds.end.x))) if wave else Vector2(bounds.position.y,maxf(.001,bounds.size.y))})
	var guides:Array=spec.guides.duplicate(true)
	for guide in guides:
		guide.start=.18;guide.end=.45;guide.kind="frame"
		if str(guide.source_curve).contains("RibbonRolledEdge"):guide.start=.10;guide.end=.32;guide.kind="wave"
		elif str(guide.source_curve).contains("SailSewnEdge"):guide.start=.35;guide.end=.54;guide.kind="sail_edge"
		elif str(guide.source_curve).contains("FixedPitchFork"):guide.start=.03;guide.end=.28
	guides.append_array(profile.weft_guides)
	var grouped:Dictionary={}
	for guide in guides:
		var key:String=guide.node+"/"+guide.kind
		if not grouped.has(key):grouped[key]=[]
		grouped[key].append(guide)
	for key in grouped:
		var group:Array=grouped[key];var first:Dictionary=group[0]
		var node:=MultiMeshInstance3D.new();var mm:=MultiMesh.new();mm.transform_format=MultiMesh.TRANSFORM_3D;mm.use_custom_data=true
		var shape:=CylinderMesh.new();shape.height=1.;shape.top_radius=.00055 if first.kind=="weft" else .0017;shape.bottom_radius=shape.top_radius;shape.radial_segments=6;mm.mesh=shape
		var count:=0
		for guide in group:count+=guide.points.size()-1
		mm.instance_count=count;node.multimesh=mm
		var mat:=ShaderMaterial.new();mat.shader=load("res://collection/butterfly_trace.gdshader")
		mat.set_shader_parameter("pattern",load("res://assets/collection/art/G_AI/field_strands.png"));mat.set_shader_parameter("ink_color",Vector3(1.,.56,.18))
		node.material_override=mat;node.cast_shadow=GeometryInstance3D.SHADOW_CASTING_SETTING_OFF;module.named(first.node).add_child(node)
		var index:=0
		for guide in group:
			var points:Array=[]
			for i in range(guide.points.size()):
				var point:Vector3=module.v3(guide.points[i])
				if guide.kind!="weft":
					var axis:Vector3=(module.v3(guide.points[mini(i+1,guide.points.size()-1)])-module.v3(guide.points[maxi(i-1,0)])).normalized()
					var outward:=Vector3.BACK-axis*axis.dot(Vector3.BACK)
					if outward.length()<.01:outward=Vector3.UP-axis*axis.dot(Vector3.UP)
					point+=outward.normalized()*(float(guide.get("radius",.002))+.0012)
				points.append(point)
			for i in range(guide.points.size()-1):
				var a:Vector3=points[i];var b:Vector3=points[i+1];var d:=b-a
				mm.set_instance_transform(index,Transform3D(Basis(Quaternion(Vector3.UP,d.normalized()))*Basis.from_scale(Vector3(1,d.length(),1)),(a+b)*.5))
				var u:=i/float(guide.points.size()-1);var v:=(i+1)/float(guide.points.size()-1)
				if guide.kind=="wave" or str(guide.get("source_curve","")).contains("KeelSpine") or str(guide.get("source_curve","")).contains("Gunwale"):
					u=clampf(absf(a.x)/.34,0,1);v=clampf(absf(b.x)/.34,0,1)
				elif str(guide.get("source_curve","")).contains("InternalHullRib"):
					u=absf(u-.5)*2.;v=absf(v-.5)*2.
				if guide.kind=="weft":u+=float(guide.delay)*sin(PI*u);v+=float(guide.delay)*sin(PI*v)
				mm.set_instance_custom_data(index,Color(u,v,0,0));index+=1
		strokes.append({"node":node,"mat":mat,"start":float(first.start),"end":float(first.end),"kind":str(first.kind)})
	tick(0.,0.)

func tick(gain:float,clock:float,warm:bool=false)->Array:
	var active:bool=player.loaded_index==2
	for s in surfaces:
		if not active and not warm:continue
		s.mat.set_shader_parameter("build_gain",.22+.08*exp(-pow((player.print_amount-.77)/.16,2)))
		s.mat.set_shader_parameter("ship_form_origin",s.branch.global_position)
		s.mat.set_shader_parameter("ship_form_axis",(s.branch.global_basis*s.axis).normalized())
		s.mat.set_shader_parameter("ship_form_bounds",s.bounds)
	var progress:float=.65 if warm else player.print_amount
	for s in strokes:
		var pulse:bool=active and player.stage=="playing" and s.kind=="wave" and player.action_energy>.002
		var amount:float=gain*smoothstep(s.start-.03,s.start+.05,progress)*(1.-smoothstep(minf(.95,s.end+.08),minf(1.0,s.end+.28),progress))
		if pulse:amount=player.action_energy*.10
		if warm:amount=.8
		s.node.visible=(active and amount>.002) or warm
		s.mat.set_shader_parameter("progress",fposmod(clock*.23,1.) if pulse else smoothstep(s.start,s.end,progress))
		s.mat.set_shader_parameter("gain",amount);s.mat.set_shader_parameter("clock",clock);s.mat.set_shader_parameter("pulse_only",pulse)
		s.mat.set_shader_parameter("rear_progress",smoothstep(profile.sails.main.cloth_phase[0],profile.sails.main.cloth_phase[1],progress) if s.kind=="weft" else -1.0)
	return [Vector3(0,.03525,0)]

func state()->Dictionary:
	return {"surfaces":surfaces.size(),"stroke_groups":strokes.size(),"visible_strokes":strokes.filter(func(s):return s.node.visible).size(),"source_sha256":profile.source_sha256}
