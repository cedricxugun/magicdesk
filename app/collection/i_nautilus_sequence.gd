extends RefCounted
## Current three-cover mechanism: open throat first, stow score before covers.
var body:RefCounted
var mouth:RefCounted
var music:Node
var desired_open:=false
var shell_open:=0.
var shell_duration:=1.8
var stage:="closed"
func bind(body_driver:RefCounted,mouth_driver:RefCounted,music_controller:Node)->void:
    body=body_driver;mouth=mouth_driver;music=music_controller
    body.set_opening(0.);mouth.closing_hold=false
func set_open(value:bool)->void:
    desired_open=value
    if not value and music!=null:music.stop(false)
    mouth.closing_hold=not value and shell_open>.00001
    mouth.set_open(value)
func music_request()->void:
    desired_open=true;mouth.closing_hold=false
    if not mouth.wants_open:mouth.set_open(true)
func set_pressed(value:bool)->void:
    if value:desired_open=true;mouth.closing_hold=false
    mouth.set_pressed(value)
func tick(delta:float)->void:
    var dt:=maxf(0.,delta)
    if desired_open:
        # A deliberate pressure gesture may hold the throat closed while the
        # chamber is displayed. Once started, cover movement does not stall.
        if shell_open>.00001 or mouth.openness>.999 or mouth.user_pressed:
            shell_open=move_toward(shell_open,1.,dt/shell_duration)
        mouth.closing_hold=false
    else:
        var quiet:bool=mouth.acoustics.ready_to_close() and mouth.suspension.settled()
        var score_closed:bool=music==null or not (music.engaged() or music.stopping)
        if quiet and score_closed:shell_open=move_toward(shell_open,0.,dt/shell_duration)
        mouth.closing_hold=shell_open>.00001
    body.set_opening(shell_open)
    if music:music.reveal_permitted=desired_open and shell_open>.999
    stage="opening_mouth" if desired_open and shell_open<.00001 and mouth.openness<.999 else "opening_shell" if desired_open and shell_open<.999 else "ready" if desired_open else "unloading" if music!=null and (music.engaged() or music.stopping) else "closing_shell" if shell_open>.00001 else "closing_mouth" if mouth.openness>.00001 else "closed"
func snapshot()->Dictionary:
    return {"desired_open":desired_open,"shell_open":shell_open,"mouth_open":mouth.openness,"mouth_closing_held":mouth.closing_hold,"stage":stage}
