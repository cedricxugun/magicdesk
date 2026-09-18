extends SceneTree
func _initialize()->void:run.call_deferred()
func run()->void:
    var report_path:="res://../review/I_refinement/nautilus_r1/chamber_response_r35/build.json"
    for arg in OS.get_cmdline_user_args():
        if arg.begins_with("--report="):report_path=arg.trim_prefix("--report=")
    var spec:Dictionary=JSON.parse_string(FileAccess.get_file_as_string(report_path))
    var path:String="res://"+str(spec.component).trim_prefix("app/");assert(FileAccess.get_sha256(path)==spec.component_sha256)
    var asset:Node3D=load(path).instantiate();root.add_child(asset)
    var response=load("res://collection/i_chamber_music_response.gd").new();response.bind(asset,spec);assert(response.bindings.size()==12)
    var originals:Dictionary={}
    for row in response.bindings:originals[str(row.mesh.name)]=row.mesh.mesh
    var transport=load("res://collection/i_music_transport.gd").new();root.add_child(transport);transport.setup(str(spec.music_manifest))
    assert(transport.chamber_envelopes.size()==3 and transport.total_length>960.)
    var samples:Array=[]
    transport.play_complete();transport.pause()
    for movement in range(3):
        var values:PackedVector3Array=transport.chamber_envelopes[movement]
        for fraction in [0.,.15,.5,.85]:
            var local_time:float=float(transport.tracks[movement].duration)*fraction
            transport.seek_total(float(transport.tracks[movement].start)+local_time)
            assert(transport.index==movement and transport.state=="paused"and transport.chamber_bands()==Vector3.ZERO)
            transport.resume()
            var cursor:float=local_time/transport.chamber_interval;var first:=mini(int(floorf(cursor)),values.size()-1);var last:=mini(first+1,values.size()-1)
            var expected:=values[first].lerp(values[last],cursor-float(first));var actual:Vector3=transport.chamber_bands()
            assert(expected.distance_to(actual)<.00001)
            response.update(actual,local_time,true,1.,4.)
            for row in response.bindings:
                var material:ShaderMaterial=row.materials[0].material;var level:float=material.get_shader_parameter("response");assert(absf(level-actual[row.band])<.0001)
                assert(row.mesh.mesh==originals[str(row.mesh.name)])
                if row.light!=null:assert(row.light.shadow_enabled and row.light.light_energy<=.16001)
            samples.append({"movement":movement+1,"seconds":local_time,"bands":[actual.x,actual.y,actual.z]})
            transport.pause();var before:float=transport.local_clock
            for frame in range(10):await process_frame
            assert(transport.local_clock==before)
    response.update(Vector3.ONE,25.,true,1.,1.)
    for frame in range(120):response.update(Vector3.ZERO,25.,false,1.,1./60.)
    assert(response.levels.length()<.0001)
    response.update(Vector3.ONE,25.,true,0.,1.)
    assert(response.levels.length()<.0001,"Closed shell must not retain chamber spill")
    var default_transport=load("res://collection/i_music_transport.gd").new();root.add_child(default_transport);default_transport.setup("res://assets/collection/art/I/moonlight_candidate/manifest.json");assert(default_transport.chamber_bands()==Vector3.ZERO)
    var layout_path:String=spec.chamber_response_layout
    var result:Dictionary={"passed":true,"source_sha256":spec.source_sha256,"component_sha256":spec.component_sha256,"layout_sha256":FileAccess.get_sha256(layout_path),"band_envelope_sha256":transport.chamber_envelope_sha256,"samples":samples,"paused_clock_stable":true,"closed_gate_and_release_passed":true,"geometry_resources_unchanged":true,"scope":"All three recordings load and route interpolated bands to 12 frame materials. Pause/seek, release/closed gate, unchanged mesh resources and bounded shadowed spill checked. No full-work playback, diaphragm deformation or final art acceptance."}
    FileAccess.open(report_path.get_base_dir()+"/qa.json",FileAccess.WRITE).store_string(JSON.stringify(result,"  "))
    transport.stop();default_transport.stop();response.release();response=null;originals.clear();await create_timer(.1).timeout
    transport.queue_free();default_transport.queue_free();asset.queue_free();await process_frame;print("I_CHAMBER_MUSIC_QA true");quit()
