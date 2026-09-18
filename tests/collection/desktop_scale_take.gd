extends SceneTree
const OUT:="res://../review/desktop_scale/"
var host:Node3D
var service:Node3D
var checks:Array=[]
func _initialize()->void:run.call_deferred()
func check(name:String,passed:bool,details:Variant=null)->void:
	checks.append({"name":name,"passed":passed,"details":details})
func capture(label:String)->void:
	await RenderingServer.frame_post_draw
	host.render_view.get_texture().get_image().save_png(OUT+label+".png")
func step(count:int)->void:
	for i in range(count):
		service.tick(1./30.)
		await RenderingServer.frame_post_draw
func run()->void:
	set_meta("collection_no_save",true);set_meta("collection_no_audio",true);set_meta("collection_skip_intro",true)
	DirAccess.make_dir_recursive_absolute(OUT)
	var scene:Node=load("res://main.tscn").instantiate();root.add_child(scene)
	for i in range(12):await process_frame
	host=scene.get_node("Render/HeliosDesktop");host.set_process(false);host.muted=true;host.rotation_enabled=false;host.angle=0;service=host.collection
	host._set_desktop_zoom(1.0);host.toast.hide();host.tooltip.hide()
	var backing:float=DisplayServer.screen_get_scale(host.get_window().current_screen)
	var before:float=host.DesktopScale.base_width_pixels(host)
	var fixed:Transform3D=host.fixed_base.global_transform
	check("default_base_uses_logical_points",absf(before/backing-host.desktop_base_points)<.1,{"actual_points":before/backing,"target_points":host.desktop_base_points,"backing_scale":backing,"canvas":str(host.canonical_size)})
	await capture("01_default_B")
	var plus:=InputEventKey.new();plus.pressed=true;plus.meta_pressed=true;plus.keycode=KEY_EQUAL
	host._input(plus);host.toast.hide()
	check("command_plus_changes_projection",absf(host.DesktopScale.base_width_pixels(host)/before-1.1)<.001)
	check("zoom_does_not_resize_model",host.fixed_base.global_transform.is_equal_approx(fixed))
	var hits:Array=[]
	for i in range(host.buttons.size()):
		var pt:Vector2=host.camera.unproject_position(host.buttons[i].mount.global_position+host.buttons[i].mount.global_basis.y*.055)
		hits.append(host.hit_button(pt)==i)
	check("physical_buttons_still_pick_at_zoom",hits.all(func(ok):return ok),hits)
	await capture("02_larger_B")
	host._menu_action(37);host.toast.hide()
	check("menu_restores_default_size",absf(host.DesktopScale.base_width_pixels(host)-before)<.1)
	service._legacy_set_visible(false);service._set_base_frame("shared")
	var data:Dictionary=JSON.parse_string(FileAccess.get_file_as_string("res://assets/collection/models/G_optical_curator.json"))
	var module:Node3D=load("res://collection/module.gd").new();service.add_child(module)
	module.setup(host,data,load("res://assets/collection/models/G_optical_curator.glb"));service.current=module;service.active_id="G";service._build_controls()
	module.play.input("leaf",1.0,"begin")
	await step(360)
	check("switch_keeps_base_screen_width",absf(host.DesktopScale.base_width_pixels(host)-before)<.1)
	await capture("03_default_G")
	service.toggle_selector();await step(480)
	check("selector_opens_after_return",service.selector_amount>.99)
	var plaques:Array=[]
	for card in service.card_nodes:
		var point:Vector2=host.camera.unproject_position(card.node.global_position)
		plaques.append({"point":str(point),"inside":Rect2(Vector2.ZERO,Vector2(host.canonical_size)).has_point(point)})
	check("selector_plaque_centers_inside_canvas",plaques.all(func(p):return p.inside),plaques)
	await capture("04_selector")
	service.toggle_selector();await step(75);module.activate(3);await step(210)
	var bounds_points:Array[Vector2]=[];service._screen_points(module.asset,bounds_points)
	service._screen_points(host.fixed_base,bounds_points)
	var extents:=Rect2(bounds_points[0],Vector2.ZERO)
	for point in bounds_points:extents=extents.expand(point)
	check("G_service_fits_at_default_size",Rect2(Vector2.ZERO,Vector2(host.canonical_size)).encloses(extents),str(extents))
	await capture("05_service")
	host._set_desktop_zoom(1.10);host.toast.hide();bounds_points.clear();service._screen_points(module.asset,bounds_points)
	service._screen_points(host.fixed_base,bounds_points)
	extents=Rect2(bounds_points[0],Vector2.ZERO)
	for point in bounds_points:extents=extents.expand(point)
	check("G_service_fits_at_max_size",Rect2(Vector2.ZERO,Vector2(host.canonical_size)).encloses(extents),str(extents))
	await capture("06_service_larger")
	var report:={"passed":checks.all(func(c):return c.passed),"checks":checks,"scope":"Actual Metal scene render and synthetic input checks, not native pointer/persistence or all model animation bounds"}
	FileAccess.open(OUT+"scale_qa.json",FileAccess.WRITE).store_string(JSON.stringify(report,"  "));print("DESKTOP_SCALE_QA ",JSON.stringify(report))
	host=null;service=null;module=null;scene.queue_free();await process_frame;await process_frame;quit(0 if report.passed else 1)
