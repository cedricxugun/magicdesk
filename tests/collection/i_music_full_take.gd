extends SceneTree
var transport:Node
var samples:Array=[]
var errors:Array=[]
var started:=0
var next_sample:=0.
var previous_position:=0.
var previous_movement:=1
var previous_quarter:=0.
var last_advance_wall:=0.
var done:=false
var out:="res://../review/I_refinement/moonlight/full_take.json"
func _initialize()->void:run.call_deferred()
func write_progress()->void:
    FileAccess.open(out,FileAccess.WRITE).store_string(JSON.stringify({"status":"running" if not done else "finished","elapsed":(Time.get_ticks_msec()-started)/1000.,"snapshot":transport.snapshot(),"errors":errors,"samples":samples,"scope":"Uninterrupted real-time full-work Godot decoding/transport with Dummy audio output. Does not assess audible quality, score alignment or native controls."},"  "))
func run()->void:
    transport=load("res://collection/i_music_transport.gd").new();root.add_child(transport)
    transport.setup("res://assets/collection/art/I/moonlight_candidate/manifest.json")
    started=Time.get_ticks_msec();transport.work_finished.connect(func():done=true);transport.play_complete()
    print("I_MUSIC_FULL_TAKE_STARTED ",transport.total_length)
    while not done:
        await create_timer(.25).timeout
        var state:Dictionary=transport.snapshot();var elapsed:float=(Time.get_ticks_msec()-started)/1000.
        if float(state.total_seconds)+.01<previous_position:errors.append({"kind":"position regressed","at":elapsed})
        if int(state.movement)==previous_movement and float(state.score_quarter_estimate)+.000001<previous_quarter:errors.append({"kind":"score clock regressed","at":elapsed})
        if float(state.total_seconds)>previous_position+.000001:last_advance_wall=elapsed
        previous_position=state.total_seconds;previous_movement=state.movement;previous_quarter=state.score_quarter_estimate
        if elapsed>=next_sample:
            samples.append({"elapsed":elapsed,"state":state});next_sample=elapsed+15.;write_progress();print("I_MUSIC_FULL_TAKE_PROGRESS ",int(elapsed)," ",int(state.movement))
        if elapsed>transport.total_length*1.25+30. or elapsed-last_advance_wall>20.:errors.append({"kind":"audio stalled or hard timeout"});done=true
    var elapsed:float=(Time.get_ticks_msec()-started)/1000.
    if transport.state!="ended":errors.append({"kind":"did not end naturally"})
    if elapsed<transport.total_length-2.:errors.append({"kind":"finished too early","elapsed":elapsed})
    write_progress()
    var result:Dictionary=JSON.parse_string(FileAccess.get_file_as_string(out));result.passed=errors.is_empty();FileAccess.open(out,FileAccess.WRITE).store_string(JSON.stringify(result,"  "))
    print("I_MUSIC_FULL_TAKE_FINISHED ",result.passed);transport.queue_free();await process_frame;quit(0 if errors.is_empty() else 1)
