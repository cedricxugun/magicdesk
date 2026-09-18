extends Node3D
var module:Node3D
var player:RefCounted
var spec:Dictionary
var surfaces:Array=[]
var strokes:Array=[]
var seal_profile:Dictionary
func setup(owner:Node3D)->void:
	module=owner;player=module.play.g_instrument;spec=module.data.g_archive.contents[1].butterfly
	seal_profile=JSON.parse_string(FileAccess.get_file_as_string("res://assets/collection/butterfly_seal.json"))
	assert(seal_profile.source_sha256==spec.source_sha256,"Seal atlas does not match butterfly source")
	var root:Node3D=module.named(module.data.g_archive.contents[1].root)
	for mesh in module.meshes:
		if not root.is_ancestor_of(mesh):continue
		var parent:Node=mesh;var wing:Node3D
		while parent!=root:
			if spec.wing_spans.has(str(parent.name)):wing=parent;break
			parent=parent.get_parent()
		for i in range(mesh.mesh.get_surface_count()):
			var mat:Material=mesh.get_active_material(i)
			if not mat is ShaderMaterial:continue
			mat.set_shader_parameter("butterfly_body",wing==null);mat.set_shader_parameter("butterfly_wing",wing!=null)
			if wing:
				var upper:bool=str(wing.name).contains("Upper")
				var seal:Dictionary=seal_profile.wings["upper" if upper else "lower"]
				mat.set_shader_parameter("wing_span",spec.wing_spans[str(wing.name)]);mat.set_shader_parameter("wing_start",seal.metal_phase[0]);mat.set_shader_parameter("wing_end",seal.metal_phase[1])
				var source:String=mat.get_meta("source_material","");var kind:=1 if source.contains("Porcelain") else 2 if source.contains("Red") else 0
				mat.set_shader_parameter("wing_seal_kind",kind)
				if kind>0:
					mat.set_shader_parameter("wing_seal_map",load(seal.texture));var bounds:Array=seal.bounds
					mat.set_shader_parameter("wing_seal_bounds",Vector4(bounds[0],bounds[1],bounds[2],bounds[3]));var phase:Array=seal.red_phase if kind==2 else seal.seal_phase
					mat.set_shader_parameter("wing_seal_start",phase[0]);mat.set_shader_parameter("wing_seal_end",phase[1])
				surfaces.append({"mat":mat,"wing":wing,"side":-1.0 if str(wing.name).ends_with("-1") else 1.0})
	var grouped:Dictionary={}
	for guide in spec.guides:
		if not grouped.has(guide.node):grouped[guide.node]=[]
		grouped[guide.node].append(guide)
	for key in grouped:
		var guides:Array=grouped[key].duplicate(true)
		if guides[0].wing:
			var phase:Array=seal_profile.wings["upper" if str(key).contains("Upper") else "lower"].metal_phase
			for guide in guides:guide.start=phase[0];guide.end=phase[1]
		var node:=MultiMeshInstance3D.new();var mm:=MultiMesh.new();mm.transform_format=MultiMesh.TRANSFORM_3D;mm.use_custom_data=true
		var shape:=CylinderMesh.new();shape.height=1.;shape.top_radius=.0018;shape.bottom_radius=.0018;shape.radial_segments=6;mm.mesh=shape
		var count:=0
		for g in guides:count+=g.points.size()-1
		mm.instance_count=count;node.multimesh=mm
		var mat:=ShaderMaterial.new();mat.shader=load("res://collection/butterfly_trace.gdshader");mat.set_shader_parameter("pattern",load("res://assets/collection/art/G_AI/field_strands.png"));node.material_override=mat;node.cast_shadow=GeometryInstance3D.SHADOW_CASTING_SETTING_OFF;module.named(key).add_child(node)
		var index:=0;var endpoints:Array=[]
		for g in guides:
			for i in range(g.points.size()-1):
				var a:Vector3=module.v3(g.points[i])+Vector3(0,0,.002);var b:Vector3=module.v3(g.points[i+1])+Vector3(0,0,.002);var d:=b-a
				mm.set_instance_transform(index,Transform3D(Basis(Quaternion(Vector3.UP,d.normalized()))*Basis.from_scale(Vector3(1,d.length(),1)),(a+b)*.5))
				mm.set_instance_custom_data(index,Color(absf(a.x)/float(g.span) if g.wing else a.y/float(g.span),absf(b.x)/float(g.span) if g.wing else b.y/float(g.span),0,0));index+=1
				if i%6==0:endpoints.append(a)
		strokes.append({"node":node,"mat":mat,"start":guides[0].start,"end":guides[0].end,"points":endpoints})
func tick(gain:float,clock:float,warm:bool=false)->Array:
	for item in surfaces:
		item.mat.set_shader_parameter("wing_origin",item.wing.global_position);item.mat.set_shader_parameter("wing_outward",item.wing.global_basis.x.normalized()*item.side);item.mat.set_shader_parameter("wing_vertical",item.wing.global_basis.y.normalized())
	var endpoints:Array=[];var print_root:Node3D=module.named(module.data.record_player.print_root)
	for s in strokes:
		s.node.visible=(player.loaded_index==1 and gain>.002) or warm;s.mat.set_shader_parameter("progress",smoothstep(s.start,s.end,.55 if warm else player.print_amount));s.mat.set_shader_parameter("gain",1.0 if warm else gain);s.mat.set_shader_parameter("clock",clock)
		for p in s.points:endpoints.append(print_root.to_local(s.node.to_global(p)))
	return endpoints
