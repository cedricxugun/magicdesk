extends RefCounted
## Review-only prepared service pose; ordinary source geometry stays unchanged.
var originals:Array=[]
func converted(a:Array)->Vector3:return Vector3(a[0],a[2],-a[1])
func apply(body:Node3D,mouth:Node3D,spec:Dictionary,manifest:Dictionary)->void:
	assert(originals.is_empty() and spec.source_sha256==manifest.body_source_sha256)
	var support:Dictionary=JSON.parse_string(FileAccess.get_file_as_string("res://../"+str(manifest.preparation_support_plan)))
	var front:Dictionary=JSON.parse_string(FileAccess.get_file_as_string("res://../"+str(manifest.preparation_front_plan)))
	assert(support.source_sha256==spec.source_sha256)
	var meshes:Array=body.find_children("*","MeshInstance3D",true,false)
	if mouth:meshes.append_array(mouth.find_children("*","MeshInstance3D",true,false))
	meshes.sort_custom(func(a,b):return a.get_path().get_name_count()<b.get_path().get_name_count())
	var offsets:Dictionary={};var homes:Dictionary={}
	for mesh in meshes:
		var name:=str(mesh.name);assert(not homes.has(name));homes[name]=mesh.global_transform;offsets[name]=Vector3.ZERO if name in support.fixed_adapter_names else body.global_basis*Vector3.UP*.45
		originals.append({"node":mesh,"home":mesh.transform})
	for g in support.groups+support.legs+support.ports:
		for name in g.names:assert(homes.has(name));offsets[name]+=body.global_basis*converted(g.offset)
	for g in front.groups:
		if g.id not in ["cover_03","pin_cap_03","pin_03"]:continue
		for name in g.meshes:assert(homes.has(name));offsets[name]+=body.global_basis*converted(g.offset_blender)
	for mesh in meshes:
		var pose:Transform3D=homes[str(mesh.name)];pose.origin+=offsets[str(mesh.name)];mesh.global_transform=pose
func restore()->void:
	for item in originals:
		if is_instance_valid(item.node):item.node.transform=item.home
	originals.clear()
