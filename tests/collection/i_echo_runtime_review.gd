extends SceneTree
var host:Node3D
var out:="res://../review/I_refinement/r2/runtime_echo/"
func _initialize()->void:run.call_deferred()
func capture(label:String)->void:
	for i in range(4):await RenderingServer.frame_post_draw
	host.render_view.get_texture().get_image().save_png(out+label+".png")
func run()->void:
	set_meta("collection_no_save",true);set_meta("collection_no_audio",true);set_meta("collection_skip_intro",true)
	DirAccess.make_dir_recursive_absolute(out)
	var scene:Node=load("res://main.tscn").instantiate();root.add_child(scene)
	for i in range(12):await process_frame
	host=scene.get_node("Render/HeliosDesktop");host.set_process(false);host.muted=true;host.power=1.;host.power_target=1.
	host.collection._legacy_set_visible(false);host.collection._set_base_frame("shared")
	host.env.ambient_light_energy=.35;var energies:Array=[24.,25.,4.];var count:=0
	for child in host.get_children():
		if child is AreaLight3D:child.light_energy=energies[count];child.light_size=.35;count+=1
	var asset:Node3D=load("res://assets/collection/components/I_pneumatic_r2.glb").instantiate();host.add_child(asset)
	var driver:Node=load("res://collection/i_runtime.gd").new();asset.add_child(driver);driver.setup(asset);driver.enable_visuals()
	var sim:RefCounted=driver.simulation
	var take:Dictionary=JSON.parse_string(FileAccess.get_file_as_string("res://../review/I_refinement/r2/pneumatic_take.json"))
	var samples:Array=[];var maximum_error:=0.;var events_seen:Array=[];var quiet_clear:=false
	for frame in range(361):
		if frame==8:sim.set_controls(.72,.8);sim.start()
		if frame==45:sim.set_pressed(true)
		if frame==90:sim.set_pressed(false)
		if frame==150:sim.set_pressed(true)
		if frame==180:sim.set_pressed(false)
		if frame==185:sim.quiet()
		if frame==240:sim.set_controls(.2,0.);sim.start()
		if frame==255:sim.set_pressed(true)
		if frame==285:sim.set_pressed(false)
		if frame==306:sim.quiet()
		var events:Array=driver.tick(1./30.);events_seen.append_array(events)
		var expected:Dictionary=take.samples[frame].state;var actual:Dictionary=sim.state()
		for key in ["pressure","compression","iris","gain","diaphragm"]:maximum_error=maxf(maximum_error,absf(float(expected[key])-float(actual[key])))
		if frame+1 in [82,99,104,121,190,226,361]:
			var label:String=str(frame+1);await capture(label+"_fx")
			var visible_nodes:Array=[]
			for item in driver.visuals.waves+driver.visuals.receivers+driver.visuals.traces.values():
				if item.node.visible:visible_nodes.append(item.node);item.node.hide()
			var warm:float=driver.visuals.warm.light_energy;var cool:float=driver.visuals.cool.light_energy
			driver.visuals.warm.light_energy=0.;driver.visuals.cool.light_energy=0.;await capture(label+"_without_fx")
			for node in visible_nodes:node.show()
			driver.visuals.warm.light_energy=warm;driver.visuals.cool.light_energy=cool
			samples.append({"frame":frame+1,"state":actual,"optics":driver.visuals.amplitudes.duplicate(true)})
		if frame==225:quiet_clear=int(driver.visuals.amplitudes.live_carriers)==0 and sim.ready_to_close()
	var result:={"passed":maximum_error<.000001 and events_seen.size()==3 and quiet_clear,"max_state_error":maximum_error,"quiet_clear":quiet_clear,"events":events_seen,"samples":samples,"component_sha256":FileAccess.get_sha256("res://assets/collection/components/I_pneumatic_r2.glb"),"atlas_sha256":FileAccess.get_sha256("res://assets/collection/art/I/acoustic_atlas_r1.png"),"scope":"Actual Metal preview of pressure-driven authored atlas effects and local lights. Paired captures disable artwork/lights only. Not native controls, final lighting or App integration."}
	FileAccess.open(out+"review.json",FileAccess.WRITE).store_string(JSON.stringify(result,"  "));print("I_ECHO_RUNTIME_REVIEW ",JSON.stringify(result))
	driver=null;asset=null;sim=null;host=null;scene.queue_free();await process_frame;await process_frame;quit(0 if result.passed else 1)
