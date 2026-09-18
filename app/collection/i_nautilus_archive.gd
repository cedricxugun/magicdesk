extends RefCounted
## Temporary archive materials only. Exact original overrides return at scan=0.
var asset:Node3D
var records:Array=[]
var cache:Dictionary={}
var shaders:Dictionary={}
var active:=false
func bind(subject:Node3D)->void:asset=subject
func cut_shader(source:Shader)->Shader:
	if shaders.has(source):return shaders[source]
	var code:String=source.code
	code=code.insert(code.find(";")+1,"\nuniform float nautilus_cut=100.;\nvarying float nautilus_y;\n")
	var re:=RegEx.new();re.compile("void\\s+vertex\\s*\\(\\s*\\)\\s*\\{")
	var match_vertex:=re.search(code)
	if match_vertex:
		var depth:=1;var end:int=match_vertex.get_end()
		while depth>0:
			if code[end]=="{":depth+=1
			elif code[end]=="}":depth-=1
			end+=1
		code=code.insert(end-1,"\nnautilus_y=(MODEL_MATRIX*vec4(VERTEX,1.)).y;\n")
	else:code+="\nvoid vertex(){nautilus_y=(MODEL_MATRIX*vec4(VERTEX,1.)).y;}\n"
	re.compile("void\\s+fragment\\s*\\(\\s*\\)\\s*\\{")
	var fragment:=re.search(code);assert(fragment!=null)
	code=code.insert(fragment.get_end(),"\nif(nautilus_y>nautilus_cut) discard;\n")
	var result:=Shader.new();result.code=code;shaders[source]=result;return result
func converted(original:Material)->ShaderMaterial:
	if cache.has(original):return cache[original]
	var mat:ShaderMaterial
	if original is ShaderMaterial:
		mat=original.duplicate();mat.shader=cut_shader(original.shader)
	elif original is StandardMaterial3D:
		# This temporary scan surface uses the existing authored archive pass.
		# Settled rendering never substitutes it for the reviewed material.
		mat=ShaderMaterial.new();mat.shader=cut_shader(load("res://collection/surface.gdshader"))
		mat.set_shader_parameter("tint",original.albedo_color);mat.set_shader_parameter("metallic",original.metallic);mat.set_shader_parameter("roughness",original.roughness)
		mat.set_shader_parameter("roughness_floor",0.);mat.set_shader_parameter("coat",original.clearcoat if original.clearcoat_enabled else 0.)
		mat.set_shader_parameter("coat_roughness",original.clearcoat_roughness);mat.set_shader_parameter("normal_depth",original.normal_scale)
		mat.set_shader_parameter("anisotropy_strength",original.anisotropy if original.anisotropy_enabled else 0.)
		for item in [["color",original.albedo_texture],["roughness",original.roughness_texture],["normal",original.normal_texture]]:
			mat.set_shader_parameter("has_"+item[0],item[1]!=null)
			if item[1]!=null:mat.set_shader_parameter(item[0]+"_map",item[1])
		mat.set_shader_parameter("emission_color",original.emission);mat.set_shader_parameter("emission_energy",original.emission_energy_multiplier if original.emission_enabled else 0.)
	else:assert(false,"Unsupported nautilus archive material");return null
	cache[original]=mat;return mat
func update(value:float,bounds:AABB)->void:
	if value<=0.:
		if active:
			for r in records:
				if r.index<0:r.mesh.material_override=r.original
				else:r.mesh.set_surface_override_material(r.index,r.original)
			records.clear();cache.clear();active=false
		return
	if not active:
		active=true
		for mesh in asset.find_children("*","MeshInstance3D",true,false):
			if mesh.material_override:
				records.append({"mesh":mesh,"index":-1,"original":mesh.material_override});mesh.material_override=converted(mesh.material_override)
			else:
				for i in range(mesh.mesh.get_surface_count()):
					records.append({"mesh":mesh,"index":i,"original":mesh.get_surface_override_material(i)})
					mesh.set_surface_override_material(i,converted(mesh.get_active_material(i)))
	for mat in cache.values():mat.set_shader_parameter("nautilus_cut",lerpf(bounds.end.y+.01,bounds.position.y-.01,clampf(value,0.,1.)))
func status()->Dictionary:return {"active":active,"wrapped_surfaces":records.size(),"unique_materials":cache.size(),"shader_variants":shaders.size(),"settled_uses_originals":not active}
