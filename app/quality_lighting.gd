extends RefCounted

# Calibrated with the same 4K studio HDR and material textures as the Blender
# reference. These values only alter illumination and surface response: the
# camera, model scale, animation transforms and desktop window remain untouched.
static func apply(root: Node3D, env: Environment, materials: Dictionary) -> void:
	var panorama := env.sky.sky_material as PanoramaSkyMaterial
	panorama.panorama = load("res://assets/studio_small_09_4k.exr")
	panorama.energy_multiplier = 0.32
	env.sky_rotation = Vector3.ZERO
	env.ambient_light_energy = 0.50
	env.adjustment_enabled = true
	env.adjustment_contrast = 1.09
	env.adjustment_saturation = 1.02
	env.tonemap_exposure = 1.0
	var energy := [24.0, 34.0, 4.0]
	var light_index := 0
	for child in root.get_children():
		if child is AreaLight3D:
			# A smaller depth bias produces visible triangle-shaped self-shadow
			# acne on the enamel and the curved fascia in Godot's area shadows.
			child.shadow_normal_bias = 0.10
			child.shadow_bias = 0.10
			if light_index < energy.size():
				child.light_energy = energy[light_index]
			light_index += 1
	if materials.has("Polished_Nickel"):
		# Retain the original roughness map, with a narrower polished lobe.
		materials.Polished_Nickel.set_shader_parameter("surface_roughness", 0.78)
		materials.Polished_Nickel.set_shader_parameter("metal_tone",1.12)
	if materials.has("Dark_Brushed_Steel"):
		materials.Dark_Brushed_Steel.set_shader_parameter("surface_roughness", 0.96)
		materials.Dark_Brushed_Steel.set_shader_parameter("metal_tone",1.32)
	if materials.has("Ivory_Enamel"):
		var ceramic:ShaderMaterial=materials.Ivory_Enamel
		ceramic.set_shader_parameter("color_map",load("res://assets/ceramic_ivory_albedo.png"))
		ceramic.set_shader_parameter("rough_map",load("res://assets/ceramic_glaze_roughness.png"))
		ceramic.set_shader_parameter("normal_map",load("res://assets/ceramic_glaze_normal.png"))
		ceramic.set_shader_parameter("use_color_map",true)
		ceramic.set_shader_parameter("use_rough_map",true)
		ceramic.set_shader_parameter("use_normal_map",true)
		ceramic.set_shader_parameter("surface_roughness",1.0)
		ceramic.set_shader_parameter("metalness",0.0)
		ceramic.set_shader_parameter("enamel_balance",0.0)
		ceramic.set_shader_parameter("coat",0.42)
		ceramic.set_shader_parameter("coat_roughness",0.105)
		ceramic.set_shader_parameter("normal_depth",0.20)
	for key in ["Polished_Nickel", "Dark_Brushed_Steel", "Warm_Nickel", "Graphite"]:
		if materials.has(key):
			materials[key].set_shader_parameter("patina",0.14 if key!="Graphite" else 0.06)
			materials[key].set_shader_parameter("brushed",0.65 if key=="Polished_Nickel" else 0.9)
	make_base_surface(root)

# Localize the heavier machining and wear to the stationary pedestal and its
# turntable deck. Duplicate only their material instances, not geometry or UVs.
static func make_base_surface(node: Node) -> void:
	if node is MeshInstance3D and (node.name=="BASE_FIXED_DisplayMesh" or node.name=="TURNTABLE_DisplayMesh"):
		for i in range(node.mesh.get_surface_count()):
			var source=node.get_active_material(i)
			if source is ShaderMaterial:
				var mat:=source.duplicate() as ShaderMaterial
				mat.set_shader_parameter("base_surface",1.0)
				var metallic:float=mat.get_shader_parameter("metalness")
				mat.set_shader_parameter("patina",0.28 if metallic>0.5 else 0.14)
				mat.set_shader_parameter("brushed",1.0 if metallic>0.5 else 0.0)
				node.set_surface_override_material(i,mat)
	for child in node.get_children():make_base_surface(child)
