extends SceneTree
var out:="res://../review/I_refinement/nautilus_r1/rear03_release_r70/two_stage_r5/views/"
func _initialize()->void:run.call_deferred()
func _process(delta:float)->bool:RenderingServer.force_draw(false,delta);return false
func converted(a:Array)->Vector3:return Vector3(a[0],a[2],-a[1])
func run()->void:
	RenderingServer.set_render_loop_enabled(false);DirAccess.make_dir_recursive_absolute(out);root.size=Vector2i(1400,1100);root.transparent_bg=false;root.msaa_3d=Viewport.MSAA_4X
	var spec:Dictionary=JSON.parse_string(FileAccess.get_file_as_string("res://../review/I_refinement/nautilus_r1/port_edge_r68/build.json"))
	var support:Dictionary=JSON.parse_string(FileAccess.get_file_as_string("res://../review/I_refinement/nautilus_r1/port_edge_r68/release_probe/probe.json"))
	var front:Dictionary=JSON.parse_string(FileAccess.get_file_as_string("res://../review/I_refinement/nautilus_r1/service_r63/stage03_wide/plan.json"))
	var rear:Dictionary=JSON.parse_string(FileAccess.get_file_as_string("res://../review/I_refinement/nautilus_r1/rear03_release_r70/two_stage_r5/probe.json"))
	assert(rear.source_sha256==spec.source_sha256 and support.source_sha256==spec.source_sha256)
	var world:=Node3D.new();root.add_child(world)
	var env:=Environment.new();env.background_mode=Environment.BG_COLOR;env.background_color=Color(.04,.045,.05);env.tonemap_mode=Environment.TONE_MAPPER_AGX
	var panorama:=PanoramaSkyMaterial.new();panorama.panorama=load("res://assets/studio_small_09_4k.exr");panorama.energy_multiplier=.30
	env.sky=Sky.new();env.sky.sky_material=panorama;env.ambient_light_source=Environment.AMBIENT_SOURCE_SKY;env.ambient_light_energy=.42;env.reflected_light_source=Environment.REFLECTION_SOURCE_SKY
	var environment:=WorldEnvironment.new();environment.environment=env;world.add_child(environment)
	var body:Node3D=load("res://"+str(spec.component).trim_prefix("app/")).instantiate();world.add_child(body);load("res://collection/i_finish_r38.gd").apply(body,str(spec.finish_profile))
	var driver:RefCounted=load("res://collection/i_nautilus_form_driver.gd").new();driver.bind(body,spec);driver.set_opening(1.)
	var mouth:Node3D=load("res://"+str(spec.mouth_component).trim_prefix("app/")).instantiate();world.add_child(mouth)
	var p:Array=spec.mouth_placement.p;var q:Array=spec.mouth_placement.q;var scales:Array=spec.mouth_placement.s
	mouth.transform=Transform3D(Basis(Quaternion(q[0],q[1],q[2],q[3])).scaled(Vector3(scales[0],scales[1],scales[2])),Vector3(p[0],p[1],p[2]))
	var donor:Node3D=load("res://assets/helios_model.glb").instantiate();world.add_child(donor);var base:Node3D=donor.find_child("BASE_FIXED",true,false);base.reparent(world,true);donor.queue_free();await process_frame
	var meshes:Array=[];meshes.append_array(body.find_children("*","MeshInstance3D",true,false));meshes.append_array(mouth.find_children("*","MeshInstance3D",true,false));meshes.sort_custom(func(a,b):return a.get_path().get_name_count()<b.get_path().get_name_count())
	var homes:Dictionary={};var offsets:Dictionary={};var targets:Dictionary={}
	for mesh in meshes:homes[str(mesh.name)]=mesh.global_transform;offsets[str(mesh.name)]=Vector3.ZERO if str(mesh.name)in support.fixed_adapter_names else Vector3.UP*.45;targets[str(mesh.name)]=mesh
	for g in support.groups+support.legs+support.ports:
		for name in g.names:assert(targets.has(name));offsets[name]+=converted(g.offset)
	for g in front.groups:
		if g.id not in ["cover_03","pin_cap_03","pin_03"]:continue
		for name in g.meshes:assert(targets.has(name));offsets[name]+=converted(g.offset_blender)
	for g in rear.groups:
		for name in g.names:assert(targets.has(name))
	for row in [[Vector3(3.2,5.2,4),20.],[Vector3(-3.,4,-3),16.],[Vector3(4.,2.5,-5.),8.]]:
		var light:=AreaLight3D.new();world.add_child(light);light.position=row[0];light.look_at(Vector3(0,2.,0));light.light_energy=row[1];light.area_size=Vector2(2.,3.);light.area_normalize_energy=true;light.area_range=18.;light.shadow_enabled=true;light.shadow_normal_bias=.1
	var camera:=Camera3D.new();world.add_child(camera);camera.near=.01;camera.fov=38.;camera.current=true
	var canvas:=CanvasLayer.new();root.add_child(canvas);var label:=Label.new();canvas.add_child(label);label.position=Vector2(24,18);label.add_theme_font_size_override("font_size",22)
	var receipts:Array=[]
	for stage in range(5):
		var delta:Dictionary=offsets.duplicate(true)
		for g in rear.groups:
			var movement:=Vector3.ZERO;var normal:=converted(g.normal)
			if str(g.id).begins_with("rear_bolt") and stage>=1:movement+=normal*.010
			if (g.id=="cassette03" or str(g.id).begins_with("rear_bolt")) and stage>=2:movement+=normal*.8
			if g.id=="rear_shell03" and stage>=3:movement+=converted(rear.shell_waypoints[1 if stage==3 else 2])
			for name in g.names:delta[name]+=movement
		for mesh in meshes:
			var pose:Transform3D=homes[str(mesh.name)];pose.origin+=delta[str(mesh.name)];mesh.global_transform=pose
		var maximum:=0.
		for mesh in meshes:maximum=maxf(maximum,mesh.global_position.distance_to(homes[str(mesh.name)].origin+delta[str(mesh.name)]))
		assert(maximum<.000002)
		label.text=["准备态 · 前罩与支柱已移开","后壳螺栓旋松 · 仍留在总成孔道","导向总成离座 · 螺栓随行","后壳先向下避让","后壳向后展开 · 保留完整边缘"][stage]
		camera.position=Vector3(5.7,4.,-5.2);camera.look_at(Vector3(.15,1.9,-.2))
		for i in range(6):await RenderingServer.frame_post_draw
		root.get_texture().get_image().save_png(out+"stage_%d.png"%stage)
		receipts.append({"stage":stage,"position_max_error":maximum,"meshes":meshes.size()})
	FileAccess.open(out+"receipt.json",FileAccess.WRITE).store_string(JSON.stringify({"source_sha256":spec.source_sha256,"rows":receipts,"scope":"Actual imported geometry in measured static preparation and rear-release poses. Not an authored motion, full service demonstration or main App interaction."},"  "))
	for light in world.find_children("*","AreaLight3D",true,false):light.queue_free()
	for i in range(3):await RenderingServer.frame_post_draw
	world.queue_free();await process_frame;quit()
