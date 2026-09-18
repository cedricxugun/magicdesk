extends SceneTree
const OUT:="res://../review/G_optical_curator/ship_r2/runtime/"
var host:Node3D
var module:Node3D
var service:Node3D
var player:RefCounted
var cue:Node3D
var checks:Array=[]
func _initialize()->void:run.call_deferred()
func step(count:int)->void:
	for i in range(count):service.tick(1./30.);await RenderingServer.frame_post_draw
func input(slot:int,value:float,event:String)->void:
	var driver:RefCounted=service.control_driver;driver.index=slot;driver.active=driver.profile(slot);driver._set_value(value,event)
	if slot!=5 or event=="release":driver.index=-1;driver.active={}
func capture(label:String)->void:
	await RenderingServer.frame_post_draw
	var image:Image=host.render_view.get_texture().get_image();image.get_region(image.get_used_rect().grow(2).intersection(Rect2i(Vector2i.ZERO,image.get_size()))).save_png(OUT+label+".png")
func run()->void:
	var baseline:=OS.get_cmdline_user_args().has("--baseline")
	if baseline:set_meta("observatory_material_baseline",true)
	set_meta("collection_no_audio",true);set_meta("collection_skip_intro",true);set_meta("collection_no_save",true);DirAccess.make_dir_recursive_absolute(OUT)
	var scene:Node=load("res://main.tscn").instantiate();root.add_child(scene)
	for i in range(10):await process_frame
	host=scene.get_node("Render/HeliosDesktop");host.set_process(false);host.power=1.;host.power_target=1.;host.muted=true;host.rotation_enabled=false;host.angle=0;service=host.collection
	service._legacy_set_visible(false);service._set_base_frame("shared");host.tooltip.hide();host.toast.hide()
	var data:Dictionary=JSON.parse_string(FileAccess.get_file_as_string("res://assets/collection/models/G_optical_curator_ship_candidate.json"))
	module=load("res://collection/module.gd").new();service.add_child(module);module.setup(host,data,load("res://assets/collection/models/G_optical_curator_ship_candidate.glb"));player=module.play.g_instrument;cue=module.effect.g_visuals.observatory_performance;service.current=module;service.active_id="G";service._build_controls()
	input(1,2.,"begin")
	for i in range(600):
		await step(1)
		if player.stage=="playing":break
	assert(player.stage=="playing")
	input(3,0.,"change");await step(15)
	var label:="before" if baseline else "after"
	await capture(label+"_desktop")
	var target:Vector3=module.named(data.record_player.print_root).global_position+Vector3.UP*.58
	host.camera.global_position=target+Vector3(.22,.45,2.1);host.camera.look_at(target);host.camera.fov=43
	await step(3);await capture(label+"_close")
	if OS.get_cmdline_user_args().has("--shade-audit"):
		var normals:Dictionary={}
		for mat in module.materials:
			if str(mat.get_meta("source_material","")).contains("Ship"):
				normals[mat]=mat.get_shader_parameter("normal_depth");mat.set_shader_parameter("normal_depth",0.0)
		await step(3);await capture("audit_no_normals")
		for mat in normals:mat.set_shader_parameter("normal_depth",normals[mat])
		var lamps:Array=host.find_children("*","Light3D",true,false);var shadows:Array=[]
		for lamp in lamps:shadows.append(lamp.shadow_enabled);lamp.shadow_enabled=false
		await step(3);await capture("audit_no_shadows")
		for i in range(lamps.size()):lamps[i].shadow_enabled=shadows[i]
		await step(3)
	if OS.get_cmdline_user_args().has("--shadow-bias-audit"):
		var lamps:Array=host.find_children("*","AreaLight3D",true,false)
		var old_bias:Array=[]
		for lamp in lamps:old_bias.append(lamp.shadow_normal_bias)
		for bias in [0.0,.015,.035,.065]:
			for lamp in lamps:lamp.shadow_normal_bias=bias
			await step(3);await capture("audit_bias_%03d"%roundi(bias*1000.0))
		for i in range(lamps.size()):lamps[i].shadow_normal_bias=old_bias[i]
		await step(3)
	if OS.get_cmdline_user_args().has("--shadow-source-audit"):
		var lamps:Array=host.find_children("*","Light3D",true,false);var sources:Array=[]
		for i in range(lamps.size()):
			var lamp:Light3D=lamps[i]
			sources.append({"index":i,"path":str(lamp.get_path()),"type":lamp.get_class(),"shadow":lamp.shadow_enabled,"energy":lamp.light_energy})
			if not lamp.shadow_enabled:continue
			lamp.shadow_enabled=false;await step(3);await capture("audit_lamp_%02d_off"%i);lamp.shadow_enabled=true
		FileAccess.open(OUT+"shadow_sources.json",FileAccess.WRITE).store_string(JSON.stringify(sources,"  "));print("SHIP_SHADOW_SOURCES ",JSON.stringify(sources))
	if OS.get_cmdline_user_args().has("--shadow-softness-audit"):
		var lamps:Array=host.find_children("*","AreaLight3D",true,false);var old_sizes:Array=[]
		for lamp in lamps:old_sizes.append(lamp.light_size)
		for size in [.13,.25,.40,.65]:
			for lamp in lamps:lamp.light_size=size
			await step(5);await capture("audit_softness_%03d"%roundi(size*1000.0))
		for i in range(lamps.size()):lamps[i].light_size=old_sizes[i]
		await step(3)
	var sail_materials:Array=[];var outside_metal_maps:=0
	for mat in module.materials:
		var source:String=mat.get_meta("source_material","")
		if source.contains("ShipMainSail") or source.contains("ShipJibSail"):
			sail_materials.append({"source":source,"metallic_map":mat.get_shader_parameter("has_metallic"),"metallic_channel":str(mat.get_shader_parameter("metallic_channel")),"has_normal":mat.get_shader_parameter("has_normal"),"normal_depth":mat.get_shader_parameter("normal_depth"),"coat":mat.get_shader_parameter("coat")})
		elif mat.get_shader_parameter("has_metallic")==true:outside_metal_maps+=1
	var sail_families:Dictionary={}
	for item in sail_materials:sail_families[item.source]=true
	var passed:bool=sail_families.size()==2 and outside_metal_maps==0 and sail_materials.all(func(m):return m.metallic_map and m.has_normal and m.coat==0.0)
	var report:={"passed":passed,"sail_materials":sail_materials,"sail_families":sail_families.keys(),"outside_metal_maps":outside_metal_maps,"stage":player.stage,"curiosity":player.loaded_index,"source_root":data.g_archive.contents[2].root,"scope":"Actual GPU scene static geometry/PBR review; new ship motion and VFX not implemented; not native input"}
	FileAccess.open(OUT+"geometry_review.json",FileAccess.WRITE).store_string(JSON.stringify(report,"  "))
	print("SHIP_GEOMETRY_QA ",JSON.stringify(report))
	player=null;cue=null;module=null;service=null;host=null;scene.queue_free();await process_frame;await process_frame;quit(0 if passed else 1)
