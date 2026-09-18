extends SceneTree
class MusicGate:
    extends Node
    var active:=false
    var stopping:=false
    var reveal_permitted:=true
    func engaged()->bool:return active
var sequence:RefCounted
var rig:RefCounted
var max_step:=0.
func _initialize()->void:run.call_deferred()
func advance(seconds:float)->void:
    for i in range(ceili(seconds*120.)):
        var before:float=sequence.shell_open
        sequence.tick(1./120.);rig.tick(1./120.)
        max_step=maxf(max_step,absf(sequence.shell_open-before))
        rig.drain_events()
        if not sequence.desired_open and sequence.shell_open>.00001:
            assert(rig.closing_hold,"Throat must stay held until the shells are seated")
func run()->void:
    var out:="res://../review/I_refinement/part_c_core/continuous_c3/"
    var body_spec:Dictionary=JSON.parse_string(FileAccess.get_file_as_string(out+"build.json"))
    var mouth_spec:Dictionary=JSON.parse_string(FileAccess.get_file_as_string("res://../"+str(body_spec.mouth_report)))
    var body_path:String="res://"+str(body_spec.component).trim_prefix("app/");var mouth_path:String="res://"+str(mouth_spec.component).trim_prefix("app/")
    assert(FileAccess.get_sha256(body_path)==body_spec.component_sha256 and FileAccess.get_sha256(mouth_path)==mouth_spec.component_sha256)
    var body:Node3D=load(body_path).instantiate();root.add_child(body)
    var mouth:Node3D=load(mouth_path).instantiate();root.add_child(mouth)
    var p:Array=body_spec.mouth_placement.p;var q:Array=body_spec.mouth_placement.q;var scale:Array=body_spec.mouth_placement.s
    mouth.transform=Transform3D(Basis(Quaternion(q[0],q[1],q[2],q[3])).scaled(Vector3(scale[0],scale[1],scale[2])),Vector3(p[0],p[1],p[2]))
    var driver=load("res://collection/i_shell_linkage_b3_driver.gd").new();driver.bind(body,body_spec)
    rig=load("res://collection/i_mouth_response_rig.gd").new();rig.bind(mouth,mouth_spec,JSON.parse_string(FileAccess.get_file_as_string(str(mouth_spec.aperture_profile))))
    var music:=MusicGate.new();root.add_child(music)
    sequence=load("res://review/i_conch_sequence.gd").new();sequence.bind(driver,rig,music)
    var records:Array=[]
    sequence.set_open(true);advance(5.);assert(sequence.shell_open>.999 and rig.openness>.999);records.append({"case":"opened","state":sequence.snapshot()})
    music.active=true;sequence.set_open(false);advance(.8)
    assert(sequence.shell_open>.999 and rig.openness>.999);records.append({"case":"wait_for_score_fade","state":sequence.snapshot()})
    music.active=false;advance(1.2);assert(sequence.shell_open<.8 and sequence.shell_open>.6 and rig.openness>.999)
    var partial:float=sequence.shell_open;sequence.set_open(true);advance(.7);assert(sequence.shell_open>partial and rig.openness>.999);records.append({"case":"reverse_close","state":sequence.snapshot()})
    sequence.set_open(false)
    while sequence.shell_open>.00001:
        advance(1./120.)
        if sequence.shell_open>.00001:assert(rig.openness>.999,"Throat closed before shell")
    assert(rig.openness>.98);records.append({"case":"shell_seated_before_throat","state":sequence.snapshot()})
    advance(2.8);assert(rig.openness<.00001);records.append({"case":"closed","state":sequence.snapshot()})
    var outgoing:int=rig.acoustics.outgoing_count
    sequence.set_pressed(true);advance(.8);sequence.set_open(false);advance(3.)
    assert(not rig.user_pressed and rig.acoustics.return_schedule().is_empty() and rig.acoustics.outgoing_count==outgoing)
    assert(sequence.shell_open<.00001 and rig.openness<.00001);records.append({"case":"cancel_charge","state":sequence.snapshot()})
    sequence.music_request();rig.set_open(false);rig.set_open(true);advance(1.)
    assert(not music.reveal_permitted);advance(3.3);assert(music.reveal_permitted);records.append({"case":"score_reveal_gate","state":sequence.snapshot()})
    assert(max_step<=1./120./4.2+.00001)
    var scripts:Dictionary={}
    for path in ["res://review/i_conch_sequence.gd","res://collection/i_mouth_response_rig.gd","res://collection/i_moonlight_controller.gd","res://collection/i_shell_linkage_b3_driver.gd"]:scripts[path]=FileAccess.get_sha256(path)
    FileAccess.open(out+"sequence_qa.json",FileAccess.WRITE).store_string(JSON.stringify({"source_sha256":body_spec.source_sha256,"component_sha256":body_spec.component_sha256,"mouth_component_sha256":mouth_spec.component_sha256,"passed":true,"scripts":scripts,"maximum_shell_progress_step":max_step,"cases":records,"scope":"Actual A/B mechanisms with deterministic coordination: score-close gate, shell-before-throat closing, reversals, cancelled charge and reveal-permission timing. Music gate is a test double; actual score/audio/native interaction still need integrated verification."},"  "))
    print("I_CONCH_SEQUENCE_QA true");body.queue_free();mouth.queue_free();music.queue_free();await process_frame;quit()
