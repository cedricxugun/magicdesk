extends SceneTree
func _initialize()->void:run.call_deferred()
func run()->void:
    var folder:="res://../review/I_refinement/part_a_mouth/shutter_r2/diaphragm/"
    var spec:Dictionary=JSON.parse_string(FileAccess.get_file_as_string(folder+"build.json"))
    var path:String="res://"+str(spec.component).trim_prefix("app/")
    assert(FileAccess.get_sha256(path)==spec.component_sha256)
    var trials:Array=[];var passed:=true
    for fps in [30,60,144]:
        var asset:Node3D=load(path).instantiate();root.add_child(asset)
        var response=load("res://collection/i_diaphragm_response.gd").new();response.bind(asset,spec.diaphragm)
        var maximum:=0.;var minimum:=0.;var quiet_jump:=0.;var samples:Array=[]
        response.set_load(1.)
        for frame in range(fps*6):
            if frame==fps:
                response.set_load(0.);response.impulse(.65)
            if frame==fps*2:response.set_load(.7)
            if frame==int(fps*2.5):
                var before:float=response.displacement
                response.quiet();quiet_jump=absf(response.displacement-before)
                # Late queued input must not restart a cancelled response.
                response.set_load(1.);response.impulse(1.)
            response.tick(1./float(fps))
            maximum=maxf(maximum,response.displacement);minimum=minf(minimum,response.displacement)
            if frame in [fps-1,fps*2-1,fps*3-1]:samples.append(response.displacement)
        var ok:bool=response.settled() and maximum<=response.max_stroke and minimum>=-response.max_stroke and minimum<-.0001 and quiet_jump==0.
        passed=passed and ok
        trials.append({"fps":fps,"passed":ok,"max":maximum,"min":minimum,"quiet_jump":quiet_jump,"final":response.displacement,"settled":response.settled(),"samples":samples})
        asset.queue_free();await process_frame
    var drift:=0.
    for i in range(3):drift=maxf(drift,absf(trials[0].samples[i]-trials[2].samples[i]))
    passed=passed and drift<.00008
    FileAccess.open(folder+"response_qa.json",FileAccess.WRITE).store_string(JSON.stringify({"source_sha256":spec.source_sha256,"component_sha256":spec.component_sha256,"passed":passed,"framerate_drift":drift,"trials":trials,"scope":"Imported morph presence and bounded load/rebound/quiet cancellation at 30/60/144 Hz. No audible audio, native controls, source morph geometry equivalence or visual acceptance claimed."},"  "))
    print("I_DIAPHRAGM_RESPONSE_QA ",passed);quit(0 if passed else 1)
