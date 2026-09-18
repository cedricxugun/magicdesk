extends SceneTree
## Current I candidate through the real desktop app, selector and shared base.
var host:Node3D
var elapsed:=0.
var ready:=false
func _initialize()->void:run.call_deferred()
func run()->void:
	set_meta("collection_skip_intro",true);set_meta("collection_no_save",true)
	set_meta("collection_registry","res://../review/I_refinement/nautilus_r1/main_adapter_r59/registry.json")
	var scene:Node=load("res://main.tscn").instantiate();root.add_child(scene);current_scene=scene
	host=scene.get_node("Render/HeliosDesktop")
	await create_timer(3.).timeout
	if host.collection==null:return
	host.rotation_enabled=false;host.angle=0.;host.collection.request_model("I");ready=true
func _process(delta:float)->bool:
	if not ready or not is_instance_valid(host) or host.collection==null:return false
	elapsed+=delta
	if elapsed>.5:
		elapsed=0.
		var report:Dictionary=host.collection.diagnostics()
		report["window_position"]=[root.position.x,root.position.y];report["window_size"]=[root.size.x,root.size.y]
		FileAccess.open("res://../review/I_refinement/nautilus_r1/main_adapter_r59/native_live.json",FileAccess.WRITE).store_string(JSON.stringify(report,"  "))
	return false
