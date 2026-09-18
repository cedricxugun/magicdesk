extends SceneTree
func _initialize()->void:run.call_deferred()
func run()->void:
    var folder:="res://../review/I_refinement/nautilus_r1/finish_r38/"
    var spec:Dictionary=JSON.parse_string(FileAccess.get_file_as_string(folder+"build.json"));var path:String="res://"+str(spec.component).trim_prefix("app/");assert(FileAccess.get_sha256(path)==spec.component_sha256)
    var source:PackedScene=load(path);var asset:Node3D=source.instantiate();var twin:Node3D=source.instantiate();root.add_child(asset);root.add_child(twin)
    var untouched:Array=[];var meshes:Dictionary={}
    for node in twin.find_children("*","MeshInstance3D",true,false):
        for i in range(node.mesh.get_surface_count()):
            var material:=node.get_active_material(i)as BaseMaterial3D
            untouched.append({"node":node,"surface":i,"material":material,"color":material.albedo_color,"roughness":material.roughness,"metallic":material.metallic})
    for node in asset.find_children("*","MeshInstance3D",true,false):meshes[str(node.name)]={"mesh":node.mesh,"transform":node.transform}
    var result:Dictionary=load("res://collection/i_finish_r38.gd").apply(asset,str(spec.finish_profile))
    var response=load("res://collection/i_chamber_music_response.gd").new();response.bind(asset,spec)
    assert(result.material_surface_counts.IN1_FoldedDiaphragm==12 and result.material_surface_counts.IN1_AcousticBronze==12)
    var brushed:=0
    for binding in response.bindings:
        for row in binding.materials:
            if row.material.get_shader_parameter("has_brushing")==true:brushed+=1
    assert(brushed==12)
    response.update(Vector3(.8,.6,.4),12.,true,1.,4.);response.update(Vector3.ZERO,12.,false,0.,4.)
    for binding in response.bindings:assert(binding.materials[0].material.get_shader_parameter("response")<.0001)
    response.release();response=null
    for row in untouched:
        assert(row.node.get_active_material(row.surface)==row.material)
        assert(row.material.albedo_color==row.color and row.material.roughness==row.roughness and row.material.metallic==row.metallic)
    for node in asset.find_children("*","MeshInstance3D",true,false):
        assert(node.mesh==meshes[str(node.name)].mesh and node.transform==meshes[str(node.name)].transform)
    result["passed"]=true;result["source_sha256"]=spec.source_sha256;result["component_sha256"]=spec.component_sha256;result["brushed_chamber_surfaces"]=brushed;result["shared_source_materials_preserved"]=true;result["mesh_and_transform_resources_preserved"]=true;result["scope"]="Isolated body finish overrides, twelve membrane/bronze groups, roughness transfer through music shader and stop/release, unchanged shared source material references and model resources. No final visual or native acceptance."
    FileAccess.open(folder+"qa.json",FileAccess.WRITE).store_string(JSON.stringify(result,"  "));untouched.clear();meshes.clear();asset.queue_free();twin.queue_free();source=null;await process_frame;print("I_FINISH_R38_QA true");quit()
