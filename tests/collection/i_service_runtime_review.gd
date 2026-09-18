extends SceneTree
var host:Node3D
var out:="res://../review/I_refinement/service_r4/runtime/"
var component:="res://assets/collection/components/I_service_r4.glb"
var reference_dir:="res://../review/I_refinement/service_r4/"
var service_rig:="res://assets/collection/i_service_rig.json"
var body_rig:="res://assets/collection/i_runtime_rig.json"
func _initialize()->void:run.call_deferred()
func capture(label:String)->void:
    for i in range(4):await RenderingServer.frame_post_draw
    host.render_view.get_texture().get_image().save_png(out+label+".png")
func run()->void:
    for arg in OS.get_cmdline_user_args():
        if arg.begins_with("--component="):component=arg.trim_prefix("--component=")
        if arg.begins_with("--out="):out=arg.trim_prefix("--out=")
        if arg.begins_with("--reference-dir="):reference_dir=arg.trim_prefix("--reference-dir=")
        if arg.begins_with("--service-rig="):service_rig=arg.trim_prefix("--service-rig=")
        if arg.begins_with("--body-rig="):body_rig=arg.trim_prefix("--body-rig=")
    set_meta("collection_no_save",true);set_meta("collection_no_audio",true);set_meta("collection_skip_intro",true)
    DirAccess.make_dir_recursive_absolute(out)
    var scene:Node=load("res://main.tscn").instantiate();root.add_child(scene)
    for i in range(12):await process_frame
    host=scene.get_node("Render/HeliosDesktop");host.set_process(false);host.power=1.;host.power_target=1.;host.muted=true
    var shared:Node3D=host.collection;shared._legacy_set_visible(false);shared._set_base_frame("shared")
    var asset:Node3D=load(component).instantiate();host.add_child(asset)
    var driver:Node=load("res://collection/i_runtime.gd").new();asset.add_child(driver);driver.setup(asset,service_rig,body_rig);driver.enable_visuals()
    var console:Node3D=load("res://collection/i_console.gd").new();shared.add_child(console);console.setup(shared)
    for i in range(8):await physics_frame
    console.seat_captions()
    var take:Dictionary=JSON.parse_string(FileAccess.get_file_as_string(reference_dir+"take.json"))
    var source:Dictionary=JSON.parse_string(FileAccess.get_file_as_string(reference_dir+"source_poses.json"));var pose_samples:Dictionary={};var pose_error:=0.
    for sample in source.snapshots:pose_samples[int(sample.frame)]=sample.poses
    var samples:Array=[];var state_error:=0.;var safety_violations:Array=[]
    for frame in range(1000):
        if frame==8:driver.request_operation();driver.simulation.set_controls(.72,.8)
        if frame==45:driver.control("bellows",1.,"begin")
        if frame==90:driver.control("bellows",0.,"release")
        if frame==95:driver.request_service()
        if frame==355:driver.request_operation()
        if frame==505:driver.control("bellows",1.,"begin")
        if frame==525:driver.request_service()
        if frame==595:driver.request_operation()
        if frame==645:driver.request_service()
        if frame==815:driver.request_stow()
        var events:Array=driver.tick(1./30.);console.update(1./30.,driver.simulation,events)
        var expected:Dictionary=take.samples[frame]
        state_error=maxf(state_error,absf(driver.service.amount-float(expected.service.amount)))
        state_error=maxf(state_error,absf(driver.simulation.pressure-float(expected.state.pressure)))
        if driver.service.amount>.0001 and (driver.opening>.0001 or not driver.simulation.ready_to_close()):safety_violations.append(frame+1)
        if pose_samples.has(frame+1):
            for name in pose_samples[frame+1]:
                var t:Transform3D=asset.global_transform.affine_inverse()*driver.node(name).global_transform
                var actual:Array=[[t.basis.x.x,t.basis.y.x,t.basis.z.x,t.origin.x],[t.basis.x.y,t.basis.y.y,t.basis.z.y,t.origin.y],[t.basis.x.z,t.basis.y.z,t.basis.z.z,t.origin.z],[0.,0.,0.,1.]]
                var expected_pose:Array=pose_samples[frame+1][name]
                for y in range(4):
                    for x in range(4):pose_error=maxf(pose_error,absf(float(actual[y][x])-float(expected_pose[y][x])))
        if frame+1 in [82,151,241,340,400,490,590,625,780,840,970]:
            await capture(str(frame+1))
            samples.append({"frame":frame+1,"service":driver.service.state(),"pressure":driver.simulation.pressure})
    var result:={"passed":state_error<.000001 and safety_violations.is_empty() and driver.service.amount==0.,"state_error":state_error,"safety_violations":safety_violations,"samples":samples,"component_sha256":FileAccess.get_sha256("res://assets/collection/components/I_service_r4.glb"),"scope":"Actual Metal service/pressure reversal state preview. Not collision/legibility acceptance or native input/main App integration."}
    result.source_pose_max_error=pose_error;result.reference_source_sha256=source.source_sha256;result.passed=result.passed and pose_error<.00002
    result.component=component;result.component_sha256=FileAccess.get_sha256(component)
    FileAccess.open(out+"review.json",FileAccess.WRITE).store_string(JSON.stringify(result,"  "));print("I_SERVICE_RUNTIME ",JSON.stringify(result))
    driver=null;console=null;asset=null;shared=null;host=null;scene.queue_free();await process_frame;await process_frame;quit(0 if result.passed else 1)
