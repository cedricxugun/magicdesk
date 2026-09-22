extends SceneTree
## Mesh-ray attribution in the same Godot projection as the R88 rear capture.
func _initialize()->void: run.call_deferred()
func run()->void:
    root.size=Vector2i(900,990)
    var world:=Node3D.new();root.add_child(world)
    var spec:Dictionary=JSON.parse_string(FileAccess.get_file_as_string("res://../review/I_refinement/nautilus_reset_r82/back_hardware_r88/built_r4/build.json"))
    var body:Node3D=load("res://"+str(spec.component).trim_prefix("app/")).instantiate();world.add_child(body)
    var driver=load("res://review/i_r82_body_driver.gd").new()
    assert(driver.bind(body,spec));driver.set_opening(1.)
    var mouth:Node3D=load("res://"+str(spec.core_component).trim_prefix("app/")).instantiate();world.add_child(mouth)
    var mp:Dictionary=spec.mouth_placement;var p:Array=mp.p;var q:Array=mp.q;var sc:Array=mp.s
    mouth.transform=Transform3D(Basis(Quaternion(q[0],q[1],q[2],q[3])).scaled(Vector3(sc[0],sc[1],sc[2])),Vector3(p[0],p[1],p[2]))
    var camera:=Camera3D.new();world.add_child(camera);camera.projection=Camera3D.PROJECTION_ORTHOGONAL;camera.size=4.1;camera.position=Vector3(4,3.65,-7);camera.look_at(Vector3(0,1.57,0));camera.current=true;camera.near=.03
    await process_frame
    var results:Array=[]
    for pixel in [Vector2(470,417),Vector2(474,425),Vector2(476,432),Vector2(464,405),Vector2(472,440),Vector2(390,440),Vector2(450,300)]:
        var origin:=camera.project_ray_origin(pixel);var direction:=camera.project_ray_normal(pixel);var hits:Array=[]
        for obj in world.find_children("*","MeshInstance3D",true,false):
            var instance:=obj as MeshInstance3D
            if instance.mesh==null:continue
            var inv:=instance.global_transform.affine_inverse();var ray_origin:=inv*origin;var ray_direction:Vector3=(inv.basis*direction).normalized()
            if instance.mesh.get_aabb().intersects_ray(ray_origin,ray_direction)==null:continue
            var nearest:=INF;var point:=Vector3.ZERO;var face_normal:=Vector3.ZERO;var normal_dot:=0.;var mat_name:="";var triangle:Array=[]
            for surface in range(instance.mesh.get_surface_count()):
                var arrays:Array=instance.mesh.surface_get_arrays(surface);var vertices:PackedVector3Array=arrays[Mesh.ARRAY_VERTEX];var indices:PackedInt32Array=arrays[Mesh.ARRAY_INDEX];var normals:PackedVector3Array=arrays[Mesh.ARRAY_NORMAL]
                for i in range(0,indices.size(),3):
                    var a:=vertices[indices[i]];var b:=vertices[indices[i+1]];var c:=vertices[indices[i+2]]
                    var hit:Variant=Geometry3D.ray_intersects_triangle(ray_origin,ray_direction,a,b,c)
                    if hit==null:continue
                    var wp:Vector3=instance.global_transform*hit;var distance:=origin.distance_to(wp)
                    if distance<nearest:
                        nearest=distance;point=wp;face_normal=instance.global_transform.basis*((b-a).cross(c-a).normalized())
                        normal_dot=(normals[indices[i]]+normals[indices[i+1]]+normals[indices[i+2]]).normalized().dot(ray_direction)
                        var material:=instance.mesh.surface_get_material(surface);mat_name=material.resource_name if material else ""
                        triangle=[a,b,c]
            if nearest<INF:hits.append({"mesh":instance.name,"distance":nearest,"world_point":point,"material":mat_name,"normal_dot_ray":normal_dot,"geometric_normal_dot_ray":face_normal.dot(direction),"local_triangle":triangle})
        hits.sort_custom(func(a,b):return a.distance<b.distance)
        if hits.size()>6:hits.resize(6)
        results.append({"pixel":pixel,"hits":hits});print("R89_PIXEL ",pixel," ",JSON.stringify(hits))
    var out:="res://../review/I_refinement/nautilus_reset_r82/chambers_r89/";DirAccess.make_dir_recursive_absolute(ProjectSettings.globalize_path(out))
    FileAccess.open(out+"rear_ray_probe.json",FileAccess.WRITE).store_string(JSON.stringify({"body_sha256":spec.component_sha256,"viewport":root.size,"rows":results,"scope":"Actual imported body at full opening and source-rest core, same rear camera. Triangle ray attribution; core shader deformations and separate live optics not included."},"  "))
    quit()
