extends SceneTree
var out:="res://../review/I_refinement/nautilus_r1/seam_fasteners_r64/oriented_r2/views_r3/"
var camera:Camera3D
func _initialize()->void:run.call_deferred()
func _process(delta:float)->bool:RenderingServer.force_draw(false,delta);return false
func snap(name:String)->void:
	for i in range(6):await RenderingServer.frame_post_draw
	root.get_texture().get_image().save_png(out+name+".png")
	print("FASTENER_VIEW ",name)
func run()->void:
	RenderingServer.set_render_loop_enabled(false);DirAccess.make_dir_recursive_absolute(out)
	root.size=Vector2i(1100,900);root.transparent_bg=false;root.msaa_3d=Viewport.MSAA_4X
	var spec:Dictionary=JSON.parse_string(FileAccess.get_file_as_string("res://../review/I_refinement/nautilus_r1/seam_fasteners_r64/oriented_r2/build.json"))
	var world:=Node3D.new();root.add_child(world)
	var env:=Environment.new();env.background_mode=Environment.BG_COLOR;env.background_color=Color(.025,.027,.030);env.tonemap_mode=Environment.TONE_MAPPER_AGX
	var panorama:=PanoramaSkyMaterial.new();panorama.panorama=load("res://assets/studio_small_09_4k.exr");panorama.energy_multiplier=.35
	env.sky=Sky.new();env.sky.sky_material=panorama;env.ambient_light_source=Environment.AMBIENT_SOURCE_SKY;env.ambient_light_energy=.4;env.reflected_light_source=Environment.REFLECTION_SOURCE_SKY
	var environment:=WorldEnvironment.new();environment.environment=env;world.add_child(environment)
	var body:Node3D=load("res://"+str(spec.component).trim_prefix("app/")).instantiate();world.add_child(body)
	var mount:Node3D=body.find_child("IC1_MouthMount",true,false)
	var pin:MeshInstance3D=body.find_child("IC1_SeamCrossBolt_-1",true,false);var cap:MeshInstance3D=body.find_child("IC64_SeamSocket_-1",true,false)
	var isolated:=Node3D.new();world.add_child(isolated);isolated.global_transform=mount.global_transform
	var selected:Array[Node3D]=[pin,cap]
	for mesh in body.find_children("IC1_SeamWasher_-1_*","MeshInstance3D",true,false):selected.append(mesh)
	for mesh in selected:mesh.reparent(isolated,true)
	body.queue_free();await process_frame;body=isolated;mount=isolated
	var axis:=Vector3(0,0,-1);var center:=Vector3(-.601,.590,0.);var cap_home:Transform3D=cap.transform;var pin_home:Transform3D=pin.transform
	var location:Vector3=mount.to_global(center);var up:Vector3=(mount.global_basis*axis).normalized();var right:Vector3=mount.global_basis.x.normalized();var front:Vector3=mount.global_basis.y.normalized()
	for row in [[right*.35+front*.25+up*.15,7.],[right*-.2+front*.2-up*.2,4.]]:
		var light:=AreaLight3D.new();world.add_child(light);light.position=location+row[0];light.look_at(location,up);light.light_energy=row[1];light.area_size=Vector2(.15,.25);light.area_normalize_energy=true;light.area_range=2.
	camera=Camera3D.new();world.add_child(camera);camera.near=.001;camera.fov=34.;camera.current=true
	camera.position=location+right*.15+front*.2-up*.2;camera.look_at(location,front);await snap("pair_seated")
	var dy:=-.014;var angle:float=-TAU*dy/.001;var basis:=Basis(axis,angle)
	cap.transform=Transform3D(basis,center+axis*dy-basis*center)*cap_home
	await snap("retainer_unscrewed")
	pin.position=pin_home.origin+axis*.15
	camera.position=location+up*.045+right*.25+front*.3-up*.2;camera.look_at(location+up*.035,front);await snap("stud_withdrawn")
	pin.hide()
	for mesh in body.find_children("IC1_SeamWasher_-1_*","MeshInstance3D",true,false):mesh.hide()
	var focus:Vector3=cap.to_global(cap.get_aabb().get_center())
	camera.position=focus+up*.040+right*.020+front*.01;camera.look_at(focus,front);await snap("female_thread_inside")
	camera.position=focus-up*.040+right*.020+front*.01;camera.look_at(focus,front);await snap("hex_socket_outside")
	FileAccess.open(out+"receipt.json",FileAccess.WRITE).store_string(JSON.stringify({"source_sha256":spec.source_sha256,"component_sha256":spec.component_sha256,"scope":"Actual imported isolated fastener pair, helical retainer displacement and stud removal. Diagnostic material/geometry views, not whole App, clamp release or final art acceptance."},"  "))
	for light in world.find_children("*","AreaLight3D",true,false):light.queue_free()
	for i in range(3):await RenderingServer.frame_post_draw
	world.queue_free();await process_frame;quit()
