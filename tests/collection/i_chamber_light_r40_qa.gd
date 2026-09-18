extends SceneTree
func _initialize()->void:run.call_deferred()
func run()->void:
    var folder:="res://../review/I_refinement/nautilus_r1/light_score_r40/refined/"
    for argument in OS.get_cmdline_user_args():
        if argument.begins_with("--report="):folder=argument.trim_prefix("--report=").get_base_dir()+"/"
    var spec:Dictionary=JSON.parse_string(FileAccess.get_file_as_string(folder+"build.json"))
    var control_spec:Dictionary=JSON.parse_string(FileAccess.get_file_as_string("res://../review/I_refinement/nautilus_r1/chamber_motion_r36/build.json"))
    var scene:PackedScene=load("res://"+str(spec.component).trim_prefix("app/"))
    var control_path:String="res://"+str(control_spec.component).trim_prefix("app/")
    assert(FileAccess.get_sha256(control_path)==control_spec.component_sha256)
    var control_scene:PackedScene=load(control_path)
    var asset:Node3D=scene.instantiate();var control:Node3D=control_scene.instantiate();root.add_child(asset);root.add_child(control)
    var finish:Dictionary=load("res://collection/i_finish_r38.gd").apply(asset,str(spec.finish_profile))
    var response=load("res://collection/i_chamber_music_response.gd").new();response.bind(asset,spec)
    var old=load("res://collection/i_chamber_music_response.gd").new();old.bind(control,control_spec)
    assert(response.bindings.size()==12 and old.bindings.size()==12)
    # The new GLB reassigns conduit faces. Compare actual imported membrane
    # buffers against R36 so a source-only signature cannot hide an export drift.
    var preserved_membranes:=0
    for i in range(12):
        var current:MeshInstance3D=response.bindings[i].motion.mesh
        var previous:MeshInstance3D=old.bindings[i].motion.mesh
        var axes_a:Array=[current.global_basis.x,current.global_basis.y,current.global_basis.z,current.global_position]
        var axes_b:Array=[previous.global_basis.x,previous.global_basis.y,previous.global_basis.z,previous.global_position]
        for axis in range(4):
            for component in range(3):assert(float(axes_a[axis][component])==float(axes_b[axis][component]))
        assert(current.mesh.get_surface_count()==previous.mesh.get_surface_count())
        for surface in range(current.mesh.get_surface_count()):
            var a:Array=current.mesh.surface_get_arrays(surface);var b:Array=previous.mesh.surface_get_arrays(surface)
            for field in [Mesh.ARRAY_VERTEX,Mesh.ARRAY_NORMAL,Mesh.ARRAY_INDEX]:assert(a[field].to_byte_array()==b[field].to_byte_array())
            var am:Array=current.mesh.surface_get_blend_shape_arrays(surface);var bm:Array=previous.mesh.surface_get_blend_shape_arrays(surface)
            assert(am.size()==bm.size())
            for key in range(am.size()):
                for field in [Mesh.ARRAY_VERTEX,Mesh.ARRAY_NORMAL]:
                    if am[key][field]!=null:assert(am[key][field].to_byte_array()==bm[key][field].to_byte_array())
        preserved_membranes+=1
    var transport=load("res://collection/i_music_transport.gd").new();root.add_child(transport);transport.setup(str(spec.music_manifest))
    assert(transport.chamber_envelopes.size()==3)
    var trials:Array=[];var maximum_motion_difference:=0.;var minimum_lit_floor:=INF
    var inputs:Array=[{"name":"open_silence","bands":Vector3.ZERO,"playing":false,"opening":1.}]
    for movement in range(3):
        var values:PackedVector3Array=transport.chamber_envelopes[movement]
        for fraction in [.01,.15,.5,.85]:
            inputs.append({"name":"recording_%d_%s"%[movement+1,str(fraction)],"bands":values[int((values.size()-1)*fraction)],"playing":true,"opening":1.})
    inputs.append({"name":"silent_high_band","bands":Vector3(.16,.035,0.),"playing":true,"opening":1.})
    inputs.append({"name":"pause","bands":Vector3.ZERO,"playing":false,"opening":1.})
    inputs.append({"name":"closed_stale_audio","bands":Vector3.ONE,"playing":true,"opening":0.})
    for input in inputs:
        for step in range(180):
            response.update(input.bands,12.,input.playing,input.opening,1./60.)
            old.update(input.bands,12.,input.playing,input.opening,1./60.)
            for i in range(12):
                var motion:Dictionary=response.bindings[i].motion;var reference:Dictionary=old.bindings[i].motion
                maximum_motion_difference=maxf(maximum_motion_difference,absf(motion.position-reference.position))
                assert(motion.position==reference.position and motion.velocity==reference.velocity,"Light floor changed physical membrane response")
        var cells:Array=[]
        for row in response.bindings:
            var minimum_base:=INF;var lit_surfaces:=0
            for surface in row.materials:
                var material:ShaderMaterial=surface.material
                var base:float=material.get_shader_parameter("base_response");var value:float=material.get_shader_parameter("response")
                if surface.emits:
                    minimum_base=minf(minimum_base,base);lit_surfaces+=1
                else:assert(base==0. and value==0.,"Metal frame still glows instead of its diffuser")
                if input.opening==0.:assert(base==0. and value==0.,"Closed chamber still emits")
                elif surface.emits:assert(base>.239,"A quiet conduit went dark")
            assert(lit_surfaces>0,"Chamber has no actual diffuser")
            if input.opening>0.:minimum_lit_floor=minf(minimum_lit_floor,minimum_base)
            if row.light!=null:
                assert(row.light.shadow_enabled and row.light.light_energy<=1.15)
                if input.opening==0.:assert(row.light.light_energy==0.)
            if not input.playing:assert(absf(row.motion.position)<.0001)
            cells.append({"frame":str(row.mesh.name),"base":minimum_base,"music":response.levels[row.band],"motion":row.motion.position})
        trials.append({"name":input.name,"cells":cells})
    var originals:Array=[]
    for row in response.bindings:
        for surface in row.materials:originals.append({"mesh":surface.mesh,"index":surface.index,"material":surface.original})
    response.release();old.release()
    for row in originals:assert(row.mesh.get_active_material(row.index)==row.material)
    var result:Dictionary={"passed":true,"source_sha256":spec.source_sha256,"component_sha256":spec.component_sha256,"layout_sha256":FileAccess.get_sha256(str(spec.chamber_response_layout)),"finish_profile_sha256":finish.profile_sha256,"minimum_open_floor":minimum_lit_floor,"imported_membrane_buffers_equal_to_r36":preserved_membranes,"maximum_motion_difference_from_r36":maximum_motion_difference,"trials":trials,"scope":"Twelve real imported chamber groups and sixteen split conduits; old metal-frame emission is zero, actual three-recording band samples plus absent high band, open/pause floor, exact closed emission and spill zero, unchanged membrane trajectories versus R36, release restores finish. Does not prove all-angle visibility, full-work playback or native acceptance."}
    result["control_component_path"]=control_path
    result["control_component_sha256"]=control_spec.component_sha256
    result["independent_reference_scene"]=true
    FileAccess.open(folder+"light_qa.json",FileAccess.WRITE).store_string(JSON.stringify(result,"  "))
    originals.clear();response=null;old=null;transport.stop();transport.queue_free();asset.queue_free();control.queue_free();scene=null;control_scene=null;await process_frame;print("I_CHAMBER_LIGHT_R40_QA true");quit()
