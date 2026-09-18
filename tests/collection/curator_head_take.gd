extends SceneTree
var host:Node3D
var module:Node3D
var player:RefCounted
const OUT:="res://../review/G_optical_curator/head/"
func _initialize()->void:run.call_deferred()
func seconds(value:float)->void:
	for i in range(ceili(value*30)):
		module.tick(1./30.,1.);await RenderingServer.frame_post_draw
func capture(label:String)->void:
	await RenderingServer.frame_post_draw
	host.render_view.get_texture().get_image().save_png(OUT+label+".png")
func run()->void:
	set_meta("collection_skip_intro",true);set_meta("collection_no_save",true)
	DirAccess.make_dir_recursive_absolute(OUT)
	var scene:Node=load("res://main.tscn").instantiate();root.add_child(scene)
	for i in range(10):await process_frame
	host=scene.get_node("Render/HeliosDesktop");host.set_process(false);host.power=1.;host.muted=true;host.rotation_enabled=false;host.angle=0
	host.collection._legacy_set_visible(false);host.collection.selector.hide();host.fixed_base.hide();host.tooltip.hide();host.toast.hide()
	module=load("res://collection/module.gd").new();host.add_child(module)
	var data:Dictionary=JSON.parse_string(FileAccess.get_file_as_string("res://assets/collection/models/G_optical_curator.json"))
	module.setup(host,data,load("res://assets/collection/models/G_optical_curator.glb"));player=module.play.g_instrument
	host.collection.lighting.select("G");host.collection.lighting.tick(1.)
	for part in module.parts:
		var keep:bool=str(part.node.name).contains("Wrist") or str(part.node.name) in data.optical_curator.get("head_service",{}).get("service_parts",[])
		if not keep:part.node.hide()
	await seconds(.4)
	var face:Node3D=module.named(data.optical_curator.face);var target:=face.global_position
	host.camera.global_position=target+Vector3(.20,.10,1.4);host.camera.look_at(target);host.camera.fov=33
	await seconds(.1);await capture("01_watch")
	await seconds(1.6);await capture("02_curious")
	await seconds(2.5);await capture("03_blink")
	await seconds(2.3);await capture("04_proud")
	await seconds(3.4);await capture("05_drowsy")
	module.stow();await seconds(.8);await capture("06_closed_iris")
	print("CURATOR_HEAD_TAKE_COMPLETE");player=null;module=null;host=null;scene.queue_free();await process_frame;await process_frame;quit()
