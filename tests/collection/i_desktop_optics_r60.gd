extends SceneTree
var host:Node3D
var service:Node3D
var out:="res://../review/I_refinement/nautilus_r1/desktop_optics_r60/take_r3/"
var receipts:Array=[]
func _initialize()->void:run.call_deferred()
func _process(delta:float)->bool:
	RenderingServer.force_draw(false,delta);return false
func until(predicate:Callable,seconds:float=90.)->bool:
	var started:=Time.get_ticks_msec()
	while not predicate.call():
		if Time.get_ticks_msec()-started>seconds*1000.:return false
		await process_frame
	return true
func capture(label:String)->void:
	for i in range(8):await RenderingServer.frame_post_draw
	var picture:Image=host.render_view.get_texture().get_image();picture.save_png(out+label+".png")
	var a:Node3D=service.current.assembly
	var corners:Array=[]
	for v in a.music.staff.sheet.mesh.get_faces():
		var p:Vector2=host.camera.unproject_position(a.music.staff.sheet.to_global(v));corners.append([p.x,p.y])
	receipts.append({"label":label,"lighting":service.lighting.current.duplicate(true),"staff":a.music.staff.status.duplicate(true),"corners":corners,"size":[picture.get_width(),picture.get_height()],"native_msaa":host.render_view.msaa_3d,"coverage":a.music.staff.material.get_shader_parameter("ink_coverage_gain"),"backing":a.music.staff.material.get_shader_parameter("optical_backing"),"tile_gradients":a.music.staff.material.get_shader_parameter("tile_gradients")})
	print("I_OPTICS_CAPTURE ",label)
func set_score(quarter:float)->void:
	var staff:Node3D=service.current.assembly.music.staff
	for i in range(60):
		staff.set_score_position(1,quarter,1.)
		await process_frame
		if staff.status.ready:break
	assert(staff.status.ready)
	staff.set_music_response(.25,true,true)
func run()->void:
	RenderingServer.set_render_loop_enabled(false)
	set_meta("collection_skip_intro",true);set_meta("collection_no_save",true)
	DirAccess.make_dir_recursive_absolute(out)
	var scene:Node=load("res://main.tscn").instantiate();root.add_child(scene);current_scene=scene;host=scene.get_node("Render/HeliosDesktop")
	await create_timer(2.).timeout;service=host.collection;host.rotation_enabled=false;host.angle=0.
	service.request_model("I");assert(await until(func():return service.active_id=="I" and service.state=="idle"))
	host.activate(1);assert(await until(func():return service.current.assembly.music.transport.state=="playing"))
	service.current.assembly.music.seek(12.);await create_timer(.15).timeout;service.current.assembly.music.toggle()
	await process_frame;host.set_process(false)
	var initial_camera:Transform3D=host.camera.global_transform
	var baseline:Dictionary=service.lighting.baseline.duplicate(true)
	await set_score(32.)
	var mat:ShaderMaterial=service.current.assembly.music.staff.material
	mat.set_shader_parameter("tile_gradients",false);mat.set_shader_parameter("ink_coverage_gain",1.)
	await capture("01_baseline")
	service.lighting.profiles["I"]=JSON.parse_string(FileAccess.get_file_as_string("res://../review/I_refinement/nautilus_r1/desktop_optics_r60/lighting_candidate.json"))
	service.lighting.select("B");service.lighting.tick(1.);service.lighting.select("I");service.lighting.tick(1.)
	await capture("02_light_candidate")
	mat.set_shader_parameter("tile_gradients",true);mat.set_shader_parameter("ink_coverage_gain",1.35)
	await capture("03_light_and_coverage")
	# Observe true tile boundaries while retaining identical camera and geometry.
	await set_score(10.820927899100099);mat.set_shader_parameter("tile_gradients",false);mat.set_shader_parameter("ink_coverage_gain",1.)
	await capture("04_seam_baseline")
	mat.set_shader_parameter("tile_gradients",true);mat.set_shader_parameter("ink_coverage_gain",1.35)
	await capture("05_seam_candidate")
	assert(host.camera.global_transform==initial_camera)
	host.env.glow_enabled=false;await capture("06_glow_off")
	host.env.glow_enabled=true;await capture("07_glow_on")
	var energies:Array=[]
	for binding in service.current.assembly.chambers.bindings:
		energies.append(binding.light.light_energy);binding.light.light_energy=0.
	await capture("08_local_spill_off")
	for i in range(energies.size()):service.current.assembly.chambers.bindings[i].light.light_energy=energies[i]
	await capture("09_local_spill_on")
	var sheet:MeshInstance3D=service.current.assembly.music.staff.sheet
	var focus:Vector3=sheet.global_transform*sheet.get_aabb().get_center()
	host.camera.global_position=focus+(host.camera.global_position-focus).normalized()*2.6
	host.camera.look_at(focus)
	mat.set_shader_parameter("tile_gradients",false);mat.set_shader_parameter("ink_coverage_gain",1.)
	await capture("10_score_close_baseline")
	mat.set_shader_parameter("tile_gradients",true);mat.set_shader_parameter("ink_coverage_gain",1.35)
	await capture("11_score_close_candidate")
	host.camera.global_transform=initial_camera
	service.lighting.select("B");service.lighting.tick(1.)
	assert(service.lighting.current==baseline,"B lighting did not restore exactly")
	FileAccess.open(out+"receipts.json",FileAccess.WRITE).store_string(JSON.stringify({"captures":receipts,"B_light_state_restored":true,"scope":"Real main viewport, same paused assembly pose and fixed score/camera. Static lighting and sampling comparisons, not musical alignment, motion or final visual acceptance."},"  "))
	for audio in host.find_children("*","AudioStreamPlayer",true,false):audio.stop()
	for audio in host.find_children("*","AudioStreamPlayer3D",true,false):audio.stop()
	await create_timer(.3).timeout;quit()
