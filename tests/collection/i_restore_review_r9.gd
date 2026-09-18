extends SceneTree
var host:Node3D
var out:="res://../review/I_refinement/restore_r9/runtime/"
func _initialize()->void:run.call_deferred()
func capture(label:String)->void:
    for i in range(4):await RenderingServer.frame_post_draw
    host.render_view.get_texture().get_image().save_png(out+label+".png")
func run()->void:
    set_meta("collection_no_save",true);set_meta("collection_no_audio",true);set_meta("collection_skip_intro",true)
    DirAccess.make_dir_recursive_absolute(out)
    var scene:Node=load("res://main.tscn").instantiate();root.add_child(scene)
    for i in range(12):await process_frame
    host=scene.get_node("Render/HeliosDesktop");host.set_process(false);host.power=1.;host.power_target=1.;host.muted=true
    var shared:Node3D=host.collection;shared._legacy_set_visible(false);shared._set_base_frame("shared")
    host.env.ambient_light_energy=.35;var energies:Array=[24.,25.,4.];var n:=0
    for child in host.get_children():
        if child is AreaLight3D:child.light_energy=energies[n];child.light_size=.35;n+=1
    var asset:Node3D=load("res://assets/collection/components/I_restore_r9.glb").instantiate();host.add_child(asset)
    var driver:RefCounted=load("res://collection/i_restore_motion.gd").new();driver.setup(asset)
    var source:Dictionary=JSON.parse_string(FileAccess.get_file_as_string("res://../review/I_refinement/restore_r9/source_poses.json"))
    var pose_error:=0.;var samples:Array=[]
    for frame in range(1,302):
        driver.apply_reference_time((frame-1)/30.)
        if source.has(str(frame)):
            for name in source[str(frame)]:
                var node:Node3D=asset.find_child(name,true,false);var target:Dictionary=source[str(frame)][name]
                var expected:=Transform3D(Basis(Quaternion(target.q[0],target.q[1],target.q[2],target.q[3])).scaled(Vector3(target.s[0],target.s[1],target.s[2])),Vector3(target.p[0],target.p[1],target.p[2]))
                pose_error=maxf(pose_error,node.global_position.distance_to(expected.origin))
            samples.append({"frame":frame,"max_position_error":pose_error})
        if frame in [1,35,55,76,120,210,301]:await capture(str(frame))
    driver.apply(1.,1.)
    var mouth:Node3D=asset.find_child("IH1_Mouth",true,false)
    host.camera.global_position=mouth.global_position+Vector3(2.0,.55,2.8);host.camera.look_at(mouth.global_position+Vector3(0,.12,0));host.camera.fov=40.
    await capture("active_core_close")
    var result:={"passed":pose_error<.00002,"source_shell_position_max_error":pose_error,"samples":samples,"component_sha256":FileAccess.get_sha256("res://assets/collection/components/I_restore_r9.glb"),"scope":"Actual Metal normal-operation restoration preview and sampled source shell positions; no all-part clearance, audio, native input or art acceptance."}
    FileAccess.open(out+"review.json",FileAccess.WRITE).store_string(JSON.stringify(result,"  "));print("I_RESTORE_REVIEW ",JSON.stringify(result));host=null;scene.queue_free();await process_frame;quit(0 if result.passed else 1)
