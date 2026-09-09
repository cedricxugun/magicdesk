extends SceneTree
## Convert the exact Blender CSG result while retaining original shader slots.
func _initialize()->void:build.call_deferred()
func build()->void:
	var original:Node=load("res://assets/helios_model.glb").instantiate()
	var source:MeshInstance3D=original.find_child("BASE_FIXED_DisplayMesh",true,false)
	var config:Dictionary=JSON.parse_string(FileAccess.get_file_as_string("res://assets/collection/base_csg_source.json"))
	var report:={"source":"res://assets/helios_model.glb","source_node":source.name,"method":"Blender exact CSG; coordinates and original material slots retained","variants":{}}
	for kind in ["helios","shared"]:
		var definition:Dictionary=config.variants[kind]
		var scene:Node=load(definition.scene).instantiate()
		var node:MeshInstance3D=scene.find_child(definition.node,true,false)
		if node==null and scene is MeshInstance3D:node=scene
		var mesh:Mesh=node.mesh
		var slots:Array=[]
		for i in range(mesh.get_surface_count()):
			var mat_name:String=mesh.surface_get_material(i).resource_name
			var matched:=-1
			for index in range(source.mesh.get_surface_count()):
				if source.mesh.surface_get_material(index).resource_name==mat_name:matched=index;break
			assert(matched>=0,"Original base material slot missing: "+mat_name)
			slots.append(matched)
		var actual:=mesh.get_aabb();var baseline:=source.mesh.get_aabb()
		# The removed middle bezel protrudes beyond the cylinder. Controller
		# envelopes may differ; fixed diameter, height and rear anchor may not.
		var bound_error:float=absf(actual.size.x-baseline.size.x)+absf(actual.size.y-baseline.size.y)+absf(actual.position.y-baseline.position.y)+absf(actual.position.z-baseline.position.z)
		if bound_error>=.0001:
			push_error("Base outer frame drift: "+str(actual)+" source="+str(baseline));quit(2);return
		var path:String="res://assets/collection/base_"+str(kind)+".res"
		assert(ResourceSaver.save(mesh,path)==OK)
		report.variants[kind]={"path":path,"source_surfaces":slots,"bounds":str(mesh.get_aabb()),"external_bounds_error":bound_error}
		scene.free()
	FileAccess.open("res://assets/collection/base_frames.json",FileAccess.WRITE).store_string(JSON.stringify(report,"  "))
	original.free();print("SHARED_BASE_DERIVED ",JSON.stringify(report));quit()
