extends Node
## Complete work + real staff on the current mouth. Audio clock is authoritative.
var transport:Node
var staff:Node3D
var rig:RefCounted
var presentation:Node3D
var reveal:=0.
var active:=false
var start_pending:=false
var pause_pending:=false
var close_pending:=false
var stopping:=false
var music_volume_db:=0.
var reveal_permitted:=true
var status:Dictionary={}
func setup(asset:Node3D,spec:Dictionary,mouth_rig:RefCounted,echo:Node3D=null)->void:
    rig=mouth_rig;presentation=echo
    transport=load("res://collection/i_music_transport.gd").new();add_child(transport)
    transport.setup(str(spec.get("music_manifest","res://assets/collection/art/I/moonlight_candidate/manifest.json")))
    music_volume_db=transport.player.volume_db
    staff=load("res://collection/i_moonlight_staff.gd").new();add_child(staff);staff.setup(asset,str(spec.component_sha256),str(spec.get("music_optics_layout","res://assets/collection/art/I/moonlight_candidate/current_mouth/layout.json")))
    transport.work_finished.connect(_finished)
func engaged()->bool:return active or reveal>.001
func toggle()->void:
    if not active:
        active=true;start_pending=true;pause_pending=false;close_pending=false;stopping=false
        transport.stop()
        transport.player.volume_db=music_volume_db
        rig.set_open(false)
        rig.set_open(true)
        if presentation:presentation.set_music_mode(true)
    elif start_pending:pause_pending=not pause_pending
    elif transport.state=="playing":transport.pause()
    elif transport.state=="paused":transport.resume()
    elif transport.state=="ended":transport.play_complete()
func stop(close_mouth:bool=false)->void:
    active=false;start_pending=false;pause_pending=false;close_pending=close_mouth;stopping=true
func _finished()->void:
    if stopping or not active:return
    # Leave the last score location visible until the user stops or restarts.
    active=true
func seek(seconds:float)->void:
    if active and not start_pending:transport.seek_total(seconds)
func tick(delta:float)->void:
    if stopping:transport.player.volume_db=move_toward(transport.player.volume_db,-60.,maxf(0.,delta)*95.)
    var target:=1. if active and rig.openness>.98 and (reveal_permitted or not start_pending) else 0.
    reveal=move_toward(reveal,target,maxf(0.,delta)/.65)
    var movement:int=1 if start_pending else transport.index+1
    var quarter:float=0. if start_pending else transport.score_quarter_estimate()
    staff.set_score_position(movement,quarter,reveal)
    if start_pending and reveal>=.999 and staff.status.ready:
        transport.play_complete()
        if pause_pending:transport.pause()
        start_pending=false
    if not engaged():
        if stopping:transport.stop();transport.player.volume_db=music_volume_db;stopping=false
        if presentation:presentation.set_music_mode(false)
        if close_pending:rig.set_open(false);close_pending=false
    # The same output-latency-corrected clock as the score drives the authored
    # axial suspension. Pausing removes load and lets its existing damping settle.
    var level:float=transport.response_level() if active or stopping else 0.
    if stopping:level*=db_to_linear(transport.player.volume_db-music_volume_db)
    rig.set_music_level(level)
    staff.set_music_response(level,transport.state=="playing" and active and not start_pending,transport.state!="stopped" and not start_pending)
    status={"active":active,"reveal":reveal,"starting":start_pending,"pause_pending":pause_pending,"transport":transport.snapshot(),"staff":staff.status.duplicate(true),"close_pending":close_pending,"response_level":level}
