extends SceneTree
var host:Node3D
var service:Node3D
var module:Node3D
var out:="res://../review/F_complete/revision_20260911/finish/"
func _initialize()->void:run.call_deferred()
func capture(label:String)->void:
	for i in range(5):await RenderingServer.frame_post_draw
	host.render_view.get_texture().get_image().save_png(out+label+".png")
func run()->void:
	set_meta("collection_no_save",true);set_meta("collection_no_audio",true);set_meta("collection_skip_intro",true)
	DirAccess.make_dir_recursive_absolute(out)
	var scene:Node=load("res://main.tscn").instantiate();root.add_child(scene)
	for i in range(12):await process_frame
	host=scene.get_node("Render/HeliosDesktop");host.set_process(false);host.power=1.;host.power_target=1.;host.muted=true;host.angle=0.;host.rotation_enabled=false
	service=host.collection;service._legacy_set_visible(false);service._set_base_frame("shared")
	var home:Transform3D=host.camera.global_transform;var fov:float=host.camera.fov
	var observations:Array=[]
	for candidate in [false,true]:
		var data:Dictionary=JSON.parse_string(FileAccess.get_file_as_string("res://assets/collection/models/F_complete.json"))
		data.erase("finish_profile")
		if candidate:data.finish_profile="res://assets/collection/f_finish.json"
		module=load("res://collection/module.gd").new();service.add_child(module);module.setup(host,data,load("res://assets/collection/models/F_complete.glb"));service.current=module;service.active_id="F";service._build_controls()
		for i in range(8):await physics_frame;service.tick(1./60.)
		host.tooltip.hide();host.toast.hide()
		var label:="B_finish" if candidate else "A_original"
		host.camera.global_transform=home;host.camera.fov=fov;await capture(label+"_desktop")
		host.camera.global_position=Vector3(.6,2.60,3.0);host.camera.look_at(Vector3(.25,2.38,0.));host.camera.fov=35.;await capture(label+"_gear")
		host.camera.global_position=Vector3(-.4,1.7,-4.);host.camera.look_at(Vector3(-.32,1.8,0.));host.camera.fov=42.;await capture(label+"_back")
		if candidate:
			host.camera.global_position=Vector3(.6,2.60,3.0);host.camera.look_at(Vector3(.25,2.38,0.));host.camera.fov=35.
			for material in module.materials:
				if material.get_meta("f_finish","")=="chrome":material.set_shader_parameter("normal_depth",0.)
			await capture("C_chrome_no_normal")
			for material in module.materials:
				if material.get_meta("f_finish","")=="chrome":material.set_shader_parameter("normal_depth",.075)
		var finishes:Dictionary={}
		for material in module.materials:
			var key:String=str(material.get_meta("f_finish","baseline"))+":"+str(material.get_meta("source_material",""))
			finishes[key]={"metallic":material.get_shader_parameter("metallic"),"roughness":material.get_shader_parameter("roughness"),"coat":material.get_shader_parameter("coat"),"has_normal":material.get_shader_parameter("has_normal"),"has_roughness":material.get_shader_parameter("has_roughness")}
		observations.append({"candidate":candidate,"materials":finishes,"base_instances":service.diagnostics().base_instances})
		service.current=null;module.queue_free();module=null;await process_frame;await process_frame
	var result:={"observations":observations,"geometry_sha256":FileAccess.get_sha256("res://assets/collection/models/F_complete.glb"),"profile_sha256":FileAccess.get_sha256("res://assets/collection/f_finish.json"),"scope":"Metal A/B same pose/light/camera. Candidate opt-in only; no model metadata or Blender source changed by this harness."}
	FileAccess.open(out+"review.json",FileAccess.WRITE).store_string(JSON.stringify(result,"  "));print("F_FINISH_REVIEW ",JSON.stringify(result))
	host=null;service=null;scene.queue_free();await process_frame;await process_frame;quit()
