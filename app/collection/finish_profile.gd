extends RefCounted
## Applies a named finish to already-isolated surface copies.
static func apply(materials:Array,profile_path:String,tag:String)->int:
	var profile:Dictionary=JSON.parse_string(FileAccess.get_file_as_string(profile_path))
	var count:=0
	for mat:ShaderMaterial in materials:
		var source:String=mat.get_meta("source_material","")
		var key:=source.trim_prefix("Collection_").get_slice(".",0)
		if not profile.materials.has(key):continue
		var spec:Dictionary=profile.materials[key];var rgb:Array=spec.color
		mat.set_shader_parameter("tint",Color(rgb[0],rgb[1],rgb[2]).linear_to_srgb())
		for name in ["metallic","roughness","coat","coat_roughness","specular_strength","anisotropy_strength"]:mat.set_shader_parameter(name,spec[name])
		mat.set_shader_parameter("roughness_floor",.08)
		mat.set_shader_parameter("roughness_scale",spec.get("roughness_scale",1.0))
		mat.set_shader_parameter("roughness_offset",spec.get("roughness_offset",0.0))
		mat.set_shader_parameter("has_color",false)
		mat.set_shader_parameter("has_roughness",spec.has("roughness_map"))
		mat.set_shader_parameter("has_normal",spec.has("normal_map"))
		if spec.has("roughness_map"):mat.set_shader_parameter("roughness_map",load(spec.roughness_map))
		if spec.has("normal_map"):
			mat.set_shader_parameter("normal_map",load(spec.normal_map));mat.set_shader_parameter("normal_depth",spec.normal_depth)
		mat.set_meta(tag,key);count+=1
	return count
