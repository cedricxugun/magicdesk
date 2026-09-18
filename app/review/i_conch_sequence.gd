extends RefCounted
## Full-device order: unload first, close the shell tip-to-mouth, then throat.
## Shell parts follow their authored mechanism; this only coordinates timing.
var body:RefCounted
var mouth:RefCounted
var music:Node
var desired_open:=false
var shell_open:=0.0
var shell_duration:=4.2
var stage:="closed"

func bind(body_driver:RefCounted,mouth_driver:RefCounted,music_controller:Node=null)->void:
    body=body_driver;mouth=mouth_driver;music=music_controller
    mouth.closing_hold=false;body.set_opening(0.)

func set_open(value:bool)->void:
    desired_open=value
    mouth.closing_hold=not value and shell_open>.00001
    mouth.set_open(value)

func music_request()->void:
    desired_open=true;mouth.closing_hold=false

func set_pressed(value:bool)->void:
    if value:desired_open=true;mouth.closing_hold=false
    mouth.set_pressed(value)

func tick(delta:float)->void:
    var dt:=maxf(0.,delta)
    if desired_open:
        shell_open=move_toward(shell_open,1.,dt/shell_duration)
        mouth.closing_hold=false
    else:
        var quiet:bool=mouth.acoustics.ready_to_close() and mouth.suspension.settled()
        var score_closed:bool=music==null or not (music.engaged() or music.stopping)
        if quiet and score_closed:shell_open=move_toward(shell_open,0.,dt/shell_duration)
        mouth.closing_hold=shell_open>.00001
    body.set_opening(shell_open)
    if music:music.reveal_permitted=shell_open>.999
    stage="opening_shell" if desired_open and shell_open<.999 else "opening_mouth" if desired_open and mouth.openness<.999 else "ready" if desired_open else "unloading" if not (mouth.acoustics.ready_to_close() and mouth.suspension.settled()) else "closing_shell" if shell_open>.00001 else "closing_mouth" if mouth.openness>.00001 else "closed"

func snapshot()->Dictionary:
    return {"desired_open":desired_open,"shell_open":shell_open,"mouth_open":mouth.openness,"mouth_closing_held":mouth.closing_hold,"stage":stage}
