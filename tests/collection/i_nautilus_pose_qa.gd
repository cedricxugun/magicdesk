extends SceneTree
func _initialize()->void:run.call_deferred()
func run()->void:
    var folder:="res://../review/I_refinement/nautilus_r1/hinge_r1/"
    for arg in OS.get_cmdline_user_args():
        if arg.begins_with("--report="):folder=arg.trim_prefix("--report=").get_base_dir()+"/"
    var spec:Dictionary=JSON.parse_string(FileAccess.get_file_as_string(folder+"build.json"))
    var reference:Dictionary=JSON.parse_string(FileAccess.get_file_as_string(folder+"pose_reference.json"))
    assert(reference.source_sha256==spec.source_sha256 and reference.component_sha256==spec.component_sha256)
    var path:String="res://"+str(spec.component).trim_prefix("app/");assert(FileAccess.get_sha256(path)==spec.component_sha256)
    var asset:Node3D=load(path).instantiate();root.add_child(asset)
    var driver=load("res://collection/i_nautilus_form_driver.gd").new();driver.bind(asset,spec)
    var maximum:=0.;var checks:=0
    for sample in reference.samples:
        driver.set_opening(sample.opening);await process_frame
        for name in sample.points:
            var node:=asset.find_child(str(name),true,false) as Node3D;assert(node!=null,"Missing imported mechanism node: "+name)
            for i in range(reference.local_points.size()):
                var p:Array=reference.local_points[i];var e:Array=sample.points[name][i]
                var actual:Vector3=node.global_transform*Vector3(p[0],p[1],p[2]);var error:=actual.distance_to(Vector3(e[0],e[1],e[2]))
                maximum=maxf(maximum,error);checks+=1
                assert(error<.00001,"Imported motion differs from evaluated source: "+name+" error="+str(error))
    FileAccess.open(folder+"runtime_pose_check.json",FileAccess.WRITE).store_string(JSON.stringify({"passed":true,"source_sha256":spec.source_sha256,"component_sha256":spec.component_sha256,"landmarks":checks,"maximum_error":maximum,"scope":"Actual imported GLB node-transform landmarks across closed/lifted/rotated and reversed input poses. No native input, continuous collision, vertex/material or art acceptance."},"  "))
    driver=null;asset.queue_free();await process_frame;print("NAUTILUS_POSE_QA true ",checks," error=",maximum);quit()
