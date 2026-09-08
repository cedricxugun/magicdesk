extends SceneTree
func _initialize() -> void:
	root.size=Vector2i(32,32);root.position=Vector2i(-32000,-32000);root.unfocusable=true
	call_deferred("build")
func build() -> void:
	var raw:=FileAccess.get_file_as_bytes("H:/model/output/helios_incubator/tools/pressure_field.rgba")
	var images:Array[Image]=[]
	for z in range(128):images.append(Image.create_from_data(128,128,false,Image.FORMAT_RGBA8,raw.slice(z*128*128*4,(z+1)*128*128*4)))
	var texture:=ImageTexture3D.new()
	assert(texture.create(Image.FORMAT_RGBA8,128,128,128,false,images)==OK)
	await process_frame
	assert(ResourceSaver.save(texture,"res://assets/pressure_curl_field.res",ResourceSaver.FLAG_COMPRESS)==OK)
	print("PRESSURE_CURL_RESOURCE_READY");quit()
