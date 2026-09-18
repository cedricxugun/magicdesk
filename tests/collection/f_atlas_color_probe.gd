extends SceneTree
func _initialize()->void:run.call_deferred()
func run()->void:
	root.size=Vector2i(256,256);var viewport:=SubViewport.new();viewport.size=Vector2i(256,256);viewport.own_world_3d=true;viewport.render_target_update_mode=SubViewport.UPDATE_ALWAYS;root.add_child(viewport)
	var world:=WorldEnvironment.new();var env:=Environment.new();env.background_mode=Environment.BG_COLOR;env.background_color=Color.BLACK;env.tonemap_mode=Environment.TONE_MAPPER_AGX;env.tonemap_exposure=1.;world.environment=env;viewport.add_child(world)
	var camera:=Camera3D.new();camera.projection=Camera3D.PROJECTION_ORTHOGONAL;camera.size=1.1;camera.position=Vector3(0,0,2);viewport.add_child(camera)
	var image:=Image.create(4,4,false,Image.FORMAT_RGBA8);image.fill(Color(.5,.25,.1,1));image.save_png("res://../review/F_complete/revision_20260911/optical_probe/constant.png")
	var mesh:=MeshInstance3D.new();var quad:=QuadMesh.new();quad.size=Vector2.ONE;mesh.mesh=quad;viewport.add_child(mesh)
	var mat:=ShaderMaterial.new();mat.shader=load("res://collection/f_atlas.gdshader");mat.set_shader_parameter("atlas",ImageTexture.create_from_image(image));mat.set_shader_parameter("tile",0.);mesh.material_override=mat
	var samples:Array=[]
	for gain in [.1,.3,.5,1.0]:
		mat.set_shader_parameter("gain",gain)
		for i in range(5):await RenderingServer.frame_post_draw
		var output:=viewport.get_texture().get_image();output.save_png("res://../review/F_complete/revision_20260911/optical_probe/godot_%02d.png"%roundi(gain*10))
		var c:=output.get_pixel(128,128);samples.append({"gain":gain,"pixel":[c.r,c.g,c.b,c.a]})
	var source:String=FileAccess.get_file_as_string("res://collection/f_atlas.gdshader")
	for pair in [["zero",0.],["extreme",6000.]]:
		var shader:=Shader.new();shader.code=source.replace("amount*6.0","amount*"+str(pair[1]))
		mat.shader=shader;mat.set_shader_parameter("atlas",ImageTexture.create_from_image(image));mat.set_shader_parameter("gain",.5)
		for i in range(5):await RenderingServer.frame_post_draw
		var c:=viewport.get_texture().get_image().get_pixel(128,128);samples.append({"variant":pair[0],"gain":.5,"pixel":[c.r,c.g,c.b,c.a]})
	FileAccess.open("res://../review/F_complete/revision_20260911/optical_probe/godot.json",FileAccess.WRITE).store_string(JSON.stringify(samples,"  "));viewport.queue_free();await process_frame;quit()
