extends SceneTree
## Thumbnails come from the actual GLBs, not the concept illustrations.
var view:SubViewport
var world:Node3D
func _initialize()->void:run.call_deferred()
func run()->void:
	root.size=Vector2i(32,32);root.position=Vector2i(-32000,-32000);root.unfocusable=true
	view=SubViewport.new();view.size=Vector2i(320,384);view.own_world_3d=true;view.transparent_bg=true;view.msaa_3d=Viewport.MSAA_4X;view.render_target_update_mode=SubViewport.UPDATE_ALWAYS;root.add_child(view)
	world=Node3D.new();view.add_child(world)
	var env:=Environment.new();env.background_mode=Environment.BG_CLEAR_COLOR;env.ambient_light_source=Environment.AMBIENT_SOURCE_SKY;env.reflected_light_source=Environment.REFLECTION_SOURCE_SKY;env.ambient_light_energy=.65;env.tonemap_mode=Environment.TONE_MAPPER_AGX
	var sky:=Sky.new();var panorama:=PanoramaSkyMaterial.new();panorama.panorama=load("res://assets/studio_small_09_4k.exr");panorama.energy_multiplier=.45;sky.sky_material=panorama;env.sky=sky
	var environment:=WorldEnvironment.new();environment.environment=env;world.add_child(environment)
	for info in [[Vector3(-3,4,3),1.3],[Vector3(4,3,-2),1.1]]:
		var light:=DirectionalLight3D.new();world.add_child(light);light.position=info[0];light.look_at(Vector3(0,1.7,0));light.light_energy=info[1]
	var camera:=Camera3D.new();world.add_child(camera);camera.position=Vector3(.7,3.2,7);camera.look_at(Vector3(0,1.85,0));camera.projection=Camera3D.PROJECTION_ORTHOGONAL;camera.size=3.5;camera.current=true
	var config:Dictionary=JSON.parse_string(FileAccess.get_file_as_string("res://assets/collection/registry.json"))
	DirAccess.make_dir_recursive_absolute("res://assets/collection/thumbs")
	for definition in config.models:
		var model:Node3D
		if definition.id=="B":
			model=load(definition.scene).instantiate();world.add_child(model)
			model.find_child("BASE_FIXED",true,false).hide()
		else:
			model=load("res://collection/module.gd").new();world.add_child(model)
			var data:Dictionary=JSON.parse_string(FileAccess.get_file_as_string(definition.metadata))
			model.setup(world,data,load(definition.scene));model.set_interactive(false)
			model.tick(.016,1.0)
		var bounds:=visible_bounds(model)
		var center:=bounds.get_center()
		camera.position=center+Vector3(.7,1.35,7)
		camera.look_at(center)
		camera.size=maxf(bounds.size.y,bounds.size.x*384.0/320.0)*1.30
		for i in range(8):await process_frame
		await RenderingServer.frame_post_draw
		var image:=view.get_texture().get_image();var path:String=definition.thumbnail
		var result:=image.save_png(path)
		print("THUMBNAIL ",definition.id," saved=",result==OK," bounds=",image.get_used_rect())
		model.queue_free();await process_frame
	quit()

func visible_bounds(node:Node)->AABB:
	var result:=AABB()
	if node is MeshInstance3D and node.is_visible_in_tree():result=node.global_transform*node.get_aabb()
	for child in node.get_children():
		var box:=visible_bounds(child)
		if box.has_volume():result=result.merge(box) if result.has_volume() else box
	return result
