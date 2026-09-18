extends SceneTree
const OUT:="res://../review/F_complete/revision_20260911/lighting/"
const TUNED:={"field_gain":.55,"glints":.22,"ribbons":.36,"plumb_beam":.42,"receiver":.42,"hardware":.55,"lights":.52,"seed":.60}
var host:Node3D
var service:Node3D
var module:Node3D
var f:RefCounted
var fx:Node3D
var main_lights:Array=[]
var camera_home:Transform3D
var camera_fov:=0.
func _initialize()->void:run.call_deferred()
func capture(label:String)->void:
	for i in range(4):await RenderingServer.frame_post_draw
	host.render_view.get_texture().get_image().save_png(OUT+label+".png");print("F_LIGHTING_CAPTURE ",label)
func light_profile(energy:Array,ambient:float,size:float,radius:float)->void:
	host.env.ambient_light_energy=ambient;host.env.ssil_radius=radius
	for i in range(3):main_lights[i].light_energy=energy[i];main_lights[i].light_size=size
func hardware_only(enabled:bool)->void:
	fx.visible=not enabled
	if enabled:
		for material in module.instrument_materials:material.set_shader_parameter("instrument_gain",0.)
	else:fx.tick(0.,1.)
func console_view()->void:
	host.camera.global_position=Vector3(.15,1.22,4.);host.camera.look_at(Vector3(0,.32,1.0));host.camera.fov=43.
func gesture(index:int,value:float,event:String)->void:
	var driver:RefCounted=service.control_driver;driver.index=index;driver.active=driver.profile(index);driver._set_value(value,event);driver.index=-1;driver.active={}

func run()->void:
	set_meta("collection_no_save",true);set_meta("collection_no_audio",true);set_meta("collection_skip_intro",true)
	DirAccess.make_dir_recursive_absolute(OUT)
	var scene:Node=load("res://main.tscn").instantiate();root.add_child(scene)
	for i in range(10):await process_frame
	host=scene.get_node("Render/HeliosDesktop");host.set_process(false);host.power=1.;host.power_target=1.;host.muted=true;host.rotation_enabled=false;host.angle=0.
	service=host.collection;service._legacy_set_visible(false);service._set_base_frame("shared");service.rotation_hologram.linger=0.;service.rotation_hologram.review_pointer=Vector2(-10000,-10000)
	var data:Dictionary=JSON.parse_string(FileAccess.get_file_as_string("res://assets/collection/models/F_complete.json"))
	module=load("res://collection/module.gd").new();service.add_child(module);module.setup(host,data,load("res://assets/collection/models/F_complete.glb"));service.current=module;service.active_id="F";service._build_controls();host.tooltip.hide();host.toast.hide()
	f=module.play.instrument;fx=module.effect.f_visuals;fx.tuning={}
	for child in host.get_children():
		if child is AreaLight3D:main_lights.append(child)
	camera_home=host.camera.global_transform;camera_fov=host.camera.fov
	gesture(1,0.,"begin")
	for i in range(2400):
		service.tick(1./60.)
		if i%30==0:await RenderingServer.frame_post_draw
		if f.peak_time>=1.45:break
	assert(f.peak_time>=1.45,"Cannot inspect calibration without an actual earned peak")
	if OS.get_cmdline_user_args().has("--backdrops"):
		light_profile([24.,25.,4.],.35,.35,.30);fx.tuning=TUNED.duplicate(true);fx.tick(0.,1.)
		var bg:=ColorRect.new();bg.size=Vector2(root.size);bg.mouse_filter=Control.MOUSE_FILTER_IGNORE;bg.z_index=-100;root.add_child(bg)
		var holo:Node3D=service.rotation_hologram;holo.review_pointer=holo.screen_center();holo.tick(.5)
		for pair in [["white",Color.WHITE],["dark",Color(.025,.028,.032)]]:
			bg.color=pair[1]
			for i in range(5):await RenderingServer.frame_post_draw
			root.get_texture().get_image().save_png(OUT+"canvas_"+pair[0]+".png")
		fx.foil.material_override.set_shader_parameter("emission_scale",.30)
		for pair in [["white",Color.WHITE],["dark",Color(.025,.028,.032)]]:
			bg.color=pair[1]
			for i in range(5):await RenderingServer.frame_post_draw
			root.get_texture().get_image().save_png(OUT+"canvas_low_foil_"+pair[0]+".png")
		bg.queue_free();f=null;fx=null;module=null;service=null;host=null;scene.queue_free();await process_frame;await process_frame;quit();return
	var state:Dictionary=f.diagnostics();var profiles:Array=[]
	for row in [["A_baseline",[24.,32.,7.],.60,.65,1.0],["B_defined",[24.,25.,4.],.35,.35,.30],["C_soft",[22.,28.,4.],.40,.50,.38]]:
		light_profile(row[1],row[2],row[3],row[4]);hardware_only(true);await capture(row[0]+"_hardware")
		hardware_only(false);await capture(row[0]+"_original_fx")
		profiles.append({"id":row[0],"light_energy":row[1],"ambient":row[2],"light_size":row[3],"ssil_radius":row[4]})
	light_profile([24.,25.,4.],.35,.35,.30);fx.tuning=TUNED.duplicate(true);fx.tick(0.,1.);await capture("D_defined_tuned_fx")
	console_view();await capture("E_console_neutral")
	# These are actual pointer-layer input values; the mechanism and signed needle update naturally.
	gesture(5,1.,"change");gesture(1,.5,"change")
	for i in range(600):
		service.tick(1./60.)
		if i%60==0:await RenderingServer.frame_post_draw
	await capture("F_console_positive_bias")
	host.camera.global_transform=camera_home;host.camera.fov=camera_fov;await capture("G_bias_tuned_fx")
	var result:={"physical_peak_state":state,"console_projection":service.f_console.export_projection(),"console_projected":service.f_console.projected,"profiles":profiles,"candidate_fx":TUNED,"end_state":f.diagnostics(),"scope":"Actual Metal renderer; pose held constant for light-only and original/tuned effect A/B. Selected B light and D FX values are now in F configuration; source sync and native input remain pending. No native input or frame-rate acceptance."}
	FileAccess.open(OUT+"review.json",FileAccess.WRITE).store_string(JSON.stringify(result,"  "))
	f=null;fx=null;module=null;service=null;host=null;scene.queue_free();await process_frame;await process_frame;quit()
