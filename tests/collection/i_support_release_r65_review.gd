extends SceneTree
var out:="res://../review/I_refinement/nautilus_r1/cradle_release_r65/lifted_legs_r2/views/"
func _initialize()->void:run.call_deferred()
func _process(delta:float)->bool:RenderingServer.force_draw(false,delta);return false
func run()->void:
	RenderingServer.set_render_loop_enabled(false);DirAccess.make_dir_recursive_absolute(out)
	root.size=Vector2i(1100,1050);root.transparent_bg=false;root.msaa_3d=Viewport.MSAA_4X
	var spec:Dictionary=JSON.parse_string(FileAccess.get_file_as_string("res://../review/I_refinement/nautilus_r1/curved_returns_r61/build.json"))
	var plan:Dictionary=JSON.parse_string(FileAccess.get_file_as_string("res://../review/I_refinement/nautilus_r1/cradle_release_r65/lifted_legs_r2/probe.json"));assert(plan.source_sha256==spec.source_sha256)
	var world:=Node3D.new();root.add_child(world)
	var env:=Environment.new();env.background_mode=Environment.BG_COLOR;env.background_color=Color(.03,.032,.034);env.tonemap_mode=Environment.TONE_MAPPER_AGX
	var panorama:=PanoramaSkyMaterial.new();panorama.panorama=load("res://assets/studio_small_09_4k.exr");panorama.energy_multiplier=.30
	env.sky=Sky.new();env.sky.sky_material=panorama;env.ambient_light_source=Environment.AMBIENT_SOURCE_SKY;env.ambient_light_energy=.42;env.reflected_light_source=Environment.REFLECTION_SOURCE_SKY
	var environment:=WorldEnvironment.new();environment.environment=env;world.add_child(environment)
	for row in [[Vector3(-3.2,4.8,4),20.,Vector2(2.6,4.)],[Vector3(3.5,4,-2),24.,Vector2(1.2,3.5)],[Vector3(0,2.5,6),4.,Vector2(4.,2.)]]:
		var light:=AreaLight3D.new();world.add_child(light);light.position=row[0];light.look_at(Vector3(0,2,0));light.light_energy=row[1];light.area_size=row[2];light.area_normalize_energy=true;light.area_range=18.;light.shadow_enabled=true;light.shadow_normal_bias=.10
	var body:Node3D=load("res://"+str(spec.component).trim_prefix("app/")).instantiate();world.add_child(body);load("res://collection/i_finish_r38.gd").apply(body,str(spec.finish_profile))
	var driver:RefCounted=load("res://collection/i_nautilus_form_driver.gd").new();driver.bind(body,spec);driver.set_opening(1.)
	var mouth:Node3D=load("res://"+str(spec.mouth_component).trim_prefix("app/")).instantiate();world.add_child(mouth)
	var p:Array=spec.mouth_placement.p;var q:Array=spec.mouth_placement.q;var scale_values:Array=spec.mouth_placement.s
	mouth.transform=Transform3D(Basis(Quaternion(q[0],q[1],q[2],q[3])).scaled(Vector3(scale_values[0],scale_values[1],scale_values[2])),Vector3(p[0],p[1],p[2]))
	var donor:Node3D=load("res://assets/helios_model.glb").instantiate();world.add_child(donor);var base:Node3D=donor.find_child("BASE_FIXED",true,false);base.reparent(world,true);donor.queue_free()
	var meshes:Array=[];meshes.append_array(body.find_children("*","MeshInstance3D",true,false));meshes.append_array(mouth.find_children("*","MeshInstance3D",true,false))
	meshes.sort_custom(func(a,b):return a.get_path().get_name_count()<b.get_path().get_name_count())
	var homes:Dictionary={};var targets:Dictionary={}
	for mesh in meshes:homes[mesh]=mesh.global_transform;targets[str(mesh.name)]=mesh
	for g in plan.groups+plan.legs:
		for name in g.names:assert(targets.has(name),"Missing actual imported member "+name)
	var camera:=Camera3D.new();world.add_child(camera);camera.position=Vector3(-3.,3.7,8.2);camera.look_at(Vector3(0,2.,0));camera.fov=34.;camera.current=true
	var canvas:=CanvasLayer.new();root.add_child(canvas);var label:=Label.new();canvas.add_child(label);label.position=Vector2(24,20);label.add_theme_font_size_override("font_size",19)
	var rows:Array=[]
	for stage in range(3):
		var offsets:Dictionary={}
		for mesh in meshes:offsets[str(mesh.name)]=Vector3.UP*.45 if stage>0 and str(mesh.name)not in plan.fixed_adapter_names else Vector3.ZERO
		if stage>0:
			for g in plan.groups:
				var a:Array=g.offset;var delta:=Vector3(a[0],a[2],-a[1])
				for name in g.names:offsets[name]+=delta
		if stage==2:
			for g in plan.legs:
				var a:Array=g.offset;var delta:=Vector3(a[0],a[2],-a[1])
				for name in g.names:offsets[name]+=delta
		for mesh in meshes:
			var pose:Transform3D=homes[mesh];pose.origin+=offsets[str(mesh.name)];mesh.global_transform=pose
		label.text=["准备态 · 支柱/安装座关系检查","固定座保留 · 上部升离与紧固件暂存","支柱沿原轴线退出 · 穿口仍留在壳板"][stage]
		for i in range(6):await RenderingServer.frame_post_draw
		root.get_texture().get_image().save_png(out+"stage_%d.png"%stage);rows.append({"stage":stage,"mesh_count":meshes.size(),"base_transform":str(base.global_transform)})
	FileAccess.open(out+"receipt.json",FileAccess.WRITE).store_string(JSON.stringify({"source_sha256":spec.source_sha256,"rows":rows,"scope":"Actual imported geometry in three source-probed poses. Static diagnostic only; not a baked animation, complete sequence or main App integration."},"  "))
	for light in world.find_children("*","AreaLight3D",true,false):light.queue_free()
	for i in range(3):await RenderingServer.frame_post_draw
	world.queue_free();await process_frame;quit()
