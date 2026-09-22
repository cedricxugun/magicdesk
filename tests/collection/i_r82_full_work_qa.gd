extends SceneTree
## Natural complete-work transport/score continuity, with no seek or pause.
## Dummy output tests timing/state; it does not prove speaker quality.
var asset:Node3D
var rig:RefCounted
var music:Node
var started_usec:=0
var playing_started_usec:=0
var ready:=false
var next_sample:=0.
var last_position:=-1.
var samples:Array=[]
var movements_seen:Dictionary={}
var failed:=false
var final_passed:=false
var output:="res://../review/I_refinement/nautilus_reset_r82/music_interface_r1/full_work_r2"
func _initialize()->void:run.call_deferred()
func run()->void:
    Engine.max_fps=120
    var directory_error:=DirAccess.make_dir_recursive_absolute(ProjectSettings.globalize_path(output))
    assert(directory_error==OK,"Cannot create full-work report directory")
    var spec:Dictionary=JSON.parse_string(FileAccess.get_file_as_string("res://../review/I_refinement/nautilus_reset_r82/music_interface_r1/optical_core_build_r2.json"))
    asset=load("res://"+str(spec.component).trim_prefix("app/")).instantiate();root.add_child(asset)
    rig=load("res://collection/i_mouth_response_rig.gd").new();rig.bind(asset,spec,JSON.parse_string(FileAccess.get_file_as_string(spec.aperture_profile)))
    music=load("res://collection/i_moonlight_controller.gd").new();root.add_child(music);music.setup(asset,spec,rig)
    started_usec=Time.get_ticks_usec();music.toggle();ready=true
    FileAccess.open(output+"/started.json",FileAccess.WRITE).store_string(JSON.stringify({"pid":OS.get_process_id(),"core_sha256":spec.component_sha256,"scope":"Natural complete-work run; dummy audio; no intentional seek/pause"}, "  "))
func fail(message:String)->void:
    if failed:return
    failed=true;ready=false
    FileAccess.open(output+"/result.json",FileAccess.WRITE).store_string(JSON.stringify({"passed":false,"error":message,"samples":samples},"  "))
    push_error(message);music.transport.stop();quit(1)
func _process(delta:float)->bool:
    if not ready or failed:return false
    rig.tick(delta);music.tick(delta)
    var elapsed:=float(Time.get_ticks_usec()-started_usec)/1000000.
    var state:String=music.transport.state
    var position:float=music.transport.position_seconds()
    if state=="playing":
        if playing_started_usec==0:playing_started_usec=Time.get_ticks_usec()
        if position+0.015<last_position:fail("Audio clock moved backwards without a user action");return false
        last_position=maxf(last_position,position)
        movements_seen[int(music.transport.index)+1]=true
    if elapsed>=next_sample:
        next_sample=elapsed+5.
        var snapshot:Dictionary={"elapsed":elapsed,"state":state,"position":position,"movement":int(music.transport.index)+1,"staff":music.staff.status.duplicate(true),"rig":rig.state()}
        samples.append(snapshot)
        FileAccess.open(output+"/live.json",FileAccess.WRITE).store_string(JSON.stringify(snapshot,"  "))
        print("R83_FULL_WORK ",elapsed," ",state," ",position," movement=",int(music.transport.index)+1)
        if elapsed>12. and position<1.:fail("Playback did not advance on the live audio clock");return false
    if elapsed>1020.:fail("Complete work did not finish within its natural duration plus setup margin");return false
    if state=="ended":
        ready=false
        var natural_duration:=float(Time.get_ticks_usec()-playing_started_usec)/1000000.
        var passed:bool=movements_seen.size()==3 and position>960. and music.staff.status.ready
        FileAccess.open(output+"/result.json",FileAccess.WRITE).store_string(JSON.stringify({"passed":passed,"natural_elapsed":natural_duration,"position":position,"movements_seen":movements_seen,"samples":samples,"scope":"Natural three-movement transport and score requests, no pause/seek. Dummy audio, no whole-body/native visuals/exact beat alignment acceptance."},"  "))
        final_passed=passed
        finish.call_deferred()
    return false
func finish()->void:
    music.transport.stop();music.queue_free();asset.queue_free()
    await create_timer(.20).timeout
    rig=null;music=null;asset=null
    quit(0 if final_passed else 1)
