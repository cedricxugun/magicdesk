extends SceneTree
## Source-bound R76 pose review. Standalone evidence, never a product control UI.
var out:="res://../review/I_refinement/nautilus_r1/coupling_repair_r76/views/"
var world:Node3D
var body:Node3D
var mouth:Node3D
var camera:Camera3D
var nodes:Dictionary={}
var homes:Dictionary={}
var spec:Dictionary
var route:Dictionary
var axis:Vector3
var axis_scale:float
var mount:Node3D
var groups:Array=[]

func _initialize()->void:run.call_deferred()
func _process(delta:float)->bool:RenderingServer.force_draw(false,delta);return false
func cv(a:Array)->Vector3:return Vector3(a[0],a[2],-a[1])
func read(path:String)->Dictionary:return JSON.parse_string(FileAccess.get_file_as_string(path))
func run()->void:
	RenderingServer.set_render_loop_enabled(false)
	out=ProjectSettings.globalize_path(out).simplify_path()+"/"
	if OS.get_cmdline_user_args().has("--installed"):out=out.path_join("../installed").simplify_path()+"/"
	if DirAccess.make_dir_recursive_absolute(out)!=OK:quit(2);return
	root.size=Vector2i(1600,1200);root.transparent_bg=false;root.msaa_3d=Viewport.MSAA_4X
	spec=read("res://../review/I_refinement/nautilus_r1/coupling_repair_r76/build.json")
	route=read("res://../review/I_refinement/nautilus_r1/coupling_repair_r76/release/probe.json")
	assert(spec.source_sha256==route.source_sha256)
	assert(FileAccess.get_sha256("res://../"+spec.component)==spec.component_sha256)
	world=Node3D.new();root.add_child(world)
	var env:=Environment.new();env.background_mode=Environment.BG_COLOR;env.background_color=Color(.035,.041,.049);env.tonemap_mode=Environment.TONE_MAPPER_AGX
	var panorama:=PanoramaSkyMaterial.new();panorama.panorama=load("res://assets/studio_small_09_4k.exr");panorama.energy_multiplier=.3
	env.sky=Sky.new();env.sky.sky_material=panorama;env.ambient_light_source=Environment.AMBIENT_SOURCE_SKY;env.ambient_light_energy=.42;env.reflected_light_source=Environment.REFLECTION_SOURCE_SKY
	var environment:=WorldEnvironment.new();environment.environment=env;world.add_child(environment)
	for row in [[Vector3(3.2,5.2,4),20.,Vector2(2.,3.)],[Vector3(-3.,4,-3),16.,Vector2(2.,3.)],[Vector3(4.,2.5,-5.),8.,Vector2(2.,3.)]]:
		var light:=AreaLight3D.new();world.add_child(light);light.position=row[0];light.look_at(Vector3(0,2.,0));light.light_energy=row[1];light.area_size=row[2];light.area_normalize_energy=true;light.area_range=18.;light.shadow_enabled=true;light.shadow_normal_bias=.10;light.shadow_bias=.10
	body=load("res://"+str(spec.component).trim_prefix("app/")).instantiate();world.add_child(body)
	load("res://collection/i_finish_r38.gd").apply(body,str(spec.finish_profile))
	var opening:RefCounted=load("res://collection/i_nautilus_form_driver.gd").new();opening.bind(body,spec);opening.set_opening(1.)
	mouth=load("res://"+str(spec.mouth_component).trim_prefix("app/")).instantiate();world.add_child(mouth)
	var p:Array=spec.mouth_placement.p;var q:Array=spec.mouth_placement.q;var scales:Array=spec.mouth_placement.s
	mouth.transform=Transform3D(Basis(Quaternion(q[0],q[1],q[2],q[3])).scaled(Vector3(scales[0],scales[1],scales[2])),Vector3(p[0],p[1],p[2]))
	var donor:Node3D=load("res://assets/helios_model.glb").instantiate();world.add_child(donor)
	var base:Node3D=donor.find_child("BASE_FIXED",true,false);base.reparent(world,true);donor.queue_free()
	camera=Camera3D.new();world.add_child(camera);camera.position=Vector3(-1.4,3.9,6.8);camera.look_at(Vector3(-.15,1.85,0));camera.fov=37.;camera.far=30.;camera.current=true
	if OS.get_cmdline_user_args().has("--installed"):
		opening.set_opening(0.);await capture("01_installed_closed")
		opening.set_opening(1.);await capture("02_installed_open")
		camera.position=Vector3(2.2,1.65,3.4);camera.look_at(Vector3(0,1.05,0));camera.fov=29.;await capture("03_support_front")
		camera.position=Vector3(-2.2,1.65,-3.4);camera.look_at(Vector3(0,1.05,0));await capture("04_support_rear")
		for light in world.find_children("*","AreaLight3D",true,false):light.queue_free()
		for i in range(3):await RenderingServer.frame_post_draw
		world.queue_free();await process_frame;quit();return
	if not prepare():quit(2);return
	if OS.get_cmdline_user_args().has("--motion"):
		await motion_review();return
	var cameras:Array=[]
	for row in [["01_prepared",0.,0.],["02_unlocked",1.,0.],["03_withdrawn",1.,1.]]:
		pose(row[1],row[2]);await capture(str(row[0]))
		cameras.append({"image":row[0],"position":[camera.position.x,camera.position.y,camera.position.z],"fov":camera.fov})
	# Macro evidence uses its own small scene, avoiding an extreme-frustum
	# transition while the full assembly is paired with area shadow lights.
	pose(0.,0.)
	FileAccess.open(out+"receipt.json",FileAccess.WRITE).store_string(JSON.stringify({"source_sha256":spec.source_sha256,"component_sha256":spec.component_sha256,"cameras":cameras,"scope":"Actual saved source, three prepared service poses. Macro is a separate isolated scene. No full service/native/art acceptance."},"  "))
	for light in world.find_children("*","AreaLight3D",true,false):light.queue_free()
	for i in range(3):await RenderingServer.frame_post_draw
	world.queue_free();await process_frame;quit()

