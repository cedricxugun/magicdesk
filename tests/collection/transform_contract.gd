extends SceneTree
## Check pose reconstruction against imported glTF, including nonuniform scale.
func _initialize()->void:
	var report:Array=[]
	for id in ["B","F","G","I","J","K","L","M","N"]:
		var path:String="res://assets/helios_model.glb" if id=="B" else "res://assets/collection/models/"+str(id)+".glb"
		var data_path:String="res://assets/mechanism.json" if id=="B" else "res://assets/collection/models/"+str(id)+".json"
		var scene:Node=load(path).instantiate()
		var data:Dictionary=JSON.parse_string(FileAccess.get_file_as_string(data_path))
		var local_error:=0.0;var global_error:=0.0
		for c in data.controls:
			var node:Node3D=scene.find_child(c.name,true,false)
			var p:Dictionary=c.samples[0]
			var q:=Quaternion(p.q[0],p.q[1],p.q[2],p.q[3]);var scale:=Vector3(p.s[0],p.s[1],p.s[2])
			var local:=Basis(q)*Basis.from_scale(scale);var global:=Basis(q).scaled(scale)
			for i in range(3):local_error=maxf(local_error,(local[i]-node.basis[i]).length());global_error=maxf(global_error,(global[i]-node.basis[i]).length())
		report.append({"model":id,"local_scale_error":local_error,"global_scale_error":global_error})
		scene.free()
	FileAccess.open("res://../tests/collection/transform_contract.json",FileAccess.WRITE).store_string(JSON.stringify(report,"  "))
	print(JSON.stringify(report));quit(0 if report.all(func(x):return x.local_scale_error<.0001) else 2)
