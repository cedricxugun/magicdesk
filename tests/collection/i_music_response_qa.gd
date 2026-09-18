extends SceneTree
func _initialize()->void:run.call_deferred()
func run()->void:
    var folder:="res://../review/I_refinement/moonlight/current_mouth/response/"
    var manifest_path:="res://assets/collection/art/I/moonlight_candidate/manifest.json"
    var manifest:Dictionary=JSON.parse_string(FileAccess.get_file_as_string(manifest_path))
    var report_path:="res://../review/I_refinement/part_a_mouth/shutter_r2/diaphragm/build.json"
    for argument in OS.get_cmdline_user_args():
        if argument.begins_with("--report="):
            report_path=argument.trim_prefix("--report=");folder=report_path.get_base_dir()+"/"
    var spec:Dictionary=JSON.parse_string(FileAccess.get_file_as_string(report_path))
    var transport=load("res://collection/i_music_transport.gd").new();root.add_child(transport);transport.setup(manifest_path)
    assert(transport.response_envelopes.size()==3)
    var trials:Array=[]
    for fps in [30,60,144]:
        var asset:Node3D=load("res://"+str(spec.component).trim_prefix("app/")).instantiate();root.add_child(asset)
        var suspension=load("res://collection/i_diaphragm_response.gd").new();suspension.bind(asset,spec.diaphragm)
        var maximum:=0.;var minimum:=0.;var silent_max:=0.;var motion_trace:Array=[]
        # Deterministic complete-recording clock sweep. No real-time playback claim.
        transport.state="playing"
        for chapter in range(3):
            transport.index=chapter
            var duration:float=transport.tracks[chapter].duration
            for frame in range(int(ceil(duration*fps))):
                transport.local_clock=minf(float(frame)/fps,duration)
                var level:float=transport.response_level()
                suspension.set_load(level*.5);suspension.tick(1./float(fps))
                maximum=maxf(maximum,suspension.displacement);minimum=minf(minimum,suspension.displacement)
                if chapter==0 and transport.local_clock<3.:silent_max=maxf(silent_max,absf(suspension.displacement))
                if frame%fps==0:motion_trace.append(suspension.displacement)
                assert(absf(suspension.moving.position.x-suspension.rest_position.x)<.000001)
                assert(absf(suspension.moving.position.z-suspension.rest_position.z)<.000001)
        assert(maximum<.003 and minimum>-.001 and maximum>.001 and silent_max==0.)
        transport.state="paused";assert(transport.response_level()==0.)
        var before:float=suspension.displacement;suspension.set_load(transport.response_level()*.5)
        assert(suspension.displacement==before,"Pause must release load without snapping geometry")
        for frame in range(fps*3):suspension.tick(1./float(fps))
        assert(suspension.settled())
        transport.state="ended";assert(transport.response_level()==0.)
        transport.state="stopped";assert(transport.response_level()==0.)
        trials.append({"fps":fps,"max_stroke":maximum,"min_stroke":minimum,"silent_intro_max":silent_max,"pause_settled":true,"trace":motion_trace})
        asset.queue_free();await process_frame
    var drift:=0.
    for frame in range(trials[0].trace.size()):drift=maxf(drift,absf(trials[0].trace[frame]-trials[2].trace[frame]))
    assert(drift<.00025)
    for trial in trials:trial.erase("trace")
    transport.stop();await create_timer(.1).timeout
    FileAccess.open(folder+"response_qa.json",FileAccess.WRITE).store_string(JSON.stringify({"passed":true,"source_sha256":spec.source_sha256,"component_sha256":spec.component_sha256,"envelope_sha256":manifest.response_envelope_sha256,"frame_rate_sample_drift":drift,"trials":trials,"scope":"Complete three-recording clock sweeps at 30/60/144Hz through current authored suspension, bounded axial movement, silent intro, pause/stop/ended neutralization. Synthetic clock sweep; not native full-work playback, subjective sound or full conch acceptance."},"  "))
    print("I_MUSIC_RESPONSE_QA true drift=",drift);transport.queue_free();await process_frame;quit()
