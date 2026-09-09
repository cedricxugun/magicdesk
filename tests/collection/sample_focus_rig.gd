extends SceneTree
func _initialize()->void:run.call_deferred()
func run()->void:
	var host:=Node3D.new();root.add_child(host)
	var model:Node3D=load("res://collection/module.gd").new();host.add_child(model)
	model.setup(host,JSON.parse_string(FileAccess.get_file_as_string("res://assets/collection/models/L.json")),load("res://assets/collection/models/L.glb"))
	var frames:Array=[]
	for frame in range(600):
		if frame==30:model.activate(1)
		if frame==210:model.activate(4)
		if frame==260:model.activate(1)
		if frame==390:model.stow()
		model.tick(1.0/60.0,1.0)
		if frame%3!=0:continue
		var poses:Dictionary={}
		for item in model.parts+model.controls+model.motions:
			var t:Transform3D=item.node.global_transform
			poses[str(item.node.name)]={"p":[t.origin.x,t.origin.y,t.origin.z],"basis":[[t.basis.x.x,t.basis.x.y,t.basis.x.z],[t.basis.y.x,t.basis.y.y,t.basis.y.z],[t.basis.z.x,t.basis.z.y,t.basis.z.z]]}
		frames.append({"time":frame/60.0,"openness":model.openness,"poses":poses})
	FileAccess.open("res://../tests/collection/focus_rig_samples.json",FileAccess.WRITE).store_string(JSON.stringify(frames))
	print("FOCUS_RIG_SAMPLED ",frames.size());host.free();quit()
