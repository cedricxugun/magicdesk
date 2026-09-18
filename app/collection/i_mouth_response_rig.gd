extends RefCounted
## One reversible mechanical timeline for the current three-tongue mouth.
var tongues:RefCounted
var suspension:RefCounted
var acoustics:RefCounted
var openness:=0.
var wants_open:=false
var user_pressed:=false
var release_waiting:=false
var stage:="closed"
var last_event:=""
var event_age:=100.
var events:Array=[]
var receipts:Array=[]
var music_level:=0.
var _closing:=false
var closing_hold:=false
func bind(asset:Node3D,spec:Dictionary,aperture:Dictionary)->void:
    tongues=load("res://collection/i_tongue_set_driver.gd").new();tongues.bind(asset,spec);receipts=tongues.receipts
    suspension=load("res://collection/i_diaphragm_response.gd").new();suspension.bind(asset,spec.diaphragm)
    acoustics=load("res://collection/i_acoustics.gd").new();acoustics.bind_measured_aperture(aperture,str(spec.component_sha256));acoustics.set_controls(.8,1.)
    acoustics.return_delay_override=1.35
    acoustics.set_driven_opening(0.)
func set_open(value:bool)->void:
    wants_open=value
    if value:
        _closing=false;acoustics.start();suspension.resume()
    else:
        _closing=true;user_pressed=false;release_waiting=false
        music_level=0.
        acoustics.quiet();acoustics.drain_events();suspension.quiet();events.clear();last_event="";event_age=100.
func set_pressed(value:bool)->void:
    if value==user_pressed:return
    user_pressed=value
    if value:
        set_open(true);release_waiting=false;acoustics.set_pressed(true)
    else:
        # Hold reservoir pressure until the physical shutters reach the release
        # pose. A separate fast iris animation must not outrun the real model.
        release_waiting=acoustics.pressed
func set_music_level(value:float)->void:
    music_level=clampf(value,0.,1.) if wants_open else 0.
func tick(delta:float)->void:
    var remaining:=maxf(0.,delta)
    while remaining>.0000001:
        var step:=minf(remaining,1./120.);remaining-=step;event_age+=step
        var target:=0. if user_pressed else 1.
        if not wants_open:
            target=0. if acoustics.ready_to_close() and suspension.settled() and not closing_hold else openness
        openness=move_toward(openness,target,step/2.6)
        acoustics.set_driven_opening(openness)
        if release_waiting and wants_open and openness>=.28:
            acoustics.set_pressed(false);release_waiting=false
        acoustics.tick(step)
        if wants_open:suspension.set_load(maxf(acoustics.compression,music_level*.5))
        for event in acoustics.drain_events():
            if not wants_open:continue
            var strength:float=clampf(float(event.gain),0.,1.)
            suspension.impulse(strength*(1. if str(event.kind)=="outgoing" else .6))
            events.append({"kind":event.kind,"time":event.time,"gain":strength,"opening":openness,"frequency_hz":event.frequency_hz})
            last_event=str(event.kind);event_age=0.
        suspension.tick(step)
    tongues.set_opening(openness)
    stage="charging" if user_pressed else "release_wait" if release_waiting else "echo" if last_event=="return" and event_age<.7 else "outgoing" if last_event=="outgoing" and event_age<.5 else "recovering" if _closing and not (acoustics.ready_to_close() and suspension.settled()) else "closing" if not wants_open and openness>.0001 else "closed" if not wants_open else "opening" if openness<.9999 else "listening"
func drain_events()->Array:
    var result:=events;events=[];return result
func state()->Dictionary:
    return {"stage":stage,"opening":openness,"wants_open":wants_open,"pressed":user_pressed,"release_waiting":release_waiting,"actual_acoustic_opening":acoustics.iris,"pressure":acoustics.pressure,"music_level":music_level,"stroke":suspension.displacement,"stroke_velocity":suspension.velocity,"suspension_settled":suspension.settled(),"pending_returns":acoustics.return_schedule().size(),"outgoing":acoustics.outgoing_count,"returns":acoustics.echo_count}
