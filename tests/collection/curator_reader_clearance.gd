extends SceneTree
## Ray-test the actual imported record surface below the actual reader vertices.
var player:RefCounted
var model:Node3D
var meshes:Array=[]
var checks:Array=[]
func _initialize()->void:run.call_deferred()
func measure(extra:float)->Dictionary:
	var origin:float=model.data.record_player.tone_origin[1]
	player.spec.tone_origin[1]=origin+extra
	var minimum:=INF;var rays:=0;var hits:=0
	for i in range(13):
		player.tone_angle=player.scan_angle(lerpf(.35,.105,i/12.));player.tone_lift=0;player.apply()
		await physics_frame
		var center:Vector3=player.media[0].global_position
		for item in meshes:
			for v in item.vertices:
				var p:Vector3=item.node.to_global(v)
				if Vector2(p.x-center.x,p.z-center.z).length()>.43 or p.y>center.y+.09:continue
				var query:=PhysicsRayQueryParameters3D.create(Vector3(p.x,center.y+.09,p.z),Vector3(p.x,center.y-.04,p.z),2)
				var hit:Dictionary=model.get_world_3d().direct_space_state.intersect_ray(query);rays+=1
				if not hit.is_empty():minimum=minf(minimum,p.y-hit.position.y);hits+=1
	player.spec.tone_origin[1]=origin
	return {"origin":origin+extra,"minimum_clearance":minimum,"rays":rays,"hits":hits,"passed":hits>100 and minimum>=.004}
func run()->void:
	var host:=Node3D.new();root.add_child(host)
	var data:Dictionary=JSON.parse_string(FileAccess.get_file_as_string("res://assets/collection/models/G_optical_curator.json"))
	model=load("res://collection/module.gd").new();host.add_child(model);model.data=data;model.power=1.;model.open_target=1.
	model.asset=load("res://assets/collection/models/G_optical_curator.glb").instantiate();model.add_child(model.asset)
	model.play=load("res://collection/play_state.gd").new();model.play.values={"leaf":0.,"fold":.5,"imprint":0.,"spin":1.}
	player=load("res://collection/optical_curator.gd").new();player.setup(model);model.play.g_instrument=player
	player.loaded_index=0;player.owners[0]="platter";player.stage="reading";player.apply()
	for mesh in player.media[0].find_children("*","MeshInstance3D",true,false):
		var body:=StaticBody3D.new();body.collision_layer=2;body.collision_mask=0;var collision:=CollisionShape3D.new();collision.shape=mesh.mesh.create_trimesh_shape();body.add_child(collision);mesh.add_child(body)
	for mesh in player.tone.find_children("*","MeshInstance3D",true,false):
		for surface in range(mesh.mesh.get_surface_count()):meshes.append({"node":mesh,"vertices":mesh.mesh.surface_get_arrays(surface)[Mesh.ARRAY_VERTEX]})
	await physics_frame
	var current:Dictionary=await measure(0.)
	var report:={"current":current,"model_sha256":FileAccess.get_sha256("res://assets/collection/models/G_optical_curator.glb"),"scope":"13 read radii, actual reader vertices vs the imported record surface including grooves and label"}
	if OS.get_cmdline_user_args().has("--candidate"):report.candidate=await measure(.018)
	FileAccess.open("res://../review/G_optical_curator/operating/reader_clearance.json",FileAccess.WRITE).store_string(JSON.stringify(report,"  "));print("CURATOR_READER_CLEARANCE ",JSON.stringify(report));host.free();quit(0 if current.passed else 2)
