extends SceneTree
var out:="res://../review/I_refinement/nautilus_r1/port_envelope_r67/views/"
var camera:Camera3D
func _initialize()->void:run.call_deferred()
func _process(delta:float)->bool:RenderingServer.force_draw(false,delta);return false
func snap(name:String)->void:
	for i in range(6):await RenderingServer.frame_post_draw
	root.get_texture().get_image().save_png(out+name+".png");print("PORT_VIEW ",name)
func run()->void:
	RenderingServer.set_render_loop_enabled(false)
	var report:="res://../review/I_refinement/nautilus_r1/port_envelope_r67/build.json"
	for arg in OS.get_cmdline_user_args():
		if arg.begins_with("--report="):report=arg.trim_prefix("--report=");out=report.get_base_dir()+"/views/"
		if arg=="--smooth":report=report.replace("/build.json","/smooth_r3/build.json");out=out.replace("/views/","/smooth_r3/views/")
		if arg=="--baseline":report="res://../review/I_refinement/nautilus_r1/curved_returns_r61/build.json";out=out.replace("/views/","/baseline_views/")
	DirAccess.make_dir_recursive_absolute(out);root.size=Vector2i(1000,900);root.transparent_bg=false;root.msaa_3d=Viewport.MSAA_4X
	var spec:Dictionary=JSON.parse_string(FileAccess.get_file_as_string(report))
	assert(FileAccess.get_sha256("res://"+str(spec.component).trim_prefix("app/"))==spec.component_sha256)
	var world:=Node3D.new();root.add_child(world)
	var body:Node3D=load("res://"+str(spec.component).trim_prefix("app/")).instantiate();world.add_child(body)
	var port:Node3D=body.find_child("IS18_Leg01_PortFrame",true,false);assert(port!=null)
	var isolated:=Node3D.new();world.add_child(isolated);isolated.global_transform=port.global_transform
	var liner:MeshInstance3D=body.find_child("IS18_Leg01_PortLiner",true,false)
	var seal:MeshInstance3D=body.find_child("IS18_Leg01_PortSeal",true,false)
	var skins:Array[Node3D]=[]
	for name in ["IN1_PorcelainPanel_01","IN1_PorcelainPanel_02"]:
		var skin:Node3D=body.find_child(name,true,false);assert(skin!=null);skin.reparent(isolated,true);skins.append(skin)
	liner.reparent(isolated,true);seal.reparent(isolated,true);body.queue_free();await process_frame
	var env:=Environment.new();env.background_mode=Environment.BG_COLOR;env.background_color=Color(.10,.11,.12);env.tonemap_mode=Environment.TONE_MAPPER_AGX
	var panorama:=PanoramaSkyMaterial.new();panorama.panorama=load("res://assets/studio_small_09_4k.exr");panorama.energy_multiplier=.35
	env.sky=Sky.new();env.sky.sky_material=panorama;env.ambient_light_source=Environment.AMBIENT_SOURCE_SKY;env.ambient_light_energy=.4;env.reflected_light_source=Environment.REFLECTION_SOURCE_SKY
	var environment:=WorldEnvironment.new();environment.environment=env;world.add_child(environment)
	var location:=isolated.to_global(Vector3(0,.17,0));var up:=isolated.global_basis.y.normalized();var right:=isolated.global_basis.x.normalized();var side:=isolated.global_basis.z.normalized()
	for row in [[right*.25+side*.2+up*.25,3.],[right*-.2+side*-.2+up*.2,2.]]:
		var light:=AreaLight3D.new();world.add_child(light);light.position=location+row[0];light.look_at(location,side);light.light_energy=row[1];light.area_size=Vector2(.15,.2);light.area_normalize_energy=true;light.area_range=2.
	camera=Camera3D.new();world.add_child(camera);camera.near=.001;camera.far=4.;camera.fov=34.;camera.current=true
	camera.position=location+right*.12+side*.10+up*.18;camera.look_at(location,side);await snap("assembled_front")
	for skin in skins:skin.hide()
	await snap("isolated_front")
	camera.position=location+right*.12+side*.12-up*.12;camera.look_at(location-up*.025,side);await snap("isolated_return")
	FileAccess.open(out+"receipt.json",FileAccess.WRITE).store_string(JSON.stringify({"source_sha256":spec.source_sha256,"component_sha256":spec.component_sha256,"scope":"Actual imported first port and actual source skins, isolated after assembled front view. Fixed camera for baseline/candidate comparison; not full App or art acceptance."},"  "))
	for light in world.find_children("*","AreaLight3D",true,false):light.queue_free()
	for i in range(3):await RenderingServer.frame_post_draw
	world.queue_free();await process_frame;quit()
