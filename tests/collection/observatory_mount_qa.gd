extends SceneTree
## Check the candidate's real underside pocket against the original disc.
func _initialize()->void:run.call_deferred()
func run()->void:
	var host:=Node3D.new();root.add_child(host)
	var stem:="res://assets/collection/models/G_optical_curator_observatory_candidate"
	var data:Dictionary=JSON.parse_string(FileAccess.get_file_as_string(stem+".json"))
	var model:Node3D=load("res://collection/module.gd").new();host.add_child(model);model.data=data;model.power=1.;model.open_target=1.
	model.asset=load(stem+".glb").instantiate();model.add_child(model.asset)
	model.play=load("res://collection/play_state.gd").new();model.play.values={"leaf":0.,"fold":.5,"imprint":0.,"spin":1.}
	var player:RefCounted=load("res://collection/optical_curator.gd").new();player.setup(model);model.play.g_instrument=player
	player.loaded_index=0;player.owners[0]="platter";player.print_amount=1.;player.stage="playing";player.apply()
	for mesh in player.media[0].find_children("*","MeshInstance3D",true,false):
		var body:=StaticBody3D.new();body.collision_layer=2;body.collision_mask=0;var shape:=CollisionShape3D.new();shape.shape=mesh.mesh.create_trimesh_shape();body.add_child(shape);mesh.add_child(body)
	var meshes:Array=[]
	for mesh in player.content[0].node.find_children("*","MeshInstance3D",true,false):
		for s in range(mesh.mesh.get_surface_count()):meshes.append({"node":mesh,"vertices":mesh.mesh.surface_get_arrays(s)[Mesh.ARRAY_VERTEX]})
	var minimum:=INF;var hits:=0
	for angle in [0.,.9,2.1,3.5]:
		player.platter_angle=angle;player.apply();await physics_frame
		var center:Vector3=player.media[0].global_position
		for item in meshes:
			for v in item.vertices:
				var point:Vector3=item.node.to_global(v)
				if point.y>center.y+.06:continue
				var ray:=PhysicsRayQueryParameters3D.create(Vector3(point.x,center.y+.065,point.z),Vector3(point.x,center.y-.035,point.z),2)
				var contact:Dictionary=model.get_world_3d().direct_space_state.intersect_ray(ray)
				if not contact.is_empty():minimum=minf(minimum,point.y-contact.position.y);hits+=1
	var report:={"passed":hits>100 and minimum>=.0002,"minimum_clearance":minimum,"surface_hits":hits,"sample_angles":4,"model_sha256":FileAccess.get_sha256(stem+".glb"),"scope":"Candidate lower vertices vs original disc including label/spindle; not full moving component clearance"}
	FileAccess.open("res://../review/G_optical_curator/observatory_r2/mount_clearance.json",FileAccess.WRITE).store_string(JSON.stringify(report,"  "));print("OBSERVATORY_MOUNT ",JSON.stringify(report));host.free();quit(0 if report.passed else 2)
