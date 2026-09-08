extends SceneTree

var host:Node3D
var frames:Array=[]
var output:="H:/model/output/helios_incubator/review/integrated_release"
var recording:=false
var ended:=false

func _initialize()->void:
	for a in OS.get_cmdline_user_args():
		if a=="--record-frames":recording=true
	root.position=Vector2i(-32000,-32000);root.size=Vector2i(32,32)
	call_deferred("run")

func run()->void:
	var scene:Node=load("res://main.tscn").instantiate()
	root.add_child(scene)
	host=scene.get_node("Render/HeliosDesktop")
	await physics_frame
	await process_frame
	host.set_process(false)
	host.rotation_enabled=false;host.angle=0.0;host.power=1.0;host.power_target=1.0
	host.toast_timer=0.0;host.muted=true
	DirAccess.make_dir_recursive_absolute(output)
	if recording:DirAccess.make_dir_recursive_absolute(output.path_join("frames"))
	for i in range(120):host._process(1.0/30.0)
	for i in range(5):await process_frame
	await capture("00_ceramic_closed")
	if recording:
		for i in range(30):
			host._process(1.0/30.0);await process_frame;await RenderingServer.frame_post_draw
			host.render_view.get_texture().get_image().save_png(output.path_join("frames/%04d.png"%i))
	host.activate(1)
	for i in range(1,181):
		var start:=Time.get_ticks_usec()
		host._process(1.0/30.0)
		await process_frame
		await RenderingServer.frame_post_draw
		frames.append({"frame":i,"open":host.openness,"pressure_volumes":host.effects.pressure.active_volume_count,"frame_ms":(Time.get_ticks_usec()-start)/1000.0})
		if i in [9,15,21,33,45,66,90,120,180]:await capture("activation_%03d"%i)
		if recording:host.render_view.get_texture().get_image().save_png(output.path_join("frames/%04d.png"%(i+29)))
	host.activate(2)
	for i in range(120):
		host._process(1.0/30.0);await process_frame
		if i==45:await capture("overload")
	host.activate(3)
	for i in range(85):host._process(1.0/30.0);await process_frame
	await capture("exploded")
	host.activate(4)
	for i in range(90):host._process(1.0/30.0);await process_frame
	await capture("assembled")
	FileAccess.open(output.path_join("timing.json"),FileAccess.WRITE).store_string(JSON.stringify(frames,"  "))
	print("INTEGRATED_RELEASE_COMPLETE ",output)
	quit()

func capture(name_string:String)->void:
	await process_frame
	await RenderingServer.frame_post_draw
	host.render_view.get_texture().get_image().save_png(output.path_join(name_string+".png"))
