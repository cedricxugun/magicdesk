extends SceneTree
var collected:Array=[]
var max_opening_mismatch:=0.
var max_opening_step_excess:=0.
func _initialize()->void:run.call_deferred()
func advance(rig:RefCounted,seconds:float,fps:int)->void:
    for frame in range(roundi(seconds*fps)):
        var before:float=rig.openness
        rig.tick(1./float(fps));collected.append_array(rig.drain_events())
        max_opening_mismatch=maxf(max_opening_mismatch,absf(rig.openness-rig.acoustics.iris))
        max_opening_step_excess=maxf(max_opening_step_excess,absf(rig.openness-before)-1./float(fps)/2.6)
func run()->void:
    var folder:="res://../review/I_refinement/part_a_mouth/shutter_r2/diaphragm/"
    for argument in OS.get_cmdline_user_args():
        if argument.begins_with("--report="):folder=argument.trim_prefix("--report=").get_base_dir()+"/"
    var spec:Dictionary=JSON.parse_string(FileAccess.get_file_as_string(folder+"build.json"))
    var aperture:Dictionary=JSON.parse_string(FileAccess.get_file_as_string(str(spec.get("aperture_profile","res://assets/collection/art/I/diaphragm/aperture_profile.json"))))
    var path:String="res://"+str(spec.component).trim_prefix("app/");assert(FileAccess.get_sha256(path)==spec.component_sha256)
    var trials:Array=[]
    for fps in [30,60,144]:
        collected=[]
        var asset:Node3D=load(path).instantiate();root.add_child(asset)
        var rig=load("res://collection/i_mouth_response_rig.gd").new();rig.bind(asset,spec,aperture)
        rig.set_pressed(true);advance(rig,1.,fps);assert(collected.is_empty())
        rig.set_pressed(false);advance(rig,2.3,fps)
        assert(collected.size()==2 and collected[0].kind=="outgoing" and collected[1].kind=="return")
        assert(float(collected[0].opening)>=.28 and float(collected[1].time)>float(collected[0].time))
        assert(float(collected[1].gain)<float(collected[0].gain))
        var normal_events:=collected.duplicate(true)
        rig.set_open(false);var close_start:float=rig.openness;advance(rig,1./fps,fps)
        assert(is_equal_approx(rig.openness,close_start),"Shutters must wait for suspension recovery")
        advance(rig,6.,fps);assert(rig.stage=="closed" and rig.suspension.settled())
        # Cancel a scheduled return, then reopen. The old return must stay gone.
        collected=[];rig.set_pressed(true);advance(rig,1.,fps);rig.set_pressed(false);advance(rig,.9,fps)
        assert(collected.size()==1 and rig.acoustics.return_schedule().size()==1)
        var before:float=rig.suspension.displacement;rig.set_open(false)
        assert(rig.suspension.displacement==before and rig.acoustics.return_schedule().is_empty())
        rig.set_open(true);advance(rig,2.,fps);assert(collected.size()==1)
        # Re-press before the release pose. Only the last release may emit.
        collected=[];rig.set_pressed(true);advance(rig,3.,fps);rig.set_pressed(false);advance(rig,.15,fps);rig.set_pressed(true);advance(rig,.4,fps);rig.set_pressed(false);advance(rig,2.3,fps)
        assert(collected.size()==2)
        rig.set_open(false);advance(rig,6.,fps);assert(rig.stage=="closed")
        trials.append({"fps":fps,"normal_events":normal_events,"final":rig.state(),"cancellation_passed":true,"repress_passed":true})
        asset.queue_free();await process_frame
    assert(max_opening_mismatch<.000001 and max_opening_step_excess<.000001)
    FileAccess.open(folder+"rig_qa.json",FileAccess.WRITE).store_string(JSON.stringify({"source_sha256":spec.source_sha256,"component_sha256":spec.component_sha256,"passed":true,"trials":trials,"max_opening_mismatch":max_opening_mismatch,"max_opening_step_excess":max_opening_step_excess,"scope":"Current imported mouth/morphs with coupled aperture/load/release/echo/close order, cancellation+reopen and re-press at three rates. No audible sound, native keyboard input or AAA acceptance."},"  "))
    print("I_MOUTH_RESPONSE_RIG_QA true");quit()