func prepare()->bool:
	var support:=read("res://../review/I_refinement/nautilus_r1/port_edge_r68/release_probe/probe.json")
	var front:=read("res://../review/I_refinement/nautilus_r1/service_r63/stage03_wide/plan.json")
	var rear:=read("res://../review/I_refinement/nautilus_r1/rear03_release_r70/two_stage_r5/probe.json")
	assert(support.source_sha256==spec.seam_fasteners.parent_source_sha256 and rear.source_sha256==support.source_sha256)
	var meshes:Array=body.find_children("*","MeshInstance3D",true,false);meshes.append_array(mouth.find_children("*","MeshInstance3D",true,false))
	meshes.sort_custom(func(a,b):return a.get_path().get_name_count()<b.get_path().get_name_count())
	var offsets:Dictionary={};var before:Dictionary={}
	for mesh in meshes:
		var name:=str(mesh.name);assert(not nodes.has(name));nodes[name]=mesh;before[name]=mesh.global_transform
		offsets[name]=Vector3.ZERO if name in support.fixed_adapter_names else Vector3.UP*.45
	for g in support.groups+support.legs+support.ports:
		for name in g.names:offsets[name]+=cv(g.offset)
	for g in front.groups:
		if g.id in ["cover_03","pin_cap_03","pin_03"]:
			for name in g.meshes:offsets[name]+=cv(g.offset_blender)
	for g in rear.groups:
		var delta:Vector3=cv(rear.shell_waypoints[2]) if g.id=="rear_shell03" else cv(g.normal)*(.810 if str(g.id).begins_with("rear_bolt") else .8)
		for name in g.names:offsets[name]+=delta
	for mesh in meshes:
		var tr:Transform3D=before[str(mesh.name)];tr.origin+=offsets[str(mesh.name)];mesh.global_transform=tr
	for mesh in meshes:homes[str(mesh.name)]=mesh.global_transform
	mount=body.find_child("IC1_MouthMount",true,false);assert(mount!=null)
	# Blender +Z maps to Godot +Y in the imported local installation frame.
	axis=mount.global_basis.y.normalized();axis_scale=mount.global_basis.y.length()
	for row in spec.coupling_threads.threads:
		groups.append({"row":row,"center":mount.global_transform*cv(row.center_parent)+Vector3.UP*.45})
	for name in route.assembly_members+route.bolt_members:
		if not nodes.has(name):
			var validated:String=str(name).validate_node_name()
			if nodes.has(validated):nodes[name]=nodes[validated];homes[name]=homes[validated]
			else:
				print("MISSING_SOURCE_NODE ",name," validated=",validated," candidates=",nodes.keys().filter(func(n):return str(n).begins_with(str(name).get_slice(".",0))))
				return false
	return true

func pose(loosen:float,extract:float)->void:
	var distance:=.006*loosen
	var desired:Dictionary={}
	for name in route.assembly_members:
		var tr:Transform3D=homes[name];tr.origin-=axis*.8*extract;desired[name]=tr
	for g in groups:
		var row:Dictionary=g.row;var center:Vector3=g.center
		var spin:=Basis(Quaternion(axis,TAU*(distance/axis_scale)/float(row.pitch_parent)))
		var tr:Transform3D=homes[row.bolt];tr.origin=center+spin*(tr.origin-center)+axis*distance;tr.basis=spin*tr.basis;desired[row.bolt]=tr
		var washer:String=str(row.bolt)+"_Washer";tr=homes[washer];tr.origin+=axis*distance;desired[washer]=tr
	var names:Array=desired.keys();names.sort_custom(func(a,b):return nodes[a].get_path().get_name_count()<nodes[b].get_path().get_name_count())
	for name in names:nodes[name].global_transform=desired[name]

