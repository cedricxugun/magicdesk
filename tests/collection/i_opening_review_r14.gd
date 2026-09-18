extends SceneTree
var host:Node3D
var out:="res://../review/I_refinement/opening_r14/runtime/"
func _initialize()->void:run.call_deferred()
func capture(name:String)->void:
    for i in range(4):await RenderingServer.frame_post_draw
    host.render_view.get_texture().get_image().save_png(out+name+".png")
func run()->void:
    set_meta("collection_no_save",true);set_meta("collection_no_audio",true);set_meta("collection_skip_intro",true);DirAccess.make_dir_recursive_absolute(out)
    var scene:Node=load("res://main.tscn").instantiate();root.add_child(scene)
    for i in range(12):await process_frame
    host=scene.get_node("Render/HeliosDesktop");host.set_process(false);host.power=1.;host.power_target=1.;host.muted=true
    var shared:Node3D=host.collection;shared._legacy_set_visible(false);shared._set_base_frame("shared")
    host.env.ambient_light_energy=.30;var energies:Array=[20.,21.,4.];var n:=0
    for child in host.get_children():
        if child is AreaLight3D:child.light_energy=energies[n];child.light_size=.50;n+=1
    var path:="res://assets/collection/components/I_opening_r14.glb";var asset:Node3D=load(path).instantiate();host.add_child(asset)
    var driver:RefCounted=load("res://collection/i_opening_layout_r14.gd").new();driver.setup(asset)
    var source:Dictionary=JSON.parse_string(FileAccess.get_file_as_string("res://../review/I_refinement/opening_r14/source_poses.json"));var error:=0.;var samples:Array=[]
    var camera_home:Transform3D=host.camera.global_transform;var fov:float=host.camera.fov
    for frame in range(1,362):
        driver.apply_time((frame-1)/30.)
        if source.has(str(frame)):
            for name in source[str(frame)]:
                var node:Node3D=asset.find_child(name,true,false);var row:Dictionary=source[str(frame)][name]
                var p:=Vector3(row.p[0],row.p[1],row.p[2]);var q:=Quaternion(row.q[0],row.q[1],row.q[2],row.q[3]);var scale:=Vector3(row.s[0],row.s[1],row.s[2]);var expected:=Transform3D(Basis(q).scaled(scale),p)
                error=maxf(error,node.global_position.distance_to(expected.origin))
                for column in range(3):error=maxf(error,node.global_basis[column].distance_to(expected.basis[column]))
            samples.append({"frame":frame,"max_pose_error":error})
        if frame in [1,31,61,91,121,181,241,301,361]:await capture(str(frame))
    driver.apply_time(4.0)
    host.camera.position=Vector3(.55,3.10,6.0);host.camera.look_at(Vector3(0,2.1,0));host.camera.fov=38.;await capture("open_hero")
    host.camera.position=Vector3(-.7,3.0,-5.5);host.camera.look_at(Vector3(0,2.1,0));await capture("open_rear")
    var result:={"source_pose_match":error<.00002,"max_pose_error":error,"samples":samples,"component_sha256":FileAccess.get_sha256(path),"scope":"Actual Metal 12-second kinematic layout forward/reverse with sampled source transforms. Bearing/core envelopes are provisional. No collision, art, native controls or music acceptance."}
    FileAccess.open(out+"review.json",FileAccess.WRITE).store_string(JSON.stringify(result,"  "));print("I_OPENING_REVIEW ",JSON.stringify(result));host=null;scene.queue_free();await process_frame;quit(0 if error<.00002 else 1)
