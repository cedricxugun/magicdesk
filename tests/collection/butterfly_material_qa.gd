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
	set_meta("collection_no_audio",true)
	set_meta("collection_skip_intro",true);set_meta("collection_no_save",true);DirAccess.make_dir_recursive_absolute(OUT)
	var scene:Node=load("res://main.tscn").instantiate();root.add_child(scene)
	for i in range(10):await process_frame
	host=scene.get_node("Render/HeliosDesktop");host.set_process(false);host.power=1.;host.power_target=1.;host.muted=true;host.rotation_enabled=false;host.angle=0;service=host.collection
	service._legacy_set_visible(false);service._set_base_frame("shared");host.tooltip.hide();host.toast.hide()
	var data:Dictionary=JSON.parse_string(FileAccess.get_file_as_string("res://assets/collection/models/G_optical_curator_butterfly_candidate.json"))
	module=load("res://collection/module.gd").new();service.add_child(module);module.setup(host,data,load("res://assets/collection/models/G_optical_curator_butterfly_candidate.glb"));player=module.play.g_instrument;cue=module.effect.g_visuals.observatory_performance;service.current=module;service.active_id="G";service._build_controls()
	var root_node:Node3D=player.content[1].node
	var families:Dictionary={};var changed:=0;var outside:=0;var shared:=0
	var cache_ids:Array=[]
	for mat in module.material_cache.values():cache_ids.append(mat.get_instance_id())
	for mesh in module.meshes:
		for i in range(mesh.mesh.get_surface_count()):
			var mat:Material=mesh.get_active_material(i)
			if not mat.has_meta("butterfly_finish"):continue
			changed+=1;families[mat.get_meta("butterfly_finish")]=true
			if not root_node.is_ancestor_of(mesh):outside+=1
			if mat.get_instance_id() in cache_ids:shared+=1
	var result:={"passed":changed>0 and families.size()==6 and outside==0 and shared==0,"finished_surfaces":changed,"families":families.keys(),"outside_butterfly":outside,"shared_cache_mutations":shared,"scope":"Inspect actual materials after collection setup; verify finish copies do not recolor other G content or shared resources"}
	FileAccess.open(OUT+"isolation_qa.json",FileAccess.WRITE).store_string(JSON.stringify(result,"  "));print("BUTTERFLY_MATERIAL_QA ",JSON.stringify(result))
	player=null;cue=null;module=null;service=null;host=null
	for audio in scene.find_children("*","AudioStreamPlayer",true,false):audio.stop()
	scene.queue_free();await process_frame;await create_timer(.08).timeout;quit(0 if result.passed else 2)