func capture(name:String)->void:
	for i in range(5):await RenderingServer.frame_post_draw
	var result:=root.get_texture().get_image().save_png(out+name+".png")
	if result!=OK:quit(3);return
	print("R76_VIEW ",name)

func motion_review()->void:
	var manifest:=read("res://assets/collection/art/I/coupling_r76/coupling_motion.json")
	var driver:RefCounted=load("res://review/i_coupling_driver.gd").new()
	if not driver.bind(body,nodes,spec,manifest):push_error("R76 motion binding failed");quit(4);return
	var max_error:=0.;var point_count:=0
	for witness in manifest.source_witnesses:
		driver.seek(float(witness.time))
		for name in witness.points:
			for i in range(manifest.local_points.size()):
				var p:Array=manifest.local_points[i];var expected:Array=witness.points[name][i]
				var actual:Vector3=body.to_local(nodes[name].to_global(Vector3(p[0],p[1],p[2])))
				max_error=maxf(max_error,actual.distance_to(Vector3(expected[0],expected[1],expected[2])));point_count+=1
	if max_error>.00001:push_error("R76 source witness mismatch: "+str(max_error));quit(5);return
	# Re-run imported source points with an independently rotated display root.
	var old_body:Transform3D=body.transform;var old_mouth:Transform3D=mouth.transform
	var display:=Transform3D(Basis(Vector3.UP,.43),Vector3(.15,0.,-.12))
	body.transform=display*old_body;mouth.transform=display*old_mouth
	for witness in manifest.source_witnesses:
		driver.seek(float(witness.time))
		for name in witness.points:
			var e:Array=witness.points[name][0];var actual:Vector3=body.to_local(nodes[name].global_position)
			max_error=maxf(max_error,actual.distance_to(Vector3(e[0],e[1],e[2])));point_count+=1
	body.transform=old_body;mouth.transform=old_mouth;driver.seek(0.)
	if max_error>.00001:push_error("R76 display rotation mismatch: "+str(max_error));quit(6);return
	var movie_out:=out.get_base_dir().path_join("../motion_review").simplify_path()+"/"
	DirAccess.make_dir_recursive_absolute(movie_out+"frames")
	var samples:Array=[];var render:=not OS.get_cmdline_user_args().has("--qa-only")
	# Whole forward/return plus a mid-extraction reversal and safe retraction.
	for frame in range(1080):
		if frame==30 or frame==600:driver.request(true)
		if frame==330 or frame==750:driver.request(false)
		driver.tick(1./30.)
		if render:
			await RenderingServer.frame_post_draw
			if root.get_texture().get_image().save_png(movie_out+"frames/%04d.png"%frame)!=OK:quit(7);return
		if frame%30==0:samples.append({"frame":frame,"time":driver.time,"velocity":driver.velocity,"target":driver.target})
		if frame%150==0:print("R76_MOTION_FRAME ",frame)
	if not driver.stowed():push_error("R76 motion did not return");quit(8);return
	var pose_error:=0.
	for name in route.assembly_members+route.bolt_members:
		var tr:Transform3D=nodes[name].global_transform;var home:Transform3D=homes[name]
		pose_error=maxf(pose_error,tr.origin.distance_to(home.origin))
		for i in range(3):pose_error=maxf(pose_error,tr.basis[i].distance_to(home.basis[i]))
	if pose_error>.00001:quit(9);return
	var originals:Array=[]
	for item in driver.ordered:originals.append({"node":item.node,"transform":item.original})
	driver.release();driver=null
	var release_exact:=true
	for item in originals:release_exact=release_exact and item.node.transform==item.transform
	if not release_exact:push_error("R76 release did not restore exact local transforms");quit(10);return
	FileAccess.open(movie_out+("report.json" if render else "qa_report.json"),FileAccess.WRITE).store_string(JSON.stringify({"passed":true,"frames":1080 if render else 0,"fps":30,"release_restores_exact_local_transforms":release_exact,
		"source_points_checked":point_count,"source_max_error":max_error,"return_pose_error":pose_error,"samples":samples,
		"body_source_sha256":spec.source_sha256,"motion_source_sha256":manifest.motion_source_sha256,
		"scope":"Blender-authored 13-group clip, source points including display rotation, full round trip and interrupted second extraction. Review renderer only, not prior-stage playback or native product controls."},"  "))
	for light in world.find_children("*","AreaLight3D",true,false):light.queue_free()
	for i in range(3):await RenderingServer.frame_post_draw
	world.queue_free();await process_frame;quit()
