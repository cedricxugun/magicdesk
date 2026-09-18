extends SceneTree
const OUT:="res://../review/F_complete/revision_20260911/installation/"
var geometry:Dictionary={}
var nodes:Array=[]
func _initialize()->void:run.call_deferred()
func pack(t:Transform3D)->Array:
	return [[t.basis.x.x,t.basis.y.x,t.basis.z.x,t.origin.x],[t.basis.x.y,t.basis.y.y,t.basis.z.y,t.origin.y],[t.basis.x.z,t.basis.y.z,t.basis.z.z,t.origin.z],[0,0,0,1]]
func register_mesh(mesh:MeshInstance3D,group:String,owner:Node)->void:
	if mesh.mesh is PrimitiveMesh:return # Runtime optical quads are not physical hardware.
	var key:=str(mesh.mesh.get_instance_id());var label:=group+"/"+str(owner.get_path_to(mesh))
	if not geometry.has(key):
		var vertices:Array=[];var triangles:Array=[]
		for i in range(mesh.mesh.get_surface_count()):
			var arrays:Array=mesh.mesh.surface_get_arrays(i);var offset:=vertices.size()
			for v in arrays[Mesh.ARRAY_VERTEX]:vertices.append([v.x,v.y,v.z])
			var indices:PackedInt32Array=arrays[Mesh.ARRAY_INDEX]
			if indices.is_empty():
				for j in range(0,arrays[Mesh.ARRAY_VERTEX].size(),3):triangles.append([offset+j,offset+j+1,offset+j+2])
			else:
				for j in range(0,indices.size(),3):triangles.append([offset+indices[j],offset+indices[j+1],offset+indices[j+2]])
		geometry[key]={"vertices":vertices,"triangles":triangles}
	nodes.append({"node":mesh,"id":label,"geometry":key,"group":group})
func run()->void:
	set_meta("collection_no_save",true);set_meta("collection_no_audio",true);set_meta("collection_skip_intro",true)
	DirAccess.make_dir_recursive_absolute(OUT)
	var scene:Node=load("res://main.tscn").instantiate();root.add_child(scene)
	for i in range(10):await process_frame
	var host:Node3D=scene.get_node("Render/HeliosDesktop");host.set_process(false);host.muted=true;host.rotation_enabled=false
	var service:Node3D=host.collection;service._legacy_set_visible(false);service._set_base_frame("shared")
	var data:Dictionary=JSON.parse_string(FileAccess.get_file_as_string("res://assets/collection/models/F_complete.json"))
	var module:Node3D=load("res://collection/module.gd").new();service.add_child(module);module.setup(host,data,load("res://assets/collection/models/F_complete.glb"));service.current=module;service.active_id="F";service._build_controls()
	for i in range(8):await physics_frame;service.tick(1./60.)
	assert(service.f_console.projected)
	for control in service.custom_controls:
		for mesh in control.node.find_children("*","MeshInstance3D",true,false):register_mesh(mesh,"F_controls",control.node.get_parent())
	# Only moving selector mechanisms, excluding its fixed shared front panel.
	var registered:Dictionary={}
	for control in service.selector_controls:
		for mesh in control.node.find_children("*","MeshInstance3D",true,false):
			if registered.has(mesh.get_instance_id()):continue
			registered[mesh.get_instance_id()]=true;register_mesh(mesh,"selector",service.selector)
	var samples:Array=[]
	for i in range(101):
		var amount:=i/100.;service.selector_amount=amount;service.selector_target=amount;service.tick(0.)
		var poses:Dictionary={}
		for item in nodes:
			if item.node.is_visible_in_tree():poses[item.id]=pack(item.node.global_transform)
		samples.append({"amount":amount,"poses":poses})
	var inventory:Array=[]
	for item in nodes:inventory.append({"id":item.id,"group":item.group,"geometry":item.geometry})
	var result:={"geometry":geometry,"nodes":inventory,"samples":samples,"controls_sha256":FileAccess.get_sha256("res://assets/collection/f_refined_controls.glb"),"selector_sha256":FileAccess.get_sha256("res://assets/collection/models/S.glb"),"scope":"Actual imported physical meshes/world transforms, moving cowl/rails/plaques against F controls across 101 opening fractions. No fixed socket/base contact classification, upper-body clearance or native input claim."}
	FileAccess.open(OUT+"selector_sweep_take.json",FileAccess.WRITE).store_string(JSON.stringify(result,""));print("F_SELECTOR_SWEEP_TAKE ",nodes.size()," nodes; ",samples.size()," poses")
	module=null;service=null;host=null;nodes.clear();scene.queue_free();await process_frame;await process_frame;quit()
