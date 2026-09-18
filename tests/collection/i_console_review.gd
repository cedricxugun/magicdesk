extends SceneTree
var host:Node3D
var out:="res://../review/I_refinement/console_r1/runtime/"
var component:="res://assets/collection/components/I_pneumatic_r2.glb"
func _initialize()->void:run.call_deferred()
func capture(label:String)->void:
    for i in range(4):await RenderingServer.frame_post_draw
    host.render_view.get_texture().get_image().save_png(out+label+".png")
func run()->void:
    for arg in OS.get_cmdline_user_args():
        if arg.begins_with("--component="):component=arg.trim_prefix("--component=")
        if arg.begins_with("--out="):out=arg.trim_prefix("--out=")
    set_meta("collection_no_save",true);set_meta("collection_no_audio",true);set_meta("collection_skip_intro",true)
    DirAccess.make_dir_recursive_absolute(out)
    var scene:Node=load("res://main.tscn").instantiate();root.add_child(scene)
    for i in range(12):await process_frame
    host=scene.get_node("Render/HeliosDesktop");host.set_process(false);host.power=1.;host.power_target=1.;host.muted=true
    var service:Node3D=host.collection;service._legacy_set_visible(false);service._set_base_frame("shared")
    host.env.ambient_light_energy=.35;var energies:Array=[24.,25.,4.];var count:=0
    for child in host.get_children():
        if child is AreaLight3D:child.light_energy=energies[count];child.light_size=.35;count+=1
    var asset:Node3D=load(component).instantiate();host.add_child(asset)
    var driver:Node=load("res://collection/i_runtime.gd").new();asset.add_child(driver);driver.setup(asset);driver.enable_visuals()
    var console:Node3D=load("res://collection/i_console.gd").new();service.add_child(console);console.setup(service)
    for i in range(8):await physics_frame
    console.seat_captions()
    var sim:RefCounted=driver.simulation;var samples:Array=[]
    for frame in range(240):
        if frame==8:sim.set_controls(.72,.8);sim.start()
        if frame==45:sim.set_pressed(true)
        if frame==90:sim.set_pressed(false)
        if frame==150:sim.set_pressed(true)
        if frame==180:sim.set_pressed(false)
        if frame==185:sim.quiet()
        var events:Array=driver.tick(1./30.);console.update(1./30.,sim,events)
        if frame+1 in [39,82,99,121,226]:
            await capture(str(frame+1)+"_whole")
            var home:Transform3D=host.camera.global_transform;var fov:float=host.camera.fov
            host.camera.global_position=Vector3(0.,1.55,3.8);host.camera.look_at(Vector3(0,.35,0));host.camera.fov=35.
            await capture(str(frame+1)+"_console")
            host.camera.global_transform=home;host.camera.fov=fov
            samples.append({"frame":frame+1,"pressure":sim.pressure,"outgoing":console.outgoing,"return":console.returning})
    var result:={"passed":console.caption_projection.applied,"caption_projection":console.caption_projection,"samples":samples,"source_sha256":JSON.parse_string(FileAccess.get_file_as_string("res://assets/collection/i_console_rig.json")).source_sha256,"component_sha256":FileAccess.get_sha256("res://assets/collection/components/I_controls_r1.glb"),"scope":"Opt-in I console on actual shared cassette, driven by pressure events. Actual Metal captures; not native pointer input/main app integration or full mounting/cowl clearance."}
    result.body_component=component;result.body_sha256=FileAccess.get_sha256(component)
    FileAccess.open(out+"review.json",FileAccess.WRITE).store_string(JSON.stringify(result,"  "));print("I_CONSOLE_RUNTIME ",JSON.stringify(result))
    driver=null;sim=null;console=null;asset=null;service=null;host=null;scene.queue_free();await process_frame;await process_frame;quit(0 if result.passed else 1)
