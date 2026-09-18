extends SceneTree
## Fixed production camera: service ordering, readability and exact reassembly.
var host:Node3D
var module:Node3D
var camera_home:Transform3D
var camera_fov:float
var frames:Array=[]
var moving_names:Array=[]
const OUT:="res://../review/G_optical_curator/service/"
func _initialize()->void:run.call_deferred()
func step(count:int)->void:
	for i in range(count):
		module.tick(1./30.,1.);await RenderingServer.frame_post_draw
		var poses:Dictionary={}
		for name in moving_names:
			var node:Node3D=module.named(name);var t:Transform3D=node.transform;var q:=t.basis.get_rotation_quaternion();var s:=t.basis.get_scale()
			poses[name]={"p":[t.origin.x,t.origin.y,t.origin.z],"q":[q.x,q.y,q.z,q.w],"s":[s.x,s.y,s.z]}
		frames.append({"frame":frames.size()+1,"poses":poses,"explosion":module.explosion,"state":module.play.g_instrument.diagnostics()})
func capture(label:String)->void:
	await RenderingServer.frame_post_draw
	var image:Image=host.render_view.get_texture().get_image();image.get_region(image.get_used_rect().grow(2).intersection(Rect2i(Vector2i.ZERO,image.get_size()))).save_png(OUT+label+".png")
func run()->void:
	set_meta("collection_skip_intro",true);set_meta("collection_no_save",true);DirAccess.make_dir_recursive_absolute(OUT)
	var scene:Node=load("res://main.tscn").instantiate();root.add_child(scene)
	for i in range(10):await process_frame
	host=scene.get_node("Render/HeliosDesktop");host.set_process(false);host.power=1.;host.muted=true;host.rotation_enabled=false;host.angle=0
	host.collection._legacy_set_visible(false);host.collection._set_base_frame("shared");host.tooltip.hide();host.toast.hide()
	module=load("res://collection/module.gd").new();host.collection.add_child(module)
	var data:Dictionary=JSON.parse_string(FileAccess.get_file_as_string("res://assets/collection/models/G_optical_curator.json"))
	module.setup(host,data,load("res://assets/collection/models/G_optical_curator.glb"));host.collection.current=module;host.collection.active_id="G";host.collection._build_controls()
	host.collection.lighting.select("G");host.collection.lighting.tick(1.)
	for part in data.parts:moving_names.append(part.name)
	var spec:Dictionary=data.record_player;var ai:Dictionary=data.optical_curator
	moving_names.append_array([spec.magazine,spec.upper_arm,spec.forearm,spec.wrist,spec.platter,spec.tonearm,ai.face,ai.carrier,ai.projector,ai.iris,ai.shoulder_fork,ai.wrist_yoke,ai.head_service.cam,ai.head_service.pinion]);moving_names.append_array(spec.cradles);moving_names.append_array(spec.records)
	for leaf in ai.leaves:moving_names.append(leaf.name)
	for link in ai.head_service.followers:moving_names.append(link.link)
	camera_home=host.camera.global_transform;camera_fov=host.camera.fov
	await step(15);await capture("00_assembled")
	module.activate(3)
	while module.explosion<.49:await step(1)
	await capture("01_banks_separated")
	while module.explosion<.73:await step(1)
	await capture("02_head_cartridges")
	while module.explosion<.999:await step(1)
	await step(12);await capture("03_full_service")
	var boxes:Array=[]
	for part in module.parts:
		var points:Array=[]
		collect_bounds(part.node,part.node,points)
		if points.is_empty():continue
		var rect:=Rect2(points[0],Vector2.ZERO)
		for point in points:rect=rect.expand(point)
		boxes.append({"part":str(part.node.name),"rect":[rect.position.x,rect.position.y,rect.size.x,rect.size.y],"on_canvas":Rect2(Vector2.ZERO,Vector2(host.render_view.size)).encloses(rect)})
	# A dedicated head detail follows only after the fixed-camera evidence.
	var face:Node3D=module.named(data.optical_curator.face);var target:=face.global_position+Vector3(0,.15,.05)
	host.camera.global_position=target+Vector3(.3,.35,3.5);host.camera.look_at(target);host.camera.fov=43
	await capture("04_head_service_detail")
	host.camera.global_transform=camera_home;host.camera.fov=camera_fov
	module.stow()
	for i in range(240):
		await step(1)
		if module.settled():break
	await capture("05_reassembled")
	var error:=0.
	for part in module.parts:error=maxf(error,part.node.transform.origin.distance_to(part.home.origin))
	var report:={"model_sha256":FileAccess.get_sha256("res://assets/collection/models/G_optical_curator.glb"),"parts":boxes,"fixed_camera":host.camera.global_transform.is_equal_approx(camera_home) and is_equal_approx(host.camera.fov,camera_fov),"reassembled":module.settled(),"max_part_return_error":error,"scope":"Image layout and return transforms; separate triangle sweep needed for transit clearance"}
	FileAccess.open(OUT+"service_take.json",FileAccess.WRITE).store_string(JSON.stringify({"fps":30,"model_sha256":report.model_sha256,"metadata_sha256":FileAccess.get_sha256("res://assets/collection/models/G_optical_curator.json"),"samples":frames}))
	FileAccess.open(OUT+"layout_report.json",FileAccess.WRITE).store_string(JSON.stringify(report,"  "));print("CURATOR_SERVICE_COMPLETE ",report.fixed_camera," ",report.reassembled," ",error);quit(0 if report.reassembled and error<.00001 else 2)
func collect_bounds(node:Node,part:Node,points:Array)->void:
	if node!=part and module.parts.any(func(p):return p.node==node):return
	if node is MeshInstance3D:
		var box:AABB=node.mesh.get_aabb()
		for i in range(8):points.append(host.camera.unproject_position(node.to_global(box.get_endpoint(i))))
	for child in node.get_children():
		if not child is StaticBody3D:collect_bounds(child,part,points)
