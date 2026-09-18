extends SceneTree
var checks:Array=[]
func _initialize()->void:run.call_deferred()
func check(name:String,passed:bool,detail:Variant=null)->void:checks.append({"name":name,"passed":passed,"detail":detail})
func run()->void:
	set_meta("collection_no_save",true);set_meta("collection_no_audio",true);set_meta("collection_skip_intro",true)
	var scene:Node=load("res://main.tscn").instantiate();root.add_child(scene)
	for i in range(10):await process_frame
	var host:Node3D=scene.get_node("Render/HeliosDesktop");host.set_process(false);host.power=1.;host.power_target=1.
	var service:Node3D=host.collection;service._legacy_set_visible(false);service._set_base_frame("shared")
	var data:Dictionary=JSON.parse_string(FileAccess.get_file_as_string("res://assets/collection/models/F_complete.json"))
	var module:Node3D=load("res://collection/module.gd").new();service.add_child(module);module.setup(host,data,load("res://assets/collection/models/F_complete.glb"));service.current=module;service.active_id="F";service._build_controls()
	for i in range(8):await physics_frame;service.tick(1./60.)
	check("all_engraving_vertices_mount_on_real_base",service.f_console.projected and service.f_console.projection_report.misses==0,{"vertices":service.f_console.projection_report.vertices,"misses":service.f_console.projection_report.misses})
	check("one_unchanged_shared_base",service.diagnostics().base_instances==1 and is_equal_approx(service.base_display.mesh.get_aabb().size.x,2.74))
	if data.has("finish_profile"):
		var finishes:Dictionary={}
		for material in module.materials:
			if material.has_meta("f_finish"):finishes[str(material.get_meta("f_finish"))]=material
		check("finish_classes_are_distinct",finishes.has_all(["brake_friction","blackened_steel","black_lacquer","red_enamel","porcelain"]))
		if finishes.has_all(["brake_friction","blackened_steel","black_lacquer","red_enamel","porcelain"]):
			check("brake_is_matte_nonmetal",float(finishes.brake_friction.get_shader_parameter("metallic"))==0. and float(finishes.brake_friction.get_shader_parameter("coat"))==0.)
			check("black_steel_not_shared_with_paint",finishes.blackened_steel!=finishes.black_lacquer and float(finishes.blackened_steel.get_shader_parameter("metallic"))>.8)
			check("red_enamel_is_coated_dielectric",float(finishes.red_enamel.get_shader_parameter("metallic"))==0. and float(finishes.red_enamel.get_shader_parameter("coat"))>.3)
	var controls:Dictionary={}
	for control in service.custom_controls:
		controls[control.index]=control
		var point:Vector2=host.camera.unproject_position(control.node.to_global(Vector3(0,0,.065)))
		check("physical_control_%d_is_pickable"%control.index,service.hit_control(point)==int(control.index))
	var driver:RefCounted=service.control_driver
	driver.index=5;driver.active=driver.profile(5);driver._set_value(1.,"change");driver.index=-1;driver.active={}
	for i in range(8):service.tick(1./60.)
	var lever:Node3D=controls[5].moving[0].node
	var pivot:Vector3=controls[5].node.to_local(lever.to_global(Vector3(0,0,.037)))
	var tip:Vector3=controls[5].node.to_local(lever.to_global(Vector3(0,.010,.127)))
	check("bias_lever_keeps_actual_pivot",pivot.distance_to(Vector3(0,0,.037))<.00001,pivot.distance_to(Vector3(0,0,.037)))
	check("positive_bias_physically_moves_up",tip.y>.030,tip.y)
	driver.index=1;driver.active=driver.profile(1);driver._set_value(.5,"change");driver.index=-1;driver.active={}
	for i in range(60):service.tick(1./60.)
	var dial:Node3D=controls[1].moving[0].node
	check("positive_preload_turns_clockwise",(controls[1].node.global_basis.inverse()*dial.global_basis*Vector3.UP).x>0.)
	var f:RefCounted=module.play.instrument;f.physics.theta=f.physics.REST
	check("balance_zero_is_gauge_center",absf(module.play.gauge_value()-.5)<.00001)
	f.physics.theta=f.physics.REST+.05;service.tick(0.)
	var needle:Node3D=controls[3].moving[0].node
	check("positive_angle_needle_points_right",(controls[3].node.global_basis.inverse()*needle.global_basis*Vector3.UP).x>0.)
	if OS.get_cmdline_user_args().has("--bake-caption-cache"):
		assert(service.f_console.projected,"Do not cache unseated type")
		var index:Dictionary=service.f_console.descriptor.duplicate(true);index.meshes={}
		DirAccess.make_dir_recursive_absolute("res://assets/collection/f_console_mounts")
		for item in service.f_console.legends:
			for mesh in item.patch.find_children("*","MeshInstance3D",true,false):
				var path:String="res://assets/collection/f_console_mounts/"+str(mesh.name)+".res"
				assert(ResourceSaver.save(mesh.mesh,path,ResourceSaver.FLAG_BUNDLE_RESOURCES)==OK)
				index.meshes[str(mesh.name)]=path
		FileAccess.open("res://assets/collection/f_console_mounts.json",FileAccess.WRITE).store_string(JSON.stringify(index,"  "))
		FileAccess.open("res://../review/F_complete/revision_20260911/engraving_geometry.json",FileAccess.WRITE).store_string(JSON.stringify(service.f_console.export_projection(),""))
	var result:={"passed":checks.all(func(c):return c.passed),"checks":checks,"console_sha256":FileAccess.get_sha256("res://assets/collection/f_refined_controls.glb"),"projection":service.f_console.projection_report,"scope":"Actual Godot control mounts, picking rays, signed motions, pivot continuity and engraved-surface projection. No native OS mouse input or cowl sweep acceptance."}
	FileAccess.open(output_path(),FileAccess.WRITE).store_string(JSON.stringify(result,"  "));print("F_CONSOLE_QA ",JSON.stringify(result))
	f=null;driver=null;module=null;service=null;host=null;scene.queue_free();await process_frame;await process_frame;quit(0 if result.passed else 1)

func output_path()->String:
	for arg in OS.get_cmdline_user_args():
		if arg.begins_with("--out="):return arg.trim_prefix("--out=")
	return "res://../review/F_complete/revision_20260911/console_runtime_qa.json"
