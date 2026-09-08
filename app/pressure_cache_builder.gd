extends SceneTree
var input_path:=""
var output_path:="res://assets/pressure_physics_preview"
func _initialize()->void:
	for arg in OS.get_cmdline_user_args():
		if arg.begins_with("--input="):input_path=arg.trim_prefix("--input=")
		if arg.begins_with("--output="):output_path=arg.trim_prefix("--output=")
	root.size=Vector2i(32,32);root.position=Vector2i(-32000,-32000);root.unfocusable=true
	call_deferred("build")
func build()->void:
	assert(not input_path.is_empty())
	var manifest=JSON.parse_string(FileAccess.get_file_as_string(input_path))
	var resolution=manifest.resolution;var nx:=int(resolution[0]);var ny:=int(resolution[1]);var nz:=int(resolution[2])
	DirAccess.make_dir_recursive_absolute(output_path)
	var frames:Array=[]
	for i in range(manifest.frames_raw.size()):
		var raw:=FileAccess.get_file_as_bytes(str(manifest.frames_raw[i]));assert(raw.size()==nx*ny*nz*2)
		var images:Array[Image]=[]
		for z in range(nz):images.append(Image.create_from_data(nx,ny,false,Image.FORMAT_RH,raw.slice(z*nx*ny*2,(z+1)*nx*ny*2)))
		var texture:=ImageTexture3D.new();assert(texture.create(Image.FORMAT_RH,nx,ny,nz,false,images)==OK)
		await process_frame
		var name:="frame_%03d.res"%i
		assert(ResourceSaver.save(texture,output_path.path_join(name),ResourceSaver.FLAG_COMPRESS)==OK)
		frames.append(name)
		print("PRESSURE_TEXTURE_SAVED ",i,"/",manifest.frames_raw.size())
	manifest.erase("frames_raw");manifest.frames=frames
	if manifest.has("occupancy_raw"):
		var r=manifest.occupancy_resolution;var x:=int(r[0]);var y:=int(r[1]);var z:=int(r[2])
		var bytes:=FileAccess.get_file_as_bytes(str(manifest.occupancy_raw));var images:Array[Image]=[]
		for layer in range(z):images.append(Image.create_from_data(x,y,false,Image.FORMAT_R8,bytes.slice(layer*x*y,(layer+1)*x*y)))
		var texture:=ImageTexture3D.new();assert(texture.create(Image.FORMAT_R8,x,y,z,false,images)==OK)
		await process_frame
		assert(ResourceSaver.save(texture,output_path.path_join("occupancy.res"),ResourceSaver.FLAG_COMPRESS)==OK)
		manifest.erase("occupancy_raw");manifest.occupancy="occupancy.res"
	FileAccess.open(output_path.path_join("manifest.json"),FileAccess.WRITE).store_string(JSON.stringify(manifest,"  "))
	print("PRESSURE_PHYSICAL_MANIFEST_READY ",output_path.path_join("manifest.json"));quit()
