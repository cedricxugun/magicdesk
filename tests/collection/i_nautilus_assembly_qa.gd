extends SceneTree
var assembly:Node3D
var cases:Array=[]
var largest_step:=0.
func _initialize()->void:run.call_deferred()
func advance(seconds:float)->void:
    for i in range(ceili(seconds*60.)):
        var before:float=assembly.sequence.shell_open;var mouth_before:float=assembly.rig.openness
        assembly.tick(1./60.)
        var after:float=assembly.sequence.shell_open
        largest_step=maxf(largest_step,absf(after-before))
        if before==0. and after>0. and not assembly.rig.user_pressed:assert(mouth_before>.999,"Shell started before throat ready")
        if not assembly.sequence.desired_open and after>.00001:assert(assembly.rig.closing_hold)
        await process_frame
func record(name:String)->void:cases.append({"case":name,"state":assembly.status.duplicate(true),"mouth":assembly.rig.state()})
func run()->void:
    var folder:="res://../review/I_refinement/nautilus_r1/interactive_r58/"
    var spec:Dictionary=JSON.parse_string(FileAccess.get_file_as_string("res://../review/I_refinement/nautilus_r1/cap_lower_trim_r55/build.json"))
    spec["mouth_spec"]=JSON.parse_string(FileAccess.get_file_as_string("res://../"+str(spec.mouth_report)))
    assembly=load("res://collection/i_nautilus_assembly.gd").new();root.add_child(assembly);assembly.setup(spec)
    assert(assembly.music.transport.chamber_envelopes.size()==3)
    assert(assembly.music.staff.scanner_caps.size()==3)
    assert(assembly.music.staff.material.get_shader_parameter("optical_backing")==0.)
    assembly.sequence.music_request();assembly.music.toggle();await advance(1.)
    assert(assembly.sequence.shell_open==0. and assembly.rig.openness>0. and assembly.music.start_pending and assembly.music.transport.state=="stopped");record("mouth_before_shell")
    await advance(5.);assert(assembly.sequence.shell_open>.999 and assembly.rig.openness>.999 and assembly.music.transport.state=="playing");record("ready_playing")
    assembly.music.seek(12.);await create_timer(.10).timeout;await advance(.25)
    assert(assembly.rig.music_level>0. and assembly.chambers.levels.length()>0.);record("same_music_drives_mouth_and_chambers")
    assembly.music.toggle();var paused:float=assembly.music.transport.position_seconds();await advance(1.)
    assert(assembly.music.transport.state=="paused" and assembly.music.transport.position_seconds()==paused);record("manual_pause")
    assembly.music.toggle();await advance(.2);assert(assembly.music.transport.state=="playing")
    assembly.sequence.set_open(false);await advance(.2);assert(assembly.sequence.shell_open>.999 and assembly.rig.openness>.999);record("wait_for_score_fade")
    await advance(.65);assert(assembly.sequence.shell_open<.99 and assembly.sequence.shell_open>.5 and assembly.rig.openness>.999);record("covers_close_throat_held")
    var partial:float=assembly.sequence.shell_open;assembly.sequence.set_open(true);await advance(.3);assert(assembly.sequence.shell_open>partial);record("reverse_cover_closing")
    assembly.sequence.set_open(false);await advance(6.);assert(assembly.sequence.shell_open==0. and assembly.rig.openness==0. and assembly.music.transport.state=="stopped");record("fully_stowed")
    assembly.sequence.music_request();assembly.music.toggle();await advance(.4);assembly.sequence.set_open(false);await advance(4.)
    assert(not assembly.music.start_pending and assembly.music.transport.state=="stopped" and assembly.sequence.shell_open==0. and assembly.rig.openness==0.);record("cancel_pending_play")
    var outgoing:int=assembly.rig.acoustics.outgoing_count;assembly.sequence.set_pressed(true);await advance(.3);assembly.sequence.set_open(false);await advance(5.)
    assert(not assembly.rig.user_pressed and assembly.rig.acoustics.return_schedule().is_empty() and assembly.rig.acoustics.outgoing_count==outgoing);record("cancel_charge")
    assert(largest_step<=1./60./assembly.sequence.shell_duration+.00001)
    await assembly.shutdown();await process_frame;await process_frame;assert(not is_instance_valid(assembly))
    FileAccess.open(folder+"assembly_qa.json",FileAccess.WRITE).store_string(JSON.stringify({"passed":true,"source_sha256":spec.source_sha256,"component_sha256":spec.component_sha256,"largest_shell_step":largest_step,"cases":cases,"scope":"Current actual assembly with real music controller and authored drivers; deterministic mechanical ticks plus dummy audio, startup gating, pause, score-close, reversal, cancelled start/charge and graceful teardown. Not OS input, full-work playback, full collision or final art/native acceptance."},"  "))
    print("I_NAUTILUS_ASSEMBLY_QA true");quit()
