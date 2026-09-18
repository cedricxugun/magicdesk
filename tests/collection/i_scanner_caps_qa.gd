extends SceneTree
func _initialize()->void:run.call_deferred()
func run()->void:
    var folder:="res://../review/I_refinement/nautilus_r1/scan_caps_runtime_r43/readable/"
    var spec:Dictionary=JSON.parse_string(FileAccess.get_file_as_string("res://../review/I_refinement/part_a_mouth/shutter_r2/collar_clamps/build.json"))
    var asset:Node3D=load("res://"+str(spec.component).trim_prefix("app/")).instantiate();root.add_child(asset)
    var red_originals:Array=[]
    for i in range(3):
        var tip:=asset.find_child("IAM_TineRoundedAxial_"+str(i),true,false)as MeshInstance3D
        red_originals.append({"node":tip,"override":tip.get_surface_override_material(0),"mesh":tip.mesh,"transform":tip.transform})
    var checked:=0;var maximum_error:=0.
    for cycle in range(3):
        var staff=load("res://collection/i_moonlight_staff.gd").new();root.add_child(staff)
        staff.setup(asset,str(spec.component_sha256),"res://assets/collection/art/I/scan_caps_r41/score_layout_readable.json")
        assert(staff.scanner_caps.size()==3 and staff.cap_status.attached==3)
        assert(staff.material.get_shader_parameter("optical_backing")==0.)
        for attempt in range(120):
            staff.set_score_position(1,32.,1.);await process_frame
            if staff.status.ready:break
        assert(staff.status.ready)
        var motion:=asset.find_child("IAM_DiaphragmMotion",true,false)as Node3D;var rest:=motion.position
        for displacement in [-.006,0.,.006,0.]:
            asset.rotation=Vector3(.12,-.25,.08)*float(cycle);asset.scale=Vector3.ONE*(1.-float(cycle)*.15)
            motion.position=rest+Vector3(0,displacement,0);staff.set_music_response(.5,true)
            for i in range(3):
                var binding:Dictionary=staff.scan_tips[i];var cap:Node3D=staff.scanner_caps[i]
                assert(cap.get_parent()==binding.node and binding.finish_node!=binding.node)
                var expected:Vector3=binding.node.to_global(binding.local_point);var nearest:=INF
                var lens:MeshInstance3D=binding.finish_node
                for surface in range(lens.mesh.get_surface_count()):
                    var vertices:PackedVector3Array=lens.mesh.surface_get_arrays(surface)[Mesh.ARRAY_VERTEX]
                    for v in vertices:nearest=minf(nearest,(lens.global_transform*v).distance_to(expected))
                assert(nearest<.000001,"Light endpoint has no actual lens surface point");maximum_error=maxf(maximum_error,nearest);checked+=1
                var ray:MeshInstance3D=staff.optics.find_child(str(staff.layout.scanner.tips[i].ray),true,false)
                var a:Array=ray.mesh.surface_get_arrays(0);var center:=Vector3.ZERO;var count:=0
                for j in range(a[Mesh.ARRAY_VERTEX].size()):
                    if a[Mesh.ARRAY_TEX_UV][j].y>.999:center+=ray.transform*a[Mesh.ARRAY_VERTEX][j];count+=1
                assert(count==2);center/=count
                var delta:Vector3=staff.scan_materials[i+1].get_shader_parameter("tip_delta")
                assert(staff.mouth.to_global(center+delta).distance_to(expected)<.000001,"Ray detached from lens")
        motion.position=rest;staff.set_score_position(1,32.,0.);staff.set_music_response(0.,false,false)
        for tip in staff.scan_tips:assert(tip.finish.emission_energy_multiplier==0.)
        var cap_refs:Array=staff.scanner_caps.duplicate();staff.queue_free();await process_frame;await process_frame
        for cap in cap_refs:assert(not is_instance_valid(cap),"Accessory leaked after reader removal")
        for row in red_originals:
            assert(row.node.get_surface_override_material(0)==row.override and row.node.mesh==row.mesh)
            var before:Transform3D=row.transform;var after:Transform3D=row.node.transform
            for vectors in [[before.basis.x,after.basis.x],[before.basis.y,after.basis.y],[before.basis.z,after.basis.z],[before.origin,after.origin]]:
                for component in range(3):assert(float(vectors[0][component])==float(vectors[1][component]))
    FileAccess.open(folder+"caps_qa.json",FileAccess.WRITE).store_string(JSON.stringify({"passed":true,"attachment_cycles":3,"actual_lens_surface_endpoint_checks":checked,"maximum_endpoint_error":maximum_error,"transparent_score":true,"red_meshes_materials_local_transforms_preserved":true,"accessories_released":true,"scope":"Actual imported cap lens vertices and shader-deformed ray origins under mouth rotation/scale and diaphragm displacement; three installation/removal cycles, original red tips unchanged, off-state emission zero. Not full collision/clearance, complete music playback or visual/native acceptance."},"  "))
    red_originals.clear();asset.queue_free();await process_frame;print("I_SCANNER_CAPS_QA true endpoints=",checked);quit()
