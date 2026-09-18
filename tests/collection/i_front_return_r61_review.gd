extends SceneTree
var out:="res://../review/I_refinement/nautilus_r1/curved_returns_r61/views_r2/"
var body:Node3D
var mouth:Node3D
var camera:Camera3D
var trim:MeshInstance3D
var driver:RefCounted
var rows:Array=[]
func _initialize()->void:run.call_deferred()
func _process(delta:float)->bool:RenderingServer.force_draw(false,delta);return false
func snap(name:String)->void:
	for i in range(6):await RenderingServer.frame_post_draw
	root.get_texture().get_image().save_png(out+name+".png")
	rows.append({"name":name,"trim_visible":trim.visible,"eye":str(camera.global_position),"target_mesh":str(trim.name),"trim_transform":str(trim.global_transform)})
func run()->void:
	RenderingServer.set_render_loop_enabled(false);DirAccess.make_dir_recursive_absolute(out)
	root.size=Vector2i(1100,1000);root.transparent_bg=false;root.msaa_3d=Viewport.MSAA_4X
	var spec:Dictionary=JSON.parse_string(FileAccess.get_file_as_string("res://../review/I_refinement/nautilus_r1/curved_returns_r61/build.json"))
	var world:=Node3D.new();root.add_child(world)
	var env:=Environment.new();env.background_mode=Environment.BG_COLOR;env.background_color=Color(.032,.032,.030)
	var panorama:=PanoramaSkyMaterial.new();panorama.panorama=load("res://assets/studio_small_09_4k.exr");panorama.energy_multiplier=.30
	env.sky=Sky.new();env.sky.sky_material=panorama;env.ambient_light_source=Environment.AMBIENT_SOURCE_SKY;env.ambient_light_energy=.42;env.reflected_light_source=Environment.REFLECTION_SOURCE_SKY;env.tonemap_mode=Environment.TONE_MAPPER_AGX
	env.ssao_enabled=true;env.ssao_radius=.08;env.ssao_intensity=.55;env.glow_enabled=false
	var environment:=WorldEnvironment.new();environment.environment=env;world.add_child(environment)
	for row in [[Vector3(-3.2,4.8,4),20.,Vector2(2.6,4.)],[Vector3(3.5,4,-2),24.,Vector2(1.2,3.5)],[Vector3(0,2.5,6),4.,Vector2(4.,2.)]]:
		var light:=AreaLight3D.new();world.add_child(light);light.position=row[0];light.look_at(Vector3(0,1.8,0));light.light_energy=row[1];light.area_size=row[2];light.area_normalize_energy=true;light.area_range=18.;light.light_size=.35;light.shadow_enabled=true;light.shadow_normal_bias=.10
	body=load("res://"+str(spec.component).trim_prefix("app/")).instantiate();world.add_child(body);load("res://collection/i_finish_r38.gd").apply(body,str(spec.finish_profile))
	driver=load("res://collection/i_nautilus_form_driver.gd").new();driver.bind(body,spec)
	mouth=load("res://"+str(spec.mouth_component).trim_prefix("app/")).instantiate();world.add_child(mouth)
	var p:Array=spec.mouth_placement.p;var q:Array=spec.mouth_placement.q;var scale_values:Array=spec.mouth_placement.s
	mouth.transform=Transform3D(Basis(Quaternion(q[0],q[1],q[2],q[3])).scaled(Vector3(scale_values[0],scale_values[1],scale_values[2])),Vector3(p[0],p[1],p[2]))
	var mouth_driver:RefCounted=load("res://collection/i_tongue_set_driver.gd").new();mouth_driver.bind(mouth,JSON.parse_string(FileAccess.get_file_as_string("res://../"+str(spec.mouth_report))));mouth_driver.set_opening(1.)
	var donor:Node3D=load("res://assets/helios_model.glb").instantiate();world.add_child(donor);var base:Node3D=donor.find_child("BASE_FIXED",true,false);base.reparent(world,true);donor.queue_free()
	trim=body.find_child("I61_FrontReturn_05",true,false);assert(trim!=null)
	var axis:Array=spec.front_return.coordinate_frame.axes[2];var normal_local:Vector3=trim.global_basis.inverse()*Vector3(-axis[0],-axis[2],axis[1])
	camera=Camera3D.new();world.add_child(camera);camera.fov=32.;camera.near=.01;camera.current=true
	for opening in [0.,1.]:
		driver.set_opening(opening)
		mouth_driver.set_opening(opening)
		camera.position=Vector3(-3,3.55,7.7);camera.look_at(Vector3(0,1.66,0))
		await snap("closed" if opening==0. else "open")
		if opening==1.:
			var center:Vector3=trim.to_global(trim.get_aabb().get_center());var normal:Vector3=(trim.global_basis*normal_local).normalized()
			camera.position=center+normal*1.35+Vector3(0,.16,0);camera.look_at(center)
			trim.hide();await snap("front_end_before")
			trim.show();await snap("front_end_after")
			for mesh in body.find_children("*","MeshInstance3D",true,false):
				if mesh!=trim:mesh.layers=0
			camera.position=center+normal*2.6+Vector3(0,.16,0);camera.look_at(center)
			mouth.hide();base.hide();await snap("front_end_isolated_diagnostic")
	FileAccess.open(out+"receipt.json",FileAccess.WRITE).store_string(JSON.stringify({"source_sha256":spec.source_sha256,"component_sha256":spec.component_sha256,"rows":rows,"scope":"Actual imported candidate: full assembly and same-camera visible/hidden new end cap comparison. Isolated view diagnostic only; not full art acceptance."},"  "));quit()
