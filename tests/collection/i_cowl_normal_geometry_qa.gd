extends SceneTree
func _initialize()->void:run.call_deferred()
func triangle_key(points:PackedVector3Array,i:int)->String:
    var vertices:Array=[]
    for j in range(3):vertices.append(PackedVector3Array([points[i+j]]).to_byte_array().hex_encode())
    var choices:Array=[vertices[0]+vertices[1]+vertices[2],vertices[1]+vertices[2]+vertices[0],vertices[2]+vertices[0]+vertices[1]]
    choices.sort();return choices[0]
func same_oriented_triangles(a:PackedVector3Array,b:PackedVector3Array)->bool:
    if a.size()!=b.size():return false
    if a.to_byte_array()==b.to_byte_array():return true
    var counts:Dictionary={}
    for i in range(0,a.size(),3):
        var key:=triangle_key(a,i);counts[key]=int(counts.get(key,0))+1
    for i in range(0,b.size(),3):
        var key:=triangle_key(b,i);counts[key]=int(counts.get(key,0))-1
    return counts.values().all(func(count):return count==0)
func run()->void:
    var folder:="res://../review/I_refinement/nautilus_r1/cowl_weighted_r50/"
    for argument in OS.get_cmdline_user_args():
        if argument.begins_with("--report="):folder=argument.trim_prefix("--report=").get_base_dir()+"/"
    var spec:Dictionary=JSON.parse_string(FileAccess.get_file_as_string(folder+"build.json"));var old:Dictionary=JSON.parse_string(FileAccess.get_file_as_string("res://../review/I_refinement/nautilus_r1/scan_caps_runtime_r43/readable/build.json"))
    assert(spec.parent_source_sha256==old.source_sha256)
    var path:String="res://"+str(spec.component).trim_prefix("app/");assert(FileAccess.get_sha256(path)==spec.component_sha256)
    var asset:Node3D=load(path).instantiate();var previous:Node3D=load("res://"+str(old.component).trim_prefix("app/")).instantiate();root.add_child(asset);root.add_child(previous)
    var names:Array=[]
    for row in spec.cowl_normal_finish:names.append(str(row.mesh))
    var count:=0;var triangles:=0;var changed:Array=[]
    for mesh in asset.find_children("*","MeshInstance3D",true,false):
        var reference:=previous.find_child(str(mesh.name),true,false)as MeshInstance3D;assert(reference!=null)
        var a:PackedVector3Array=mesh.mesh.get_faces();var b:PackedVector3Array=reference.mesh.get_faces();assert(same_oriented_triangles(a,b),"Imported triangle geometry changed: "+str(mesh.name));triangles+=a.size()/3;count+=1
        var av:Array=[mesh.global_basis.x,mesh.global_basis.y,mesh.global_basis.z,mesh.global_position];var bv:Array=[reference.global_basis.x,reference.global_basis.y,reference.global_basis.z,reference.global_position]
        for axis in range(4):
            for component in range(3):assert(float(av[axis][component])==float(bv[axis][component]))
        var differs:=false
        assert(mesh.mesh.get_surface_count()==reference.mesh.get_surface_count())
        for surface in range(mesh.mesh.get_surface_count()):
            var aa:Array=mesh.mesh.surface_get_arrays(surface);var bb:Array=reference.mesh.surface_get_arrays(surface)
            differs=differs or aa[Mesh.ARRAY_NORMAL].to_byte_array()!=bb[Mesh.ARRAY_NORMAL].to_byte_array()
        if differs:assert(str(mesh.name)in names);changed.append(str(mesh.name))
    assert(count==previous.find_children("*","MeshInstance3D",true,false).size() and changed.size()==4)
    FileAccess.open(folder+"runtime_geometry_qa.json",FileAccess.WRITE).store_string(JSON.stringify({"passed":true,"source_sha256":spec.source_sha256,"component_sha256":spec.component_sha256,"mesh_count":count,"triangle_count":triangles,"changed_normal_meshes":changed,"scope":"Every imported oriented triangle coordinate multiset equal to R40 at exact float32 precision, preserving multiplicity and winding; triangle ordering may change. Every world transform scalar equal; imported normal changes restricted to four declared cowls. Separate chamber QA checks morph buffers. No art/native acceptance."},"  "))
    asset.queue_free();previous.queue_free();await process_frame;print("I_COWL_NORMAL_GEOMETRY_QA true meshes=",count);quit()
