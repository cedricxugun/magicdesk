extends SceneTree
func _initialize()->void:run.call_deferred()
func run()->void:
    var out:="res://../review/I_refinement/part_b_shell/linkage_b3/"
    for argument in OS.get_cmdline_user_args():
        if argument.begins_with("--report="):out=argument.trim_prefix("--report=").get_base_dir()+"/"
    var spec:Dictionary=JSON.parse_string(FileAccess.get_file_as_string(out+"build.json"))
    var path:String="res://"+str(spec.component).trim_prefix("app/")
    assert(FileAccess.get_sha256(path)==spec.component_sha256)
    var asset:Node3D=load(path).instantiate();root.add_child(asset)
    var driver=load("res://collection/i_shell_linkage_b3_driver.gd").new();driver.bind(asset,spec)
    var convert:=Transform3D(Basis(Vector3(1,0,0),Vector3(0,0,-1),Vector3(0,1,0)),Vector3.ZERO)
    var max_pose_error:=0.;var max_endpoint_error:=0.;var comparisons:=0
    for record in spec.pose_records:
        driver.set_opening(float(record.release))
        for name in record.panel_world_matrices:
            var node:Node3D=asset.find_child(name,true,false);var m:Array=record.panel_world_matrices[name]
            var expected:=Transform3D(Basis(Vector3(m[0][0],m[1][0],m[2][0]),Vector3(m[0][1],m[1][1],m[2][1]),Vector3(m[0][2],m[1][2],m[2][2])),Vector3(m[0][3],m[1][3],m[2][3]))
            expected=convert*expected*convert.inverse()
            for point in [Vector3.ZERO,Vector3.RIGHT,Vector3.UP,Vector3.FORWARD]:
                max_pose_error=maxf(max_pose_error,(node.global_transform*point-expected*point).length());comparisons+=1
        for row in spec.rig:
            var panel:Node3D=asset.find_child(row.panel_pivot,true,false)
            for i in range(2):
                var arm:Node3D=asset.find_child(row.link_pivots[i],true,false)
                var first:Vector3=driver.vector(row.a if i==0 else row.d)
                var last:Vector3=driver.vector(row.b0 if i==0 else row.c0)
                var endpoint:Vector3=arm.global_transform*Vector3((last-first).length(),0,0)
                var offset:Vector3=driver.vector(row.axis)*float(row.get("ab_axis_offset",0.)) if i==0 else Vector3.ZERO
                var mount:Vector3=panel.global_transform*(convert*(last+offset))
                max_endpoint_error=maxf(max_endpoint_error,endpoint.distance_to(mount))
    # Exercise the same pose after several reversals, without relying on animation history.
    for amount in [.73,.15,.88,.0,.5,1.,.34,0.]:driver.set_opening(amount)
    var rest_error:=0.
    for row in spec.rig:
        var pivot:Node3D=asset.find_child(row.panel_pivot,true,false)
        rest_error=maxf(rest_error,maxf(pivot.transform.origin.length(),pivot.transform.basis.get_rotation_quaternion().angle_to(Quaternion.IDENTITY)))
    var passed:bool=max_pose_error<.00001 and max_endpoint_error<.00001 and rest_error<.00001
    FileAccess.open(out+"runtime_pose_check.json",FileAccess.WRITE).store_string(JSON.stringify({"source_sha256":spec.source_sha256,"component_sha256":spec.component_sha256,"passed":passed,"point_comparisons":comparisons,"max_pose_error":max_pose_error,"max_endpoint_error":max_endpoint_error,"return_to_rest_error":rest_error,"scope":"Godot imported hierarchy vs baked Blender panel poses, link endpoint closure, and deterministic reversals. No finite collision, visual/native input, music or AAA acceptance."},"  "))
    print("B3_RUNTIME_POSES ",passed," pose=",max_pose_error," closure=",max_endpoint_error);asset.queue_free();await process_frame;quit(0 if passed else 1)
