extends SceneTree
## Render the current source through the same material/light host as the app.
func _initialize()->void:run.call_deferred()
func run()->void:
	set_meta("collection_skip_intro",true);set_meta("collection_no_save",true)
	var scene:Node=load("res://main.tscn").instantiate();root.add_child(scene)
	for i in range(10):await process_frame
	var host:Node3D=scene.get_node("Render/HeliosDesktop");host.set_process(false);host.power=1.;host.muted=true;host.rotation_enabled=false;host.angle=0
	host.collection._legacy_set_visible(false);host.collection.selector.hide();host.fixed_base.hide();host.tooltip.hide();host.toast.hide()
	if host.collection.current:host.collection.current.hide()
	var model:Node3D=load("res://collection/module.gd").new();host.add_child(model)
	model.setup(host,JSON.parse_string(FileAccess.get_file_as_string("res://assets/collection/models/G_optical_curator.json")),load("res://assets/collection/models/G_optical_curator.glb"))
	host.collection.lighting.select("G");host.collection.lighting.tick(1.)
	for i in range(30):model.tick(1./30.,1.)
	host.render_view.size=Vector2i(320,384)
	host.camera.global_position=Vector3(.3,3.5,7);host.camera.look_at(Vector3(0,1.80,0));host.camera.projection=Camera3D.PROJECTION_ORTHOGONAL;host.camera.size=3.85
	for i in range(8):await RenderingServer.frame_post_draw
	var path:="res://assets/collection/thumbs/G_AI.png"
	var error:int=host.render_view.get_texture().get_image().save_png(path)
	print("CURATOR_THUMBNAIL_SAVED ",error);quit(error)
