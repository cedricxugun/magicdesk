extends SceneTree
## Render the actual shared base without the HELIOS upper assembly.
## New image-generation references must not carry the egg silhouette forward.

func _initialize() -> void:
	render.call_deferred()

func render() -> void:
	root.size = Vector2i(1200,900)
	root.position = Vector2i(-12000,-12000)
	root.unfocusable = true
	root.transparent = true
	root.transparent_bg = true
	root.msaa_3d = Viewport.MSAA_4X
	var stage := Node3D.new()
	root.add_child(stage)
	var model: Node3D = load("res://assets/helios_model.glb").instantiate()
	stage.add_child(model)
	var upper := model.find_child("TURNTABLE",true,false)
	upper.get_parent().remove_child(upper)
	upper.queue_free()
	var world := WorldEnvironment.new()
	var environment := Environment.new()
	environment.background_mode = Environment.BG_CLEAR_COLOR
	environment.ambient_light_source = Environment.AMBIENT_SOURCE_SKY
	environment.reflected_light_source = Environment.REFLECTION_SOURCE_SKY
	environment.ambient_light_energy = .65
	environment.tonemap_mode = Environment.TONE_MAPPER_ACES
	var sky := Sky.new()
	var panorama := PanoramaSkyMaterial.new()
	panorama.panorama = load("res://assets/studio_small_09_4k.exr")
	panorama.energy_multiplier = .7
	sky.sky_material = panorama
	environment.sky = sky
	world.environment = environment
	stage.add_child(world)
	for settings in [[Vector3(-3,5,4),1.6],[Vector3(4,2,1),.8],[Vector3(1,3,-4),1.1]]:
		var light := DirectionalLight3D.new()
		stage.add_child(light)
		light.light_energy = settings[1]
		light.look_at_from_position(settings[0],Vector3(0,.3,0))
	var camera := Camera3D.new()
	stage.add_child(camera)
	camera.projection = Camera3D.PROJECTION_ORTHOGONAL
	camera.size = 3.3
	camera.look_at_from_position(Vector3(3.8,3.2,6.6),Vector3(0,.3,0))
	camera.current = true
	for i in range(8):await process_frame
	await RenderingServer.frame_post_draw
	var output := ""
	for arg in OS.get_cmdline_user_args():
		if arg.begins_with("--output="):output=arg.trim_prefix("--output=")
	if output.is_empty():quit(2);return
	var img := root.get_texture().get_image()
	var result := img.save_png(output)
	print("BASE_REFERENCE ",output," saved=",result==OK," used_rect=",img.get_used_rect())
	quit(0 if result==OK else 2)
