extends SceneTree
func _initialize()->void:run.call_deferred()
func run()->void:
    var report_path:="res://../review/I_refinement/part_a_mouth/shutter_r2/diaphragm/build.json"
    var output_path:="res://../review/I_refinement/part_a_mouth/shutter_r2/foil_frame/attributes_qa.json"
    for argument in OS.get_cmdline_user_args():
        if argument.begins_with("--report="):
            report_path=argument.trim_prefix("--report=");output_path=report_path.get_base_dir()+"/attributes_qa.json"
    var spec:Dictionary=JSON.parse_string(FileAccess.get_file_as_string(report_path))
    var asset:Node3D=load("res://"+str(spec.component).trim_prefix("app/")).instantiate();root.add_child(asset)
    var before:Dictionary={}
    for group in spec.tongues:
        for name in group.mesh_names:before[name]=asset.find_child(name,true,false).mesh.surface_get_arrays(0)
    var driver=load("res://collection/i_tongue_set_driver.gd").new();driver.bind(asset,spec)
    var checks:Array=[]
    for group in spec.tongues:
        for name in group.mesh_names:
            var node:=asset.find_child(name,true,false) as MeshInstance3D
            if node.mesh.get_surface_count()!=1:push_error("Missing foil surface");quit(1);return
            var a:Array=node.mesh.surface_get_arrays(0)
            # The old runtime also rebuilds ArrayMesh to discard invalid REST LOD.
            # Compare against that identical repack to isolate custom-frame changes.
            var control:=ArrayMesh.new();control.add_surface_from_arrays(Mesh.PRIMITIVE_TRIANGLES,before[name],[],{},0)
            var repacked:Array=control.surface_get_arrays(0);var source_drift:Dictionary={}
            for channel in [Mesh.ARRAY_VERTEX,Mesh.ARRAY_INDEX,Mesh.ARRAY_NORMAL,Mesh.ARRAY_TANGENT,Mesh.ARRAY_TEX_UV,Mesh.ARRAY_TEX_UV2]:
                if a[channel].to_byte_array()!=repacked[channel].to_byte_array():push_error("Adding custom frames changed runtime attributes: "+name+" channel "+str(channel));quit(1);return
                var maximum:=0.
                if a[channel].to_byte_array()!=before[name][channel].to_byte_array():
                    for i in range(a[channel].size()):
                        var v=a[channel][i];var old=before[name][channel][i]
                        maximum=maxf(maximum,v.distance_to(old) if v is Vector3 or v is Vector2 else absf(float(v)-float(old)))
                source_drift[str(channel)]=maximum
                if channel in [Mesh.ARRAY_VERTEX,Mesh.ARRAY_INDEX,Mesh.ARRAY_TEX_UV,Mesh.ARRAY_TEX_UV2] and maximum!=0.:
                    push_error("Geometry or UV changed");quit(1);return
            var rt:PackedFloat32Array=a[Mesh.ARRAY_CUSTOM0];var rn:PackedFloat32Array=a[Mesh.ARRAY_CUSTOM1]
            var count:int=a[Mesh.ARRAY_VERTEX].size();assert(rt.size()==count*4 and rn.size()==count*3)
            var max_dot:=0.;var length_error:=0.
            for i in range(count):
                var t:=Vector3(rt[i*4],rt[i*4+1],rt[i*4+2]);var n:=Vector3(rn[i*3],rn[i*3+1],rn[i*3+2])
                assert(t.is_finite() and n.is_finite() and absf(rt[i*4+3])==1.)
                max_dot=maxf(max_dot,absf(t.dot(n)));length_error=maxf(length_error,maxf(absf(t.length()-1.),absf(n.length()-1.)))
            assert(max_dot<.00001 and length_error<.00001 and node.mesh.shadow_mesh==null)
            checks.append({"mesh":name,"vertices":count,"indices":a[Mesh.ARRAY_INDEX].size(),"matches_previous_runtime_repack_exactly":true,"source_positions_indices_uv_exact":true,"inherent_source_to_runtime_repack_drift_by_channel":source_drift,"rest_frame_max_dot":max_dot,"rest_frame_max_length_error":length_error})
    FileAccess.open(output_path,FileAccess.WRITE).store_string(JSON.stringify({"passed":true,"component_sha256":spec.component_sha256,"source_sha256":spec.source_sha256,"binder_sha256":FileAccess.get_sha256("res://collection/i_tongue_fields.gd"),"meshes":checks,"scope":"Actual ArrayMesh source-attribute preservation and populated finite rest-frame custom attributes on six foil skins. No moving geometry or art acceptance inferred from this check."},"  "))
    print("I_FOIL_REFERENCE_FRAME_QA true");asset.queue_free();await process_frame;quit()
