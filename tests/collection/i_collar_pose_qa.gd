extends SceneTree
func _initialize()->void:run.call_deferred()
func run()->void:
    var folder:="res://../review/I_refinement/part_a_mouth/shutter_r2/collar_clamps/"
    var spec:Dictionary=JSON.parse_string(FileAccess.get_file_as_string(folder+"build.json"))
    var golden:Dictionary=JSON.parse_string(FileAccess.get_file_as_string(folder+"source_poses.json"))
    assert(spec.source_sha256==golden.source_sha256 and spec.component_sha256==golden.component_sha256)
    var path:String="res://"+str(spec.component).trim_prefix("app/");assert(FileAccess.get_sha256(path)==spec.component_sha256)
    var asset:Node3D=load(path).instantiate();root.add_child(asset)
    var homes:Dictionary={}
    for row in spec.collar_clamps:homes[row.pivot]=asset.find_child(row.pivot,true,false).basis
    var maximum_position:=0.;var maximum_basis:=0.;var count:=0
    for amount in [0.,.5,1.,.75,.25,0.]:
        for row in spec.collar_clamps:
            var pivot:Node3D=asset.find_child(row.pivot,true,false)
            pivot.basis=homes[row.pivot]*Basis(Vector3.FORWARD,deg_to_rad(float(row.service_release_degrees))*amount)
        for sample in golden.samples:
            if absf(float(sample.release)-amount)>.00001:continue
            for name in sample.nodes:
                var actual:Transform3D=asset.find_child(name,true,false).global_transform
                var reference:Dictionary=sample.nodes[name];var q:Array=reference.q;var s:Array=reference.s;var p:Array=reference.p
                var basis:=Basis(Quaternion(q[0],q[1],q[2],q[3])).scaled(Vector3(s[0],s[1],s[2]))
                maximum_position=maxf(maximum_position,actual.origin.distance_to(Vector3(p[0],p[1],p[2])))
                maximum_basis=maxf(maximum_basis,maxf(actual.basis.x.distance_to(basis.x),maxf(actual.basis.y.distance_to(basis.y),actual.basis.z.distance_to(basis.z))))
                count+=1
    assert(count==180 and maximum_position<.00001 and maximum_basis<.00001)
    FileAccess.open(folder+"runtime_pose_qa.json",FileAccess.WRITE).store_string(JSON.stringify({"passed":true,"source_sha256":spec.source_sha256,"component_sha256":spec.component_sha256,"node_pose_comparisons":count,"maximum_position_error":maximum_position,"maximum_basis_error":maximum_basis,"scope":"Actual imported GLB nodes versus refreshed Blender world transforms, including reverse/cancelled progress and fixed stud/pin. Not native interaction or full service/disassembly acceptance."},"  "))
    print("I_COLLAR_POSE_QA true");asset.queue_free();await process_frame;quit()
