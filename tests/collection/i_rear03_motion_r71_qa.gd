extends SceneTree
func _initialize()->void:run.call_deferred()
func run()->void:
	var out:="res://../review/I_refinement/nautilus_r1/rear03_motion_r71/"
	var spec:Dictionary=JSON.parse_string(FileAccess.get_file_as_string("res://../review/I_refinement/nautilus_r1/port_edge_r68/build.json"))
	var manifest:Dictionary=JSON.parse_string(FileAccess.get_file_as_string("res://assets/collection/art/I/rear03_motion_r71/rear03_motion.json"))
	var body:Node3D=load("res://"+str(spec.component).trim_prefix("app/")).instantiate();root.add_child(body)
	var opening:RefCounted=load("res://collection/i_nautilus_form_driver.gd").new();opening.bind(body,spec);opening.set_opening(1.)
	var preparation:RefCounted=load("res://review/i_rear03_preparation.gd").new();preparation.apply(body,null,spec,manifest)
	var original_poses:Array=preparation.originals.duplicate(true)
	var driver:RefCounted=load("res://review/i_service03_driver.gd").new();driver.bind(body,spec,manifest)
	var maximum:=0.;var landmarks:=0;var failures:Array=[]
	for sample in manifest.source_witnesses:
		driver.seek(sample.time)
		for name in sample.points:
			var node:Node3D=body.find_child(name,true,false)
			for i in range(manifest.local_points.size()):
				var p:Array=manifest.local_points[i];var q:Array=sample.points[name][i]
				var error:=node.to_global(Vector3(p[0],p[1],p[2])).distance_to(Vector3(q[0],q[1],q[2]));maximum=maxf(maximum,error);landmarks+=1
				if error>=.00001:failures.append({"time":sample.time,"node":name,"error":error})
	var animation:Animation=driver.player.get_animation(manifest.clip);var tracks:Array=[]
	for i in range(animation.get_track_count()):tracks.append({"path":str(animation.track_get_path(i)),"keys":animation.track_get_key_count(i),"type":animation.track_get_type(i)})
	FileAccess.open(out+"pose_diagnostic.json",FileAccess.WRITE).store_string(JSON.stringify({"failures":failures,"tracks":tracks,"maximum":maximum},"  "))
	assert(failures.is_empty(),"Source/imported motion mismatches; see pose_diagnostic.json")
	body.rotation.y=.45
	for sample in manifest.source_witnesses:
		driver.seek(sample.time)
		for name in sample.points:
			var node:Node3D=body.find_child(name,true,false)
			var p:Array=manifest.local_points[0];var q:Array=sample.points[name][0]
			assert(node.to_global(Vector3(p[0],p[1],p[2])).distance_to(body.to_global(Vector3(q[0],q[1],q[2])))<.00001,"Display rotation broke service-space binding")
	driver.seek(0.);driver.request(true)
	for i in range(120):driver.tick(1./60.)
	var before:float=driver.time;driver.request(false);var old_velocity:float=driver.velocity;driver.tick(1./60.)
	assert(absf(driver.time-before)<.017 and absf(driver.velocity-old_velocity)<.067)
	for i in range(600):driver.tick(1./60.)
	assert(driver.stowed(),"Cancelled service did not return to exact prepared home")
	for b in driver.bindings:
		for item in b.targets:
			var actual:Transform3D=item.node.transform;var home:Transform3D=item.home
			for axis in range(3):
				assert(float(actual.origin[axis])==float(home.origin[axis]))
				for column in range(3):assert(float(actual.basis[column][axis])==float(home.basis[column][axis]))
	driver.request(true)
	for i in range(600):driver.tick(1./60.)
	assert(driver.time==driver.duration)
	driver.request(false)
	for i in range(600):driver.tick(1./60.)
	assert(driver.stowed())
	driver.release();driver=null;body.rotation.y=0.;preparation.restore()
	for item in original_poses:
		var pose:Transform3D=item.node.transform;var expected:Transform3D=item.home
		for i in range(3):
			assert(pose.origin[i]==expected.origin[i])
			for j in range(3):assert(pose.basis[i][j]==expected.basis[i][j])
	FileAccess.open(out+"runtime_qa.json",FileAccess.WRITE).store_string(JSON.stringify({"passed":true,"source_landmarks":landmarks,"maximum_source_error":maximum,"motion_source_sha256":manifest.motion_source_sha256,"motion_asset_sha256":manifest.motion_asset_sha256,"scope":"Actual body plus imported authored marker animation. Independent Blender target landmarks, smooth time reversal, full return and exact prepared-pose restoration. No full service, native input or continuous collision acceptance."},"  "))
	body.queue_free();await process_frame;await process_frame;print("REAR03_RUNTIME true");quit()
