extends SceneTree
var viewer:Node3D
var out:="res://../review/I_refinement/part_c_core/continuous_c3/viewer_integration/"
var cases:Array=[]
func _initialize()->void:run.call_deferred()
func click(position:Vector2)->void:
    var event:=InputEventMouseButton.new();event.button_index=MOUSE_BUTTON_LEFT;event.position=position;event.pressed=true;viewer._input(event)
    event=event.duplicate();event.pressed=false;viewer._input(event)
func capture(name:String)->void:
    await RenderingServer.frame_post_draw
    root.get_texture().get_image().save_png(out+name+".png")
    cases.append({"name":name,"sequence":viewer.sequence.snapshot(),"music":viewer.moonlight.status.duplicate(true),"action":viewer.last_action})
func run()->void:
    DirAccess.make_dir_recursive_absolute(out)
    viewer=load("res://review/i_mouth_viewer.tscn").instantiate();root.add_child(viewer)
    await process_frame;assert(viewer.body_mode and viewer.sequence!=null)
    await capture("closed_start")
    var emitter:Node3D=viewer.moonlight.staff.emitter_centers[0]
    var projector:Vector2=viewer.camera.unproject_position(emitter.global_position)
    assert(viewer.moonlight.staff.pointer_target(viewer.camera,projector)=="emitter")
    click(projector);await create_timer(.45).timeout
    assert(viewer.moonlight.start_pending and viewer.moonlight.transport.state=="stopped" and not viewer.moonlight.reveal_permitted)
    await capture("opening_before_score")
    await create_timer(4.8).timeout
    assert(viewer.sequence.shell_open>.999 and viewer.openness>.999 and viewer.moonlight.transport.state=="playing" and viewer.moonlight.reveal>.99)
    await capture("moonlight_open")
    var sheet:Node3D=viewer.moonlight.staff.sheet
    var point:Vector3=sheet.global_transform*Vector3(0,-.225,-float(viewer.moonlight.staff.layout.center_y))
    var staff_screen:Vector2=viewer.camera.unproject_position(point)
    assert(viewer.moonlight.staff.pointer_target(viewer.camera,staff_screen)=="staff")
    click(staff_screen);await create_timer(.25).timeout;assert(viewer.moonlight.transport.state=="paused")
    var time:float=viewer.moonlight.transport.position_seconds();await create_timer(.25).timeout;assert(absf(viewer.moonlight.transport.position_seconds()-time)<.0001)
    await capture("paused_score")
    var mouth:Node3D=viewer.asset.find_child("IAM_Mouth",true,false)
    var rim:Vector2=viewer.camera.unproject_position(mouth.global_transform*Vector3(0,-.17,.74))
    assert(viewer.moonlight.staff.pointer_target(viewer.camera,rim).is_empty() and viewer.over_model(rim))
    click(rim);await create_timer(.20).timeout;assert(not viewer.sequence.desired_open and viewer.sequence.shell_open>.999)
    click(rim);await create_timer(.85).timeout
    assert(viewer.sequence.desired_open and viewer.sequence.shell_open>.999 and viewer.openness>.999)
    await capture("reverse_during_score_fade")
    click(rim);await create_timer(1.10).timeout
    assert(viewer.sequence.shell_open>.60 and viewer.sequence.shell_open<.85 and viewer.openness>.999)
    await capture("closing_shell_mouth_held")
    # Observe order directly: GPU readback/PNG writing can stall a rendered
    # frame, so fixed wall-time snapshots are not animation-duration evidence.
    var close_started:=Time.get_ticks_msec()
    while viewer.sequence.shell_open>.00001:
        await process_frame
        assert(Time.get_ticks_msec()-close_started<8000,"Shell close stalled")
        if viewer.sequence.shell_open>.00001:assert(viewer.openness>.999,"Throat closed before shell seated")
    assert(not viewer.response_rig.closing_hold)
    await capture("shell_closed_throat_closing")
    await create_timer(2.70).timeout
    assert(viewer.sequence.shell_open<.00001 and viewer.openness<.00001 and viewer.moonlight.transport.state=="stopped")
    await capture("closed_return")
    FileAccess.open(out+"check.json",FileAccess.WRITE).store_string(JSON.stringify({"source_sha256":viewer.body_spec.source_sha256,"component_sha256":viewer.body_spec.component_sha256,"mouth_component_sha256":viewer.spec.component_sha256,"passed":true,"cases":cases,"scope":"Actual Metal source viewer composition and projected pointer handling for score/music/open-close/reversal. Dummy audio and programmatic InputEvents; not native OS input, audible playback, final art or AAA acceptance."},"  "))
    print("I_CONCH_VIEWER_INTEGRATION true");viewer.queue_free();await process_frame;quit()
