extends SceneTree
var host:Node3D
var service:Node3D
var module:Node3D
var out:="res://../review/F_complete/revision_20260911/gears/render/"
func payload_bounds_error()->float:
	var payload:Dictionary=JSON.parse_string(FileAccess.get_file_as_string("res://../review/F_complete/revision_20260911/gears/mesh_payload.json"))
	var error:=0.
	for name in payload:
		var mesh:MeshInstance3D=module.named(name);var root_node:Node3D=mesh.get_parent()
		for surface in range(mesh.mesh.get_surface_count()):
			var material:Material=mesh.get_active_material(surface);var source:String=str(material.get_meta("source_material"))
			var values:Array=payload[name][source].positions
			var expected:=AABB(Vector3(values[0],values[1],values[2]),Vector3.ZERO)
			for i in range(0,values.size(),3):expected=expected.expand(Vector3(values[i],values[i+1],values[i+2]))
			var vertices:PackedVector3Array=mesh.mesh.surface_get_arrays(surface)[Mesh.ARRAY_VERTEX]
			var relative:Transform3D=root_node.global_transform.affine_inverse()*mesh.global_transform
			var actual:=AABB(relative*vertices[0],Vector3.ZERO)
			for point in vertices:actual=actual.expand(relative*point)
			error=maxf(error,maxf(expected.position.distance_to(actual.position),expected.end.distance_to(actual.end)))
	return error
func _initialize()->void:run.call_deferred()
func capture(label:String)->void:
	for i in range(4):await RenderingServer.frame_post_draw
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
		var path:="res://assets/collection/models/F_gears_candidate" if candidate else "res://assets/collection/models/F_complete"
		var data:Dictionary=JSON.parse_string(FileAccess.get_file_as_string(path+".json"))
		module=load("res://collection/module.gd").new();service.add_child(module);module.setup(host,data,load(path+".glb"));service.current=module;service.active_id="F";service._build_controls()
		for i in range(8):await physics_frame;service.tick(1./60.)
		host.tooltip.hide();host.toast.hide();module.effect.f_visuals.hide()
		var prefix:="B_involute" if candidate else "A_block"
		var bounds_error:float=payload_bounds_error() if candidate else 0.
		assert(bounds_error<.000005,"Gear render-surface local frame mismatch")
		host.camera.global_transform=home;host.camera.fov=fov;await capture(prefix+"_desktop")
		var focus:Vector3=(module.named("F2_MainGear").global_position+module.named("F2_CounterGear").global_position)*.5
		host.camera.global_position=focus+Vector3(.38,.18,1.6);host.camera.look_at(focus);host.camera.fov=32.
		await capture(prefix+"_neutral")
		var poses:Array=[]
		if candidate:
			for trim in [1.,-1.,0.]:
				module.play.input("trim",trim,"begin");module.play.input("trim",trim,"release")
				for i in range(200):
					service.tick(1./60.)
					if i%40==0:await RenderingServer.frame_post_draw
				await capture(prefix+"_trim_"+str(trim))
				var row:={"trim":module.play.instrument.preload_value,"roots":{}}
				for name in ["F2_MainGear","F2_CounterGear"]:
					var node:Node3D=module.named(name);row.roots[name]={"origin":str(node.position),"basis":str(node.basis)}
				poses.append(row)
		var route_error:=0.
		if candidate:
			module.stow()
			for i in range(900):service.tick(1./60.)
			var source:Dictionary=JSON.parse_string(FileAccess.get_file_as_string("res://../review/F_complete/revision_20260911/gears/route_source.json"))
			for sample in source.samples:
				module.explosion=sample.explosion;module.apply_pose()
				var p:Array=sample.godot_local_position
				route_error=maxf(route_error,module.named("F2_P_Differential").position.distance_to(Vector3(p[0],p[1],p[2])))
				await capture("B_service_"+str(sample.frame))
			assert(route_error<.000002,"Source/runtime disassembly route mismatch")
		observations.append({"candidate":candidate,"glb_sha256":FileAccess.get_sha256(path+".glb"),"poses":poses,"source_root_bounds_error":bounds_error,"source_route_error":route_error,"one_base":service.diagnostics().base_instances==1})
		service.current=null;module.queue_free();module=null;await process_frame;await process_frame
	var result:={"observations":observations,"scope":"Actual Metal before/after and real control-driven end/reversal poses. Precise flank/neighbor clearance is separate."}
	FileAccess.open(out+"review.json",FileAccess.WRITE).store_string(JSON.stringify(result,"  "));print("F_GEAR_RENDER ",JSON.stringify(result))
	host=null;service=null;scene.queue_free();await process_frame;await process_frame;quit()
