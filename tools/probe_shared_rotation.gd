extends SceneTree
func _initialize()->void:run.call_deferred()
func run()->void:
	set_meta("collection_no_save",true);set_meta("collection_no_audio",true);set_meta("collection_skip_intro",true)
	var scene:Node=load("res://main.tscn").instantiate();root.add_child(scene)
	for i in range(10):await process_frame
	var host:Node3D=scene.get_node("Render/HeliosDesktop");host.set_process(false)
	var result:={"camera":str(host.camera.global_transform),"canvas":str(host.canonical_size),"base_points":host.desktop_base_points,"controls":[],"proposals":[]}
	for i in range(host.buttons.size()):
		var p:Vector3=host.buttons[i].mount.global_position
		result.controls.append({"index":i,"world":[p.x,p.y,p.z],"screen":str(host.camera.unproject_position(p))})
	for p in [Vector3(1.34,.18,-.1),Vector3(1.90,.32,-.10),Vector3(1.90,.40,-.30)]:
		result.proposals.append({"world":[p.x,p.y,p.z],"screen":str(host.camera.unproject_position(p))})
	var mesh:MeshInstance3D=host.named("BASE_FIXED_DisplayMesh");var levels:Dictionary={}
	for i in range(mesh.mesh.get_surface_count()):
		var arrays:Array=mesh.mesh.surface_get_arrays(i)
		for v in arrays[Mesh.ARRAY_VERTEX]:
			var world:Vector3=mesh.to_global(v);var level:=snappedf(world.y,.001)
			if level>.08 and level<.30:levels[level]=maxf(float(levels.get(level,0)),Vector2(world.x,world.z).length())
	result.base_radius_by_height=levels
	await physics_frame
	result.port_surfaces=[]
	for angle in [.20,.28,.36,.44]:
		var radial:=Vector3(cos(angle),0,sin(angle));var origin:=radial*2.+Vector3.UP*.145
		var query:=PhysicsRayQueryParameters3D.create(origin,radial*.7+Vector3.UP*.145,31)
		var hit:Dictionary=host.get_world_3d().direct_space_state.intersect_ray(query)
		if not hit.is_empty():result.port_surfaces.append({"angle":angle,"position":str(hit.position),"normal":str(hit.normal),"screen":str(host.camera.unproject_position(hit.position)),"collider":str(hit.collider.name)})
	FileAccess.open("res://../production/shared_rotation/layout_probe.json",FileAccess.WRITE).store_string(JSON.stringify(result,"  "))
	print("ROTATION_LAYOUT ",JSON.stringify(result));scene.queue_free();await process_frame;quit()
