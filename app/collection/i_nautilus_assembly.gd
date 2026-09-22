extends Node3D
## Current upper assembly only; the host owns its base, camera and controls.
var body_asset:Node3D
var mouth_asset:Node3D
var body_driver:RefCounted
var rig:RefCounted
var music:Node
var echo:Node3D
var chambers:RefCounted
var sequence:RefCounted
var finish_receipt:Dictionary={}
var disposed:=false
var status:Dictionary={}
func setup(spec:Dictionary)->void:
    var body_path:String="res://"+str(spec.component).trim_prefix("app/")
    var mouth_path:String="res://"+str(spec.mouth_component).trim_prefix("app/")
    assert(FileAccess.get_sha256(body_path)==spec.component_sha256)
    assert(FileAccess.get_sha256(mouth_path)==spec.mouth_component_sha256)
    body_asset=load(body_path).instantiate();add_child(body_asset)
    mouth_asset=load(mouth_path).instantiate();add_child(mouth_asset)
    var p:Array=spec.mouth_placement.p;var q:Array=spec.mouth_placement.q;var scale_values:Array=spec.mouth_placement.s
    mouth_asset.transform=Transform3D(Basis(Quaternion(q[0],q[1],q[2],q[3])).scaled(Vector3(scale_values[0],scale_values[1],scale_values[2])),Vector3(p[0],p[1],p[2]))
    finish_receipt=load("res://collection/i_finish_r38.gd").apply(body_asset,str(spec.finish_profile))
    body_driver=load("res://collection/i_nautilus_form_driver.gd").new();body_driver.bind(body_asset,spec)
    var mouth_spec:Dictionary=spec.mouth_spec.duplicate(true) if spec.has("mouth_spec") else JSON.parse_string(FileAccess.get_file_as_string("res://../"+str(spec.mouth_report)))
    assert(mouth_spec.component_sha256==spec.mouth_component_sha256)
    mouth_spec["music_optics_layout"]=spec.music_optics_layout;mouth_spec["music_manifest"]=spec.music_manifest
    rig=load("res://collection/i_mouth_response_rig.gd").new()
    rig.bind(mouth_asset,mouth_spec,JSON.parse_string(FileAccess.get_file_as_string(str(mouth_spec.aperture_profile))))
    echo=load("res://collection/i_echo_presentation.gd").new();add_child(echo);echo.setup(mouth_asset,true,2.)
    music=load("res://collection/i_moonlight_controller.gd").new();add_child(music);music.setup(mouth_asset,mouth_spec,rig,echo)
    chambers=load("res://collection/i_chamber_music_response.gd").new();chambers.bind(body_asset,spec)
    sequence=load("res://collection/i_nautilus_sequence.gd").new();sequence.bind(body_driver,rig,music)
    status={"source_sha256":spec.source_sha256,"component_sha256":spec.component_sha256,"mouth_component_sha256":spec.mouth_component_sha256}
func tick(delta:float)->void:
    if disposed:return
    sequence.tick(delta)
    music.transport._process(0.)
    music.tick(delta);rig.tick(delta)
    echo.update(delta,rig,rig.drain_events())
    var chamber_clock:float=music.transport.position_seconds() if chambers.wants_work_clock() else music.transport.local_clock
    chambers.update(music.transport.chamber_bands(),chamber_clock,music.transport.state=="playing",sequence.shell_open,delta)
    status["sequence"]=sequence.snapshot();status["music"]=music.status.duplicate(true);status["chambers"]=chambers.status.duplicate(true)
func shutdown()->void:
    if disposed:return
    disposed=true
    music.transport.stop()
    for voice in echo.voices:
        if is_instance_valid(voice):voice.stop()
    rig.set_open(false);chambers.release()
    # Let the live audio mix release playback references before tree teardown.
    await get_tree().create_timer(.20).timeout
    queue_free()
