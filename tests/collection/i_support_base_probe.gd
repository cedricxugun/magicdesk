extends SceneTree
func _initialize()->void:run.call_deferred()
func run()->void:
    set_meta("collection_no_save",true);set_meta("collection_no_audio",true);set_meta("collection_skip_intro",true)
    var scene:Node=load("res://main.tscn").instantiate();root.add_child(scene)
    for i in range(12):await process_frame
    var host:Node3D=scene.get_node("Render/HeliosDesktop");host.set_process(false);host.collection._legacy_set_visible(false);host.collection._set_base_frame("shared")
    var base:MeshInstance3D=host.collection.base_display;var faces:PackedVector3Array=base.mesh.get_faces()
    var component:Node3D=load("res://assets/collection/components/I_pneumatic_r2.glb").instantiate();host.add_child(component)
    var fixed:Node3D=component.find_child("IH1_FixedChamber",true,false)
    for i in range(faces.size()):faces[i]=base.to_global(faces[i])
    var rows:Array=[]
    for center in [Vector2.ZERO,Vector2(-.576,.30),Vector2(.576,.30)]:
        for dx in [-.10,-.05,0.,.05,.10]:
            for dz in [-.10,-.05,0.,.05,.10]:
                var local:=Vector3(center.x+dx,1.,center.y+dz);var point:Vector3=fixed.to_global(local);var height:=-100.
                for i in range(0,faces.size(),3):
                    var hit:Variant=Geometry3D.ray_intersects_triangle(point,Vector3.DOWN,faces[i],faces[i+1],faces[i+2])
                    if hit!=null:height=maxf(height,hit.y)
                rows.append({"x":local.x,"blender_y":-local.z,"world_x":point.x,"world_blender_y":-point.z,"height":height})
    var out:="res://../review/I_refinement/support_r3/";DirAccess.make_dir_recursive_absolute(out)
    var source_faces:Array=[]
    for p in faces:source_faces.append([p.x,-p.z,p.y])
    FileAccess.open(out+"actual_base_triangles.json",FileAccess.WRITE).store_string(JSON.stringify({"source_sha256":FileAccess.get_sha256(base.mesh.resource_path),"triangle_vertices":source_faces},""))
    var result:={"rows":rows,"base_mesh":base.mesh.resource_path,"base_sha256":FileAccess.get_sha256(base.mesh.resource_path),"scope":"Actual app shared-base mesh, 25 footprint samples per central/side pedestal; Godot Y-up converted to source Z-up. No legacy height assumption."}
    FileAccess.open(out+"base_probe.json",FileAccess.WRITE).store_string(JSON.stringify(result,"  "));print("I_ACTUAL_BASE_HEIGHTS ",rows.map(func(r):return r.height).min()," ",rows.map(func(r):return r.height).max())
    host=null;scene.queue_free();await process_frame;quit()
