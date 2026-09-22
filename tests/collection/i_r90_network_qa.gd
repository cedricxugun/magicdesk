extends SceneTree
func _initialize()->void:run.call_deferred()
func run()->void:
    var folder:="res://../review/I_refinement/nautilus_reset_r82/network_r90/built_r5/"
    for a in OS.get_cmdline_user_args():
        if a.begins_with("--folder="):folder=a.trim_prefix("--folder=").trim_suffix("/")+"/"
    var spec:Dictionary=JSON.parse_string(FileAccess.get_file_as_string(folder+"build.json"))
    var layout:Dictionary=JSON.parse_string(FileAccess.get_file_as_string(str(spec.chamber_response_layout)))
    var asset:Node3D=load("res://"+str(spec.component).trim_prefix("app/")).instantiate();root.add_child(asset)
    var response=load("res://collection/i_chamber_music_response.gd").new();response.bind(asset,spec)
    assert(response.network_bindings.size()==layout.network.segments.size() and response.wants_work_clock())
    var ranges:Dictionary={};var vertices_checked:=0
    for row in layout.network.segments:
        var mesh:=asset.find_child(str(row.mesh),true,false) as MeshInstance3D;assert(mesh!=null)
        var low:=INF;var high:=-INF
        for i in range(mesh.mesh.get_surface_count()):
            var uv:PackedVector2Array=mesh.mesh.surface_get_arrays(i)[Mesh.ARRAY_TEX_UV]
            for p in uv:low=minf(low,p.x);high=maxf(high,p.x);vertices_checked+=1
        assert(absf(low-float(row.uv_start))<.00001 and absf(high-float(row.uv_end))<.00001)
        ranges[str(row.mesh)]=[low,high]
    var connections:Array=[]
    for port in spec.network.ports:
        var target:float=float(port.distance)/float(spec.network.maximum_distance)
        var matches:Array=[]
        for segment in layout.network.segments:
            if segment.cells.size()==1 and int(segment.cells[0])==int(port.cell) and absf(float(segment.uv_end)-target)<.00001:matches.append(segment)
        assert(matches.size()==1)
        var actual:float=ranges[str(matches[0].mesh)][1]
        var ring_phase:float=float(port.angle)/TAU+float(layout.cells[int(port.cell)].phase_offset)
        assert(absf(actual-ring_phase)<.00001)
        connections.append({"cell":port.cell,"actual_branch_end_uv":actual,"ring_entry_phase":ring_phase})
    response.update(Vector3(.8,.5,.2),100.,true,1.,1.)
    for row in response.network_bindings:
        for mat in row.materials:assert(is_equal_approx(float(mat.material.get_shader_parameter("travel")),100.))
    response.update(Vector3.ZERO,0.,false,1.,1./60.)
    assert(is_equal_approx(response.network_clock,100.),"Stopping transport must not jump a visible wave")
    response.update(Vector3.ZERO,0.,false,0.,2.)
    assert(response.network_clock==0. and response.light_floor==0.)
    var result:Dictionary={"passed":true,"source_sha256":spec.source_sha256,"component_sha256":spec.component_sha256,"network_segments":response.network_bindings.size(),"uv_vertices_checked":vertices_checked,"connections":connections,"pause_holds_wave":true,"closed_resets_wave":true,"scope":"Actual imported UV ranges meet the physical-distance model and 12 cell-entry phases. Material clock updates, pause/stop hold and closed reset verified. Not all visual/performance/pressure-control or full-song acceptance."}
    response.release();asset.queue_free();await process_frame
    FileAccess.open(folder+"network_runtime_qa.json",FileAccess.WRITE).store_string(JSON.stringify(result,"  "));print("R90_NETWORK_QA true ",vertices_checked);quit()
