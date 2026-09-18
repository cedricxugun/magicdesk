extends SceneTree
var transport:Node
var movements:Array=[]
var ended:=0
var errors:Array=[]
func _initialize()->void:run.call_deferred()
func run()->void:
    transport=load("res://collection/i_music_transport.gd").new();root.add_child(transport)
    transport.setup("res://assets/collection/art/I/moonlight_candidate/manifest.json")
    transport.movement_changed.connect(func(i:int):movements.append(i))
    transport.work_finished.connect(func():ended+=1)
    transport.play_complete();await create_timer(.15).timeout
    transport.seek_total(17.);await create_timer(.12).timeout;transport.pause()
    var paused:float=transport.position_seconds();await create_timer(.2).timeout
    if absf(transport.position_seconds()-paused)>.000001:errors.append("paused audio clock advanced")
    transport.seek_total(3.);await create_timer(.1).timeout
    if transport.state!="paused" or absf(transport.position_seconds()-3.)>.000001:errors.append("paused backward seek did not preserve state/position")
    transport.resume();await create_timer(.2).timeout
    if transport.position_seconds()<=3.:errors.append("resume did not advance")
    for i in range(3):
        transport.seek_total(float(transport.tracks[i].start)+float(transport.tracks[i].duration)-.12)
        await create_timer(.5).timeout
        if i<2 and transport.index!=i+1:errors.append("missing natural next movement "+str(i+1))
    if ended!=1 or transport.state!="ended" or absf(transport.position_seconds()-transport.total_length)>.000001:errors.append("whole work did not end exactly once")
    transport.play_complete();await create_timer(.08).timeout;transport.stop();await create_timer(.08).timeout
    if transport.state!="stopped" or transport.player.playing or transport.position_seconds()!=0.:errors.append("stop/restart did not reset")
    var durations:Array=[]
    for track in transport.tracks:durations.append(track.duration)
    var result:={"passed":errors.is_empty(),"errors":errors,"movement_events":movements,"stream_durations":durations,"total_duration":transport.total_length,"scope":"Real Godot audio transport under Dummy output: pause/resume/backward seek, natural ends of each movement, final finish and stop/restart. Seeks cover boundaries; not a complete 16-minute playback/listening test or score-sync/native/art acceptance."}
    DirAccess.make_dir_recursive_absolute("res://../review/I_refinement/moonlight")
    FileAccess.open("res://../review/I_refinement/moonlight/transport_check.json",FileAccess.WRITE).store_string(JSON.stringify(result,"  "));print("I_MUSIC_TRANSPORT ",JSON.stringify(result));transport.queue_free();await process_frame;quit(0 if errors.is_empty() else 1)
