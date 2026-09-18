extends SceneTree
var out:="res://../review/I_refinement/nautilus_r1/desktop_optics_r60/sampling/"
func _initialize()->void:run.call_deferred()
func _process(delta:float)->bool:RenderingServer.force_draw(false,delta);return false
func run()->void:
	RenderingServer.set_render_loop_enabled(false);DirAccess.make_dir_recursive_absolute(out)
	root.size=Vector2i(192,128);root.transparent_bg=true;root.msaa_3d=Viewport.MSAA_2X
	var world:=Node3D.new();root.add_child(world)
	var camera:=Camera3D.new();world.add_child(camera);camera.projection=Camera3D.PROJECTION_ORTHOGONAL;camera.size=.96;camera.position=Vector3(0,0,2);camera.current=true
	var sheet:=MeshInstance3D.new();world.add_child(sheet);var quad:=QuadMesh.new();quad.size=Vector2(1.2,.72);sheet.mesh=quad
	var mat:=ShaderMaterial.new();mat.shader=load("res://collection/i_moonlight_staff.gdshader");sheet.material_override=mat
	var width:=167.*1.2/.72
	mat.set_shader_parameter("window_width",width);mat.set_shader_parameter("tile_width",512.);mat.set_shader_parameter("reveal",1.);mat.set_shader_parameter("optical_backing",0.);mat.set_shader_parameter("correct_alpha",true)
	for i in range(3):mat.set_shader_parameter("page_"+str(i),load("res://assets/collection/art/I/moonlight_candidate/score/m1.0/%03d.png"%i))
	var samples:Array=[]
	for index in range(7):
		var shift:float=[-4.,-1.,-.25,0.,.25,1.,4.][index]
		mat.set_shader_parameter("offset_in_tile",512.-width*.5+shift)
		for variant in ["implicit","gradients","coverage"]:
			mat.set_shader_parameter("tile_gradients",variant!="implicit");mat.set_shader_parameter("ink_coverage_gain",1.35 if variant=="coverage" else 1.)
			for f in range(3):await RenderingServer.frame_post_draw
			root.get_texture().get_image().save_png(out+"%02d_%s.png"%[index,variant])
		samples.append({"index":index,"shift_source_units":shift})
	FileAccess.open(out+"manifest.json",FileAccess.WRITE).store_string(JSON.stringify({"size":[192,128],"samples":samples,"scope":"Isolated actual staff shader and original score tiles at desktop-like pixel footprint, explicit gradients isolated from ink coverage. Orthographic diagnostic only."},"  "))
	quit()
