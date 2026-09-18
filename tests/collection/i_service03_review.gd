extends SceneTree
var out:="res://../review/I_refinement/nautilus_r1/service_r63/stage03/render/"
var driver:RefCounted
func _initialize()->void:run.call_deferred()
func _process(delta:float)->bool:RenderingServer.force_draw(false,delta);return false
func run()->void:
	var wide:=OS.get_cmdline_user_args().has("--wide")
	var stills:=OS.get_cmdline_user_args().has("--stills-only")
	out="res://../review/I_refinement/nautilus_r1/service_r63/"+("stage03_wide/" if wide else "stage03/")+("render_stills/" if stills else "render/")
	RenderingServer.set_render_loop_enabled(false);DirAccess.make_dir_recursive_absolute(out+"frames")
	root.size=Vector2i(1200 if wide else 1000,900);root.transparent_bg=false;root.msaa_3d=Viewport.MSAA_4X
	var s:Dictionary=JSON.parse_string(FileAccess.get_file_as_string("res://../review/I_refinement/nautilus_r1/curved_returns_r61/build.json"))
	var manifest:Dictionary=JSON.parse_string(FileAccess.get_file_as_string("res://assets/collection/art/I/service_r63/"+("service03_motion_wide.json" if wide else "service03_motion.json")))
	var world:=Node3D.new();root.add_child(world)
	var env:=Environment.new();env.background_mode=Environment.BG_COLOR;env.background_color=Color(.028,.030,.032);env.tonemap_mode=Environment.TONE_MAPPER_AGX
	var panorama:=PanoramaSkyMaterial.new();panorama.panorama=load("res://assets/studio_small_09_4k.exr");panorama.energy_multiplier=.30
	env.sky=Sky.new();env.sky.sky_material=panorama;env.ambient_light_source=Environment.AMBIENT_SOURCE_SKY;env.ambient_light_energy=.42;env.reflected_light_source=Environment.REFLECTION_SOURCE_SKY
	var environment:=WorldEnvironment.new();environment.environment=env;world.add_child(environment)
	for row in [[Vector3(-3.2,4.8,4),20.,Vector2(2.6,4.)],[Vector3(3.5,4,-2),24.,Vector2(1.2,3.5)],[Vector3(0,2.5,6),4.,Vector2(4.,2.)]]:
		var light:=AreaLight3D.new();world.add_child(light);light.position=row[0];light.look_at(Vector3(0,1.8,0));light.light_energy=row[1];light.area_size=row[2];light.area_normalize_energy=true;light.area_range=18.;light.shadow_enabled=true;light.shadow_normal_bias=.10
	var body:Node3D=load("res://"+str(s.component).trim_prefix("app/")).instantiate();world.add_child(body);load("res://collection/i_finish_r38.gd").apply(body,str(s.finish_profile))
	var opening:RefCounted=load("res://collection/i_nautilus_form_driver.gd").new();opening.bind(body,s);opening.set_opening(1.)
	var mouth:Node3D=load("res://"+str(s.mouth_component).trim_prefix("app/")).instantiate();world.add_child(mouth)
	var p:Array=s.mouth_placement.p;var q:Array=s.mouth_placement.q;var scale_values:Array=s.mouth_placement.s
	mouth.transform=Transform3D(Basis(Quaternion(q[0],q[1],q[2],q[3])).scaled(Vector3(scale_values[0],scale_values[1],scale_values[2])),Vector3(p[0],p[1],p[2]))
	var donor:Node3D=load("res://assets/helios_model.glb").instantiate();world.add_child(donor);var base:Node3D=donor.find_child("BASE_FIXED",true,false);base.reparent(world,true);donor.queue_free()
	driver=load("res://review/i_service03_driver.gd").new();driver.bind(body,s,manifest)
	var camera:=Camera3D.new();world.add_child(camera);camera.position=Vector3(3.,3.2,7.8);camera.look_at(Vector3(0,1.65,0));camera.fov=34.;camera.current=true
	var canvas:=CanvasLayer.new();root.add_child(canvas);var label:=Label.new();canvas.add_child(label);label.position=Vector2(24,20);label.text="03 号机构拆解检查 · 非整机完成";label.add_theme_font_size_override("font_size",20)
	var hint:=Label.new();canvas.add_child(hint);hint.position=Vector2(24,52);hint.text="真实端盖 / 销轴 / 连接舌 · 途中反向与回装";hint.add_theme_font_size_override("font_size",14)
	var samples:Array=[]
	for row in [["prepared",0.],["pin_withdrawn",1.15],["fork_released",2.05],["front_module_out",3.5]]:
		driver.seek(row[1])
		for i in range(5):await RenderingServer.frame_post_draw
		root.get_texture().get_image().save_png(out+row[0]+".png")
	if stills:driver.release();await process_frame;quit();return
	driver.seek(0.);driver.request(true)
	for frame in range(480):
		if frame==80:driver.request(false)
		if frame==140:driver.request(true)
		if frame==270:driver.request(false)
		driver.tick(1./30.)
		await RenderingServer.frame_post_draw
		root.get_texture().get_image().save_png(out+"frames/%04d.png"%frame)
		if frame%10==0:samples.append({"frame":frame,"time":driver.time,"target":driver.target,"velocity":driver.velocity})
	assert(driver.stowed())
	FileAccess.open(out+"receipt.json",FileAccess.WRITE).store_string(JSON.stringify({"frames":480,"fps":30,"stowed":driver.stowed(),"samples":samples,"body_source_sha256":s.source_sha256,"motion_source_sha256":manifest.motion_source_sha256,"scope":"Actual source body and authored service03 clip, fixed camera, three retained modules and mouth stationary, scripted reversals and final prepared-home return. Not full disassembly or native App acceptance."},"  "))
	driver.release();driver=null;await process_frame;quit()
