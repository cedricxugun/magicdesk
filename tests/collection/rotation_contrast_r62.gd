extends SceneTree
class Host extends Node3D:
	var camera:Camera3D
	var rotation_enabled:=false
	var shutdown_time:=-1.
	var closing_time:=-1.
	func sound(_name:String,_pitch:float)->void:pass
class Service extends Node3D:
	var host:Node3D
	var state:="idle"
	var selector_amount:=0.
	var selector_target:=0.
	var selector_wait:=false
	func pointer_position()->Vector2:return Vector2(-10000,-10000)
	func toggle_display_rotation()->void:host.rotation_enabled=not host.rotation_enabled
var out:="res://../review/shared_rotation/contrast_r3/render/"
var view:SubViewport
var host:Node3D
var service:Node3D
var control:Node3D
var bg:ColorRect
var records:Array=[]
func _initialize()->void:run.call_deferred()
func _process(delta:float)->bool:RenderingServer.force_draw(false,delta);return false
func step(seconds:float)->void:
	for i in range(ceili(seconds*60.)):
		control.tick(1./60.);await process_frame
func capture(label:String)->void:
	for pair in [["white",Color.WHITE],["dark",Color(.025,.028,.032)],["gray",Color(.46,.49,.51)]]:
		bg.color=pair[1]
		for f in range(3):await RenderingServer.frame_post_draw
		root.get_texture().get_image().save_png(out+label+"_"+pair[0]+".png")
	records.append({"label":label,"state":control.state(),"icon_size":.28,"fixture":"Real shared base and actual control class; lightweight host for visual comparison only."})
func press(value:bool,point:Vector2)->bool:
	var event:=InputEventMouseButton.new();event.button_index=MOUSE_BUTTON_LEFT;event.pressed=value;event.position=point
	return control.consume(event)
func run()->void:
	RenderingServer.set_render_loop_enabled(false);DirAccess.make_dir_recursive_absolute(out)
	root.size=Vector2i(1600,1100);root.transparent_bg=false
	bg=ColorRect.new();root.add_child(bg);bg.size=Vector2(root.size);bg.color=Color.WHITE
	view=SubViewport.new();root.add_child(view);view.size=root.size;view.own_world_3d=true;view.transparent_bg=true;view.msaa_3d=Viewport.MSAA_2X;view.render_target_update_mode=SubViewport.UPDATE_ALWAYS
	var present:=TextureRect.new();root.add_child(present);present.texture=view.get_texture();present.size=Vector2(root.size)
	host=Host.new();view.add_child(host)
	host.camera=Camera3D.new();host.add_child(host.camera);host.camera.fov=34.;host.camera.position=Vector3(.65,3.95,7.65);host.camera.look_at(Vector3(0,1.92,0));host.camera.current=true
	var env:=Environment.new();env.background_mode=Environment.BG_CLEAR_COLOR;env.ambient_light_source=Environment.AMBIENT_SOURCE_COLOR;env.ambient_light_color=Color.WHITE;env.ambient_light_energy=.8
	var environment:=WorldEnvironment.new();host.add_child(environment);environment.environment=env
	var light:=DirectionalLight3D.new();host.add_child(light);light.rotation_degrees=Vector3(-45,-25,0);light.light_energy=1.2
	var donor:Node3D=load("res://assets/helios_model.glb").instantiate();host.add_child(donor);var base:Node3D=donor.find_child("BASE_FIXED",true,false);base.reparent(host,true);donor.queue_free()
	service=Service.new();host.add_child(service);service.host=host
	for variant in ["before","after"]:
		control=load("res://../review/shared_rotation/contrast_r3/before/rotation_hologram.gd" if variant=="before" else "res://collection/rotation_hologram.gd").new();service.add_child(control);control.setup(service)
		host.rotation_enabled=false;control.review_pointer=Vector2(-10000,-10000);await step(3.);await capture(variant+"_idle_rotate")
		host.rotation_enabled=true;await step(.2);await capture(variant+"_idle_pause")
		control.review_pointer=control.screen_center();await step(.6);await capture(variant+"_hover")
		if variant=="after":
			var center:Vector2=control.screen_center();var initial:bool=host.rotation_enabled
			assert(press(true,center));await step(.05);await capture("after_pressed")
			assert(press(false,center) and host.rotation_enabled!=initial);await step(.05);await capture("after_release")
			var toggled:bool=host.rotation_enabled;assert(not press(false,center));assert(host.rotation_enabled==toggled)
			press(true,center);press(false,center+Vector2(200,0));assert(host.rotation_enabled==toggled)
			press(true,center);root.focus_exited.emit();assert(not control.held);press(false,center);assert(host.rotation_enabled==toggled)
			press(true,center);service.state="loading";await step(.5);assert(not control.held);press(false,center);assert(host.rotation_enabled==toggled)
			await capture("after_unavailable");service.state="idle"
			service.selector_target=1.;assert(not control.available());service.selector_target=0.
			service.selector_wait=true;assert(not control.available());service.selector_wait=false
		control.queue_free();await process_frame;await process_frame
	FileAccess.open(out+"receipt.json",FileAccess.WRITE).store_string(JSON.stringify({"records":records,"input_checks_passed":true,"scope":"Actual control and physical base in lightweight visual fixture. Click/release/drag-out/focus cancel/unavailable logic only; no main G/I independence or native mouse claim."},"  "));quit()
