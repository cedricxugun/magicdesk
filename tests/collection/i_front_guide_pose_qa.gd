extends SceneTree
func _initialize()->void:run.call_deferred()
func errors(node:Node3D,p:Dictionary)->Dictionary:
    var q:Array=p.q;var s:Array=p.s;var t:Array=p.p
    var basis:=Basis(Quaternion(q[0],q[1],q[2],q[3])).scaled(Vector3(s[0],s[1],s[2]))
    var actual:Transform3D=node.global_transform
    return {"position":actual.origin.distance_to(Vector3(t[0],t[1],t[2])),"basis":maxf(actual.basis.x.distance_to(basis.x),maxf(actual.basis.y.distance_to(basis.y),actual.basis.z.distance_to(basis.z)))}
func run()->void:
    var directory:="res://../review/I_refinement/part_a_mouth/shutter_r2/front_guides/"
    for argument in OS.get_cmdline_user_args():
        if argument.begins_with("--report="):directory=argument.trim_prefix("--report=").get_base_dir()+"/"
    var spec:Dictionary=JSON.parse_string(FileAccess.get_file_as_string(directory+"build.json"))
    var golden:Dictionary=JSON.parse_string(FileAccess.get_file_as_string(directory+"source_poses.json"))
    assert(golden.source_sha256==spec.source_sha256)
    var path:String="res://"+str(spec.component).trim_prefix("app/")
    assert(FileAccess.get_sha256(path)==golden.component_sha256)
    var asset:Node3D=load(path).instantiate();root.add_child(asset)
    var driver=load("res://collection/i_tongue_set_driver.gd").new();driver.bind(asset,spec)
    var rows:Array=[];var passed:=true
    # Reverse and cancellation revisit the same source states in a different order.
    for opening in [0.,.5,1.,.5,0.,24./156.,108./156.,60./156.,24./156.]:
        driver.set_opening(opening)
        for reference in golden.poses:
            if absf(float(reference.opening)-opening)>.000001:continue
            var g:=errors(asset.find_child(reference.guide,true,false),reference.guide_pose)
            var s:=errors(asset.find_child(reference.shaft,true,false),reference.shaft_pose)
            var ok:bool=g.position<.00001 and g.basis<.0001 and s.position<.00001 and s.basis<.0001
            passed=passed and ok;rows.append({"opening":opening,"index":reference.index,"guide_errors":g,"shaft_errors":s,"passed":ok})
    assert(rows.size()==27)
    FileAccess.open(directory+"runtime_pose_qa.json",FileAccess.WRITE).store_string(JSON.stringify({"source_sha256":spec.source_sha256,"component_sha256":spec.component_sha256,"passed":passed,"samples":rows,"scope":"Actual imported transforms compared to evaluated Blender golden poses, including repeated/reversed/cancelled progress. This headless check does not verify native gestures or visible quality."},"  "))
    print("I_FRONT_GUIDE_POSE_QA ",passed);asset.queue_free();await process_frame;quit(0 if passed else 1)
