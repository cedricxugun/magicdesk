extends SceneTree
## Isolated lighting comparisons on identical geometry, pose and camera.
const OUT:="res://../review/G_optical_curator/lighting/"
var host:Node3D
var module:Node3D
var lights:Array=[]
var light_baselines:Array=[]
var ambient_baseline:float
var ssil_baseline:float
func _initialize()->void:run.call_deferred()
func settle()->void:
	for i in range(12):await RenderingServer.frame_post_draw
func capture(label:String)->void:
	await settle()
	var image:Image=host.render_view.get_texture().get_image()
	image.get_region(image.get_used_rect().grow(2).intersection(Rect2i(Vector2i.ZERO,image.get_size()))).save_png(OUT+label+".png")
func reset()->void:
	host.env.ssil_enabled=true;host.env.ssil_radius=ssil_baseline;host.env.ambient_light_energy=ambient_baseline
	for i in range(lights.size()):
		var l:Light3D=lights[i]
		for key in light_baselines[i]:l.set(key,light_baselines[i][key])
func run()->void:
	set_meta("collection_skip_intro",true);set_meta("collection_no_save",true);DirAccess.make_dir_recursive_absolute(OUT)
	var scene:Node=load("res://main.tscn").instantiate();root.add_child(scene)
	for i in range(10):await process_frame
	host=scene.get_node("Render/HeliosDesktop");host.set_process(false);host.power=1.;host.muted=true;host.rotation_enabled=false;host.angle=0
	host.collection._legacy_set_visible(false);host.collection._set_base_frame("shared");host.tooltip.hide();host.toast.hide()
	module=load("res://collection/module.gd").new();host.collection.add_child(module)
	var data:Dictionary=JSON.parse_string(FileAccess.get_file_as_string("res://assets/collection/models/G_optical_curator.json"))
	module.setup(host,data,load("res://assets/collection/models/G_optical_curator.glb"));host.collection.current=module;host.collection.active_id="G";host.collection._build_controls()
	# Explicit previous optical response keeps this A/B reproducible after
	# the selected candidate has been integrated into production defaults.
	module.play.g_instrument.face_material.set_shader_parameter("face_specular",.5)
	module.play.g_instrument.face_material.set_shader_parameter("face_coat",.4)
	module.play.g_instrument.face_material.set_shader_parameter("face_roughness",.23)
	for child in host.get_children():
		if child is AreaLight3D:lights.append(child)
	assert(lights.size()==3)
	ambient_baseline=host.env.ambient_light_energy;ssil_baseline=host.env.ssil_radius
	for light in lights:
		var saved:Dictionary={}
		for key in ["shadow_enabled","light_size","light_specular","shadow_normal_bias","shadow_bias","light_energy"]:saved[key]=light.get(key)
		light_baselines.append(saved)
	for i in range(15):module.tick(1./30.,1.);await RenderingServer.frame_post_draw
	var camera_home:Transform3D=host.camera.global_transform;var fov:float=host.camera.fov
	await capture("00_baseline_whole")
	var target:Vector3=module.named(data.optical_curator.face).global_position
	host.camera.global_position=target+Vector3(.20,.10,1.4);host.camera.look_at(target);host.camera.fov=33
	await capture("01_baseline_head")
	host.env.ssil_enabled=false;await capture("02_no_ssil")
	reset()
	for l in lights:l.light_size=0.
	await capture("03_no_pcss")
	reset()
	for l in lights:l.light_specular=0.
	await capture("04_no_light_specular")
	reset()
	for l in lights:l.shadow_enabled=false
	await capture("05_no_light_shadow")
	reset();host.env.ssil_radius=.25;host.env.ambient_light_energy=.40
	for i in range(lights.size()):lights[i].light_size=.065;lights[i].light_energy=[20.,22.,3.][i]
	await capture("06_balanced_candidate_head")
	var face_material:ShaderMaterial=module.play.g_instrument.face_material
	face_material.set_shader_parameter("face_specular",.20);face_material.set_shader_parameter("face_coat",.10);face_material.set_shader_parameter("face_roughness",.22)
	await capture("08_coated_optical_candidate_head")
	host.camera.global_transform=camera_home;host.camera.fov=fov
	await capture("07_balanced_candidate_whole")
	FileAccess.open(OUT+"probe.json",FileAccess.WRITE).store_string(JSON.stringify({"model_sha256":FileAccess.get_sha256("res://assets/collection/models/G_optical_curator.glb"),"same_pose":true,"production_changed":false,"baseline":{"ambient":ambient_baseline,"ssil_radius":ssil_baseline,"lights":light_baselines},"variants":["baseline","no_ssil","no_pcss","no_light_specular","no_light_shadow","balanced_candidate","coated_optical"],"candidate":{"ambient":.40,"ssil_radius":.25,"energies":[20,22,3],"pcss_size":.065,"optical_specular":.20,"optical_coat":.10}},"  "))
	print("CURATOR_LIGHTING_PROBE_COMPLETE");module=null;host=null;scene.queue_free();await process_frame;await process_frame;quit()
