extends SceneTree
## Isolated, recentered geometry diagnostic. No large-scene shadow pairing.
func _initialize()->void:run.call_deferred()
func _process(delta:float)->bool:RenderingServer.force_draw(false,delta);return false
func run()->void:
	RenderingServer.set_render_loop_enabled(false)
	root.size=Vector2i(1200,900);root.transparent_bg=false;root.msaa_3d=Viewport.MSAA_8X
	var out:=ProjectSettings.globalize_path("res://../review/I_refinement/nautilus_r1/coupling_repair_r76/macro/").simplify_path()+"/"
	DirAccess.make_dir_recursive_absolute(out)
	var spec:Dictionary=JSON.parse_string(FileAccess.get_file_as_string("res://../review/I_refinement/nautilus_r1/coupling_repair_r76/build.json"))
	var source:Node3D=load("res://../"+str(spec.component)).instantiate();root.add_child(source)
	var part:MeshInstance3D=source.find_child("IN3_CouplingBolt_00",true,false)
	if part==null:quit(2);return
	var mount:Node3D=source.find_child("IC1_MouthMount",true,false)
	var axis:Vector3=mount.global_basis.y.normalized()
	var side:Vector3=mount.global_basis.x.normalized()
	var center:Array=spec.coupling_threads.threads[0].center_parent
	# Frame the actual short threaded tip, not the long screw's AABB center.
	var location:Vector3=mount.global_transform*Vector3(center[0],.631,-center[1])
	var mesh:=MeshInstance3D.new();mesh.mesh=part.mesh;root.add_child(mesh)
	mesh.transform=part.global_transform;mesh.position-=location
	source.queue_free();await process_frame
	var env:=Environment.new();env.background_mode=Environment.BG_COLOR;env.background_color=Color(.03,.035,.043);env.tonemap_mode=Environment.TONE_MAPPER_AGX
	var panorama:=PanoramaSkyMaterial.new();panorama.panorama=load("res://assets/studio_small_09_4k.exr");panorama.energy_multiplier=.7
	env.sky=Sky.new();env.sky.sky_material=panorama;env.ambient_light_source=Environment.AMBIENT_SOURCE_SKY;env.reflected_light_source=Environment.REFLECTION_SOURCE_SKY
	var environment:=WorldEnvironment.new();environment.environment=env;root.add_child(environment)
	var light:=DirectionalLight3D.new();root.add_child(light);light.rotation_degrees=Vector3(-40,-35,0);light.light_energy=1.4;light.shadow_enabled=false
	var camera:=Camera3D.new();root.add_child(camera);camera.near=.0005;camera.far=.2;camera.fov=32.
	camera.position=side*.020-axis*.008;camera.look_at(Vector3.ZERO,axis);camera.current=true
	for i in range(6):await RenderingServer.frame_post_draw
	var result:=root.get_texture().get_image().save_png(out+"actual_screw.png")
	if result!=OK:quit(3);return
	FileAccess.open(out+"receipt.json",FileAccess.WRITE).store_string(JSON.stringify({"source_sha256":spec.source_sha256,"component_sha256":spec.component_sha256,
		"part":"IN3_CouplingBolt_00","scale_changed":false,"source_world_focus":[location.x,location.y,location.z],
		"scope":"Exact imported mesh, isolated/recentered for macro readability. Environment reflections and directional fill, no whole-assembly shadow culler."},"  "))
	mesh.queue_free();light.queue_free();environment.queue_free();camera.queue_free();await process_frame;quit()
