extends SceneTree
var host:Node3D
var asset:Node3D
var driver:Node
var out:="res://../review/I_refinement/r2/runtime/"
var component:="res://assets/collection/components/I_pneumatic_r2.glb"
func _initialize()->void:run.call_deferred()
func capture(label:String)->void:
	for i in range(4):await RenderingServer.frame_post_draw
	host.render_view.get_texture().get_image().save_png(out+label+".png")
func run()->void:
	for arg in OS.get_cmdline_user_args():
		if arg.begins_with("--component="):component=arg.trim_prefix("--component=")
		if arg.begins_with("--out="):out=arg.trim_prefix("--out=")
	set_meta("collection_no_save",true);set_meta("collection_no_audio",true);set_meta("collection_skip_intro",true)
	DirAccess.make_dir_recursive_absolute(out)
	var scene:Node=load("res://main.tscn").instantiate();root.add_child(scene)
	for i in range(12):await process_frame
	host=scene.get_node("Render/HeliosDesktop");host.set_process(false);host.muted=true;host.power=1.;host.power_target=1.
	host.collection._legacy_set_visible(false);host.collection._set_base_frame("shared")
	host.env.ambient_light_energy=.35;var energies:Array=[24.,25.,4.];var count:=0
	for child in host.get_children():
		if child is AreaLight3D:child.light_energy=energies[count];child.light_size=.35;count+=1
	asset=load(component).instantiate();host.add_child(asset)
	driver=load("res://collection/i_runtime.gd").new();asset.add_child(driver);driver.setup(asset)
	var take:Dictionary=JSON.parse_string(FileAccess.get_file_as_string("res://../review/I_refinement/r2/pneumatic_take.json"))
	var source:Dictionary=JSON.parse_string(FileAccess.get_file_as_string("res://../review/I_refinement/r2/runtime_source_poses.json"))
	var samples:Dictionary={}
	for item in source.snapshots:samples[int(item.frame)]=item
	var errors:=0.;var states:Array=[]
	var camera_home:Transform3D=host.camera.global_transform;var camera_fov:float=host.camera.fov
	for sample in take.samples:
		driver.apply_state(sample.state,sample.opening)
		if samples.has(int(sample.frame)):
			var expected:Dictionary=samples[int(sample.frame)]
			for name in expected.poses:
				var t:Transform3D=asset.global_transform.affine_inverse()*driver.node(name).global_transform
				var rows:Array=expected.poses[name]
				var actual:Array=[[t.basis.x.x,t.basis.y.x,t.basis.z.x,t.origin.x],[t.basis.x.y,t.basis.y.y,t.basis.z.y,t.origin.y],[t.basis.x.z,t.basis.y.z,t.basis.z.z,t.origin.z],[0.,0.,0.,1.]]
				for y in range(4):
					for x in range(4):errors=maxf(errors,absf(float(actual[y][x])-float(rows[y][x])))
		if int(sample.frame) in [39,88,96,226]:
			await capture("whole_"+str(sample.frame))
			var bell:Node3D=driver.node("IH1_Bellows");host.camera.global_position=bell.global_position+bell.global_basis*Vector3(1.55,-.85,.25);host.camera.look_at(bell.global_position);host.camera.fov=40.
			var hidden:Array=[]
			for node in asset.find_children("*","MeshInstance3D",true,false):
				if str(node.name).contains("Porcelain") or str(node.name).contains("ChamberSpine") or str(node.name).contains("AcousticChamberRib") or str(node.name).contains("BrassReturnConductor"):node.hide();hidden.append(node)
			await capture("pressure_"+str(sample.frame))
			for node in hidden:node.show()
			host.camera.global_transform=camera_home;host.camera.fov=camera_fov
			states.append({"frame":sample.frame,"compression":driver.wall.get_blend_shape_value(driver.wall.find_blend_shape_by_name("Compression")),"front":str(driver.front.position),"diaphragm":str(driver.diaphragm.position)})
	var result:={"passed":errors<.00002,"source_pose_max_error":errors,"states":states,"component_sha256":FileAccess.get_sha256("res://assets/collection/components/I_pneumatic_r2.glb"),"source_sha256":source.source_sha256,"scope":"Actual Metal morph/control preview on shared base, saved Blender world poses compared at8 checkpoints. Cutaways hide porcelain; not native input, final controls, VFX or whole-model acceptance."}
	result.component=component;result.component_sha256=FileAccess.get_sha256(component)
	FileAccess.open(out+"review.json",FileAccess.WRITE).store_string(JSON.stringify(result,"  "));print("I_RUNTIME_REVIEW ",JSON.stringify(result))
	driver=null;asset=null;host=null;scene.queue_free();await process_frame;await process_frame;quit(0 if result.passed else 1)
