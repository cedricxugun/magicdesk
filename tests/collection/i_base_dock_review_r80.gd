extends SceneTree
## Installed comparison and cutaway only; never a claim that the cutaway is an operating pose.
var world:Node3D
var camera:Camera3D
var out:String
var receipts:Array=[]
func _initialize()->void:run.call_deferred()
func _process(delta:float)->bool:RenderingServer.force_draw(false,delta);return false
func run()->void:
	RenderingServer.set_render_loop_enabled(false)
	var baseline:=OS.get_cmdline_user_args().has("--baseline")
	var directory:="coupling_repair_r76" if baseline else "base_dock_r80"
	var spec:Dictionary=JSON.parse_string(FileAccess.get_file_as_string("res://../review/I_refinement/nautilus_r1/"+directory+"/build.json"))
	assert(FileAccess.get_sha256("res://../"+spec.component)==spec.component_sha256)
	out=ProjectSettings.globalize_path("res://../review/I_refinement/nautilus_r1/base_dock_r80/"+("baseline/" if baseline else "views/")).simplify_path()+"/"
	if DirAccess.make_dir_recursive_absolute(out)!=OK:quit(2);return
	root.size=Vector2i(1600,1200);root.transparent_bg=false;root.msaa_3d=Viewport.MSAA_4X
	world=Node3D.new();root.add_child(world)
	var env:=Environment.new();env.background_mode=Environment.BG_COLOR;env.background_color=Color(.07,.078,.088);env.tonemap_mode=Environment.TONE_MAPPER_AGX
	var panorama:=PanoramaSkyMaterial.new();panorama.panorama=load("res://assets/studio_small_09_4k.exr");panorama.energy_multiplier=.3
	env.sky=Sky.new();env.sky.sky_material=panorama;env.ambient_light_source=Environment.AMBIENT_SOURCE_SKY;env.ambient_light_energy=.42;env.reflected_light_source=Environment.REFLECTION_SOURCE_SKY
	var environment:=WorldEnvironment.new();environment.environment=env;world.add_child(environment)
	for row in [[Vector3(3.2,5.2,4),20.,Vector2(2.,3.)],[Vector3(-3.,4,-3),16.,Vector2(2.,3.)],[Vector3(4.,2.5,-5.),8.,Vector2(2.,3.)]]:
		var light:=AreaLight3D.new();world.add_child(light);light.position=row[0];light.look_at(Vector3(0,2.,0));light.light_energy=row[1];light.area_size=row[2];light.area_normalize_energy=true;light.area_range=18.;light.shadow_enabled=true;light.shadow_normal_bias=.10;light.shadow_bias=.10
	var body:Node3D=load("res://../"+spec.component).instantiate();world.add_child(body)
	load("res://collection/i_finish_r38.gd").apply(body,str(spec.finish_profile))
	var opening:RefCounted=load("res://collection/i_nautilus_form_driver.gd").new();opening.bind(body,spec)
	var mouth:Node3D=load("res://../"+spec.mouth_component).instantiate();world.add_child(mouth)
	var p:Array=spec.mouth_placement.p;var q:Array=spec.mouth_placement.q;var scales:Array=spec.mouth_placement.s
	mouth.transform=Transform3D(Basis(Quaternion(q[0],q[1],q[2],q[3])).scaled(Vector3(scales[0],scales[1],scales[2])),Vector3(p[0],p[1],p[2]))
	var donor:Node3D=load("res://assets/helios_model.glb" if baseline else "res://../"+spec.candidate_base_component).instantiate();world.add_child(donor)
	var base:Node3D=donor.find_child("BASE_FIXED",true,false);assert(base!=null);base.reparent(world,true);donor.queue_free()
	camera=Camera3D.new();world.add_child(camera);camera.far=30.;camera.current=true
	camera.position=Vector3(-1.4,3.9,6.8);camera.look_at(Vector3(-.15,1.85,0));camera.fov=37.
	if OS.get_cmdline_user_args().has("--motion"):
		out=out.path_join("../motion").simplify_path()+"/"
		DirAccess.make_dir_recursive_absolute(out+"frames")
		var homes:Dictionary={}
		for node in body.find_children("ID80*","MeshInstance3D",true,false):homes[node.get_path()]=node.global_transform
		var samples:Array=[]
		for frame in range(420):
			var time:=float(frame)/30.;var u:=0.
			if time>=2. and time<6.:u=smoothstep(2.,6.,time)
			elif time>=6. and time<8.:u=1.
			elif time>=8. and time<12.:u=1.-smoothstep(8.,12.,time)
			opening.set_opening(u)
			for path in homes:
				assert(root.get_node(path).global_transform==homes[path],"Normal opening moved the fixed dock")
			await RenderingServer.frame_post_draw
			if root.get_texture().get_image().save_png(out+"frames/%04d.png"%frame)!=OK:quit(5);return
			if frame%30==0:samples.append({"frame":frame,"opening":u})
			if frame%90==0:print("R80_FRAME ",frame)
		FileAccess.open(out+"receipt.json",FileAccess.WRITE).store_string(JSON.stringify({"source_sha256":spec.source_sha256,"component_sha256":spec.component_sha256,"frames":420,"fps":30,"fixed_dock_meshes":homes.size(),"fixed_dock_transform_check":true,"samples":samples,"scope":"Offline real-source closed/open/closed demonstration at normal playback speed. No service release, audio or native performance claim."},"  "))
		for light in world.find_children("*","AreaLight3D",true,false):light.queue_free()
		for i in range(3):await RenderingServer.frame_post_draw
		world.queue_free();await process_frame;quit();return
	await capture("01_installed_closed")
	opening.set_opening(1.);await capture("02_installed_open")
	camera.position=Vector3(2.2,1.65,3.4);camera.look_at(Vector3(0,1.05,0));camera.fov=29.;await capture("03_support_front")
	camera.position=Vector3(-2.2,1.65,-3.4);camera.look_at(Vector3(0,1.05,0));await capture("04_support_rear")
	var hidden:Array=[]
	for node in body.find_children("*","MeshInstance3D",true,false):
		if str(node.name).begins_with("IN1_Porcelain") or str(node.name).begins_with("IN1_Fixed") or str(node.name).begins_with("IN1_PanelRim") or str(node.name).contains("PortRim"):
			node.visible=false;hidden.append(str(node.name))
	await capture("05_metal_path_cutaway")
	FileAccess.open(out+"receipt.json",FileAccess.WRITE).store_string(JSON.stringify({"source_sha256":spec.source_sha256,"component_sha256":spec.component_sha256,"baseline":baseline,"cameras":receipts,"cutaway_hidden":hidden,"scope":"Actual installed candidate and explicitly hidden-skin structural inspection. Cutaway is diagnostic, not normal operation or exploded service."},"  "))
	for light in world.find_children("*","AreaLight3D",true,false):light.queue_free()
	for i in range(3):await RenderingServer.frame_post_draw
	world.queue_free();await process_frame;quit()
func capture(name:String)->void:
	for i in range(5):await RenderingServer.frame_post_draw
	if root.get_texture().get_image().save_png(out+name+".png")!=OK:quit(3);return
	receipts.append({"image":name,"position":[camera.position.x,camera.position.y,camera.position.z],"basis":str(camera.basis),"fov":camera.fov})
	print("R80_VIEW ",name)
