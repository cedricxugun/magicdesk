extends SceneTree
const OUT:="res://../review/G_optical_curator/butterfly_r2/materials/"
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
	if baseline:set_meta("butterfly_finish_baseline",true)
	set_meta("collection_skip_intro",true);set_meta("collection_no_save",true);DirAccess.make_dir_recursive_absolute(OUT)
	var scene:Node=load("res://main.tscn").instantiate();root.add_child(scene)
	for i in range(10):await process_frame
	host=scene.get_node("Render/HeliosDesktop");host.set_process(false);host.power=1.;host.power_target=1.;host.muted=true;host.rotation_enabled=false;host.angle=0;service=host.collection
	service._legacy_set_visible(false);service._set_base_frame("shared");host.tooltip.hide();host.toast.hide()
	var data:Dictionary=JSON.parse_string(FileAccess.get_file_as_string("res://assets/collection/models/G_optical_curator_butterfly_candidate.json"))
	module=load("res://collection/module.gd").new();service.add_child(module);module.setup(host,data,load("res://assets/collection/models/G_optical_curator_butterfly_candidate.glb"));player=module.play.g_instrument;cue=module.effect.g_visuals.observatory_performance;service.current=module;service.active_id="G";service._build_controls()
	input(1,1.,"begin")
	for i in range(600):
		await step(1)
		if player.stage=="playing":break
	assert(player.stage=="playing")
	input(3,0.,"change");await step(45)
	var label:="before" if baseline else "after"
	await capture(label+"_desktop")
	var target:Vector3=module.named(data.record_player.print_root).global_position+Vector3.UP*.58
	host.camera.global_position=target+Vector3(.22,.45,2.1);host.camera.look_at(target);host.camera.fov=43
	await step(3);await capture(label+"_close")
	var specs:Array=[]
	for mat in module.effect.g_visuals.surface_sets[1]:
		var row:={"name":mat.get_meta("source_material","")}
		for name in ["metallic","roughness","roughness_scale","roughness_offset","coat","coat_roughness","has_normal","normal_depth"]:row[name]=mat.get_shader_parameter(name)
		specs.append(row)
	FileAccess.open(OUT+label+"_materials.json",FileAccess.WRITE).store_string(JSON.stringify(specs,"  "))
	player=null;cue=null;module=null;service=null;host=null;scene.queue_free();await process_frame;await process_frame;quit()
