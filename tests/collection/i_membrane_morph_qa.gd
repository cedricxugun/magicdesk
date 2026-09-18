extends SceneTree
func _initialize()->void:run.call_deferred()
func vector(p:Array)->Vector3:return Vector3(p[0],p[1],p[2])
func run()->void:
    var folder:="res://../review/I_refinement/nautilus_r1/chamber_motion_r36/"
    var spec:Dictionary=JSON.parse_string(FileAccess.get_file_as_string(folder+"build.json"));var ref:Dictionary=JSON.parse_string(FileAccess.get_file_as_string(folder+"morph_witnesses.json"));assert(ref.source_sha256==spec.source_sha256 and ref.component_sha256==spec.component_sha256)
    var path:String="res://"+str(spec.component).trim_prefix("app/");assert(FileAccess.get_sha256(path)==spec.component_sha256)
    var asset:Node3D=load(path).instantiate();root.add_child(asset);var response=load("res://collection/i_chamber_music_response.gd").new();response.bind(asset,spec)
    var checked:=0;var max_error:=0.;var summaries:Array=[]
    for row in ref.meshes:
        var node:=asset.find_child(str(row.mesh),true,false)as MeshInstance3D;assert(node!=null)
        var mesh:=node.mesh as ArrayMesh;assert(mesh.shadow_mesh==null and mesh.get_blend_shape_count()==2)
        var pressure:=node.find_blend_shape_by_name(str(row.pressure));var rebound:=node.find_blend_shape_by_name(str(row.rebound));assert(pressure>=0 and rebound>=0)
        var vertices:=PackedVector3Array();var positive:=PackedVector3Array();var negative:=PackedVector3Array()
        for surface in range(mesh.get_surface_count()):
            var data:Dictionary=RenderingServer.mesh_get_surface(mesh.get_rid(),surface)
            assert(data.get("lods",[]).is_empty())
            assert(not bool(mesh.surface_get_format(surface)&Mesh.ARRAY_FLAG_COMPRESS_ATTRIBUTES))
            var arrays:Array=mesh.surface_get_arrays(surface);var morphs:Array=mesh.surface_get_blend_shape_arrays(surface)
            vertices.append_array(arrays[Mesh.ARRAY_VERTEX]);positive.append_array(morphs[pressure][Mesh.ARRAY_VERTEX]);negative.append_array(morphs[rebound][Mesh.ARRAY_VERTEX])
        assert(vertices.size()==positive.size()and vertices.size()==negative.size())
        for p in row.points:
            var query:=vector(p.local_rest);var nearest:=-1;var distance:=INF
            for i in range(vertices.size()):
                var d:=query.distance_squared_to(vertices[i])
                if d<distance:nearest=i;distance=d
            assert(nearest>=0 and sqrt(distance)<.00001)
            var deltap:Vector3=positive[nearest];var deltan:Vector3=negative[nearest]
            if mesh.blend_shape_mode==Mesh.BLEND_SHAPE_MODE_NORMALIZED:deltap-=vertices[nearest];deltan-=vertices[nearest]
            for value in [-1.,-.5,0.,.5,1.]:
                var delta:Vector3=deltap if value>=0 else deltan;var actual:Vector3=node.global_transform*(vertices[nearest]+delta*absf(value));var expected:=vector(p.world_rest).lerp(vector(p.world_pressure if value>=0 else p.world_rebound),absf(value));var error:=actual.distance_to(expected);max_error=maxf(max_error,error);checked+=1;assert(error<.00001,"Imported morph differs from Blender: "+str(row.mesh))
        summaries.append({"mesh":row.mesh,"vertices":vertices.size(),"morph_mode":mesh.blend_shape_mode,"witnesses":row.points.size()})
    var peak:=0.
    for frame in range(480):
        var playing:=frame<180 or frame>=300 and frame<360;var bands:=Vector3(1.,.6,.3)if playing else Vector3.ZERO
        response.update(bands,float(frame)/60.,playing,1.,1./60.)
        for binding in response.bindings:
            var m:Dictionary=binding.motion;var a:float=m.mesh.get_blend_shape_value(m.pressure);var b:float=m.mesh.get_blend_shape_value(m.rebound);assert(a>=0 and b>=0 and a<=1 and b<=1 and minf(a,b)==0.);assert(absf(a-b-m.position)<.000001);peak=maxf(peak,absf(m.position))
    assert(peak>.5)
    for row in response.bindings:assert(absf(row.motion.position)<.0001 and absf(row.motion.velocity)<.001)
    response.release();response=null
    var output:Dictionary={"passed":true,"source_sha256":spec.source_sha256,"component_sha256":spec.component_sha256,"witness_checks":checked,"maximum_world_error":max_error,"meshes":summaries,"maximum_runtime_shape_weight":peak,"settles_on_pause_and_stop":true,"scope":"Actual imported morph arrays match source world-space witnesses at signed amplitudes; no automatic LOD/compression/proxy on twelve membrane meshes. Runtime bounded spring weights, exclusive pressure/rebound and settling checked. No full-work playback, continuous collision or final art acceptance."}
    FileAccess.open(folder+"runtime_morph_qa.json",FileAccess.WRITE).store_string(JSON.stringify(output,"  "));asset.queue_free();await process_frame;print("I_MEMBRANE_MORPH_QA true ",checked," max_error=",max_error);quit()
