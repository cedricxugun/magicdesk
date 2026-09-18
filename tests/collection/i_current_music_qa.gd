extends SceneTree
var rig:RefCounted
var music:Node
func _initialize()->void:run.call_deferred()
func advance(frames:int)->void:
    for frame in range(frames):
        rig.tick(1./60.);music.tick(1./60.);await process_frame
func run()->void:
    var report_path:="res://../review/I_refinement/part_a_mouth/shutter_r2/diaphragm/build.json"
    var output_path:="res://../review/I_refinement/moonlight/current_mouth/controller_qa.json"
    for argument in OS.get_cmdline_user_args():
        if argument.begins_with("--report="):
            report_path=argument.trim_prefix("--report=");output_path=report_path.get_base_dir()+"/controller_qa.json"
    var spec:Dictionary=JSON.parse_string(FileAccess.get_file_as_string(report_path))
    var aperture:Dictionary=JSON.parse_string(FileAccess.get_file_as_string(str(spec.get("aperture_profile","res://assets/collection/art/I/diaphragm/aperture_profile.json"))))
    var asset:Node3D=load("res://"+str(spec.component).trim_prefix("app/")).instantiate();root.add_child(asset)
    rig=load("res://collection/i_mouth_response_rig.gd").new();rig.bind(asset,spec,aperture)
    for group in spec.tongues:
        for name in group.mesh_names:
            var foil:=asset.find_child(name,true,false) as MeshInstance3D
            if foil.mesh.get_surface_count()!=1 or foil.mesh.surface_get_array_len(0)<10000:
                push_error("Current mouth has missing foil geometry: "+str(name));quit(1);return
    var echo=load("res://collection/i_echo_presentation.gd").new();root.add_child(echo);echo.setup(asset,false)
    music=load("res://collection/i_moonlight_controller.gd").new();root.add_child(music);music.setup(asset,spec,rig,echo)
    rig.set_pressed(true);rig.tick(.2)
    music.toggle();await advance(30);assert(music.start_pending and music.transport.state=="stopped" and not rig.user_pressed)
    await advance(210);assert(music.transport.state=="playing" and music.reveal>.99 and echo._music_mode)
    var camera:=Camera3D.new();root.add_child(camera);camera.position=Vector3(-1.,-3.4,-.6);camera.look_at(Vector3(0,.03,0),Vector3.FORWARD);camera.current=true
    var sheet_world:Vector3=music.staff.sheet.global_transform*Vector3(0,-.225,-float(music.staff.layout.center_y))
    var sheet_screen:=camera.unproject_position(sheet_world)
    assert(music.staff.pointer_target(camera,sheet_screen)=="staff")
    var emitter:Node3D=music.staff.emitter_centers[0]
    assert(music.staff.pointer_target(camera,camera.unproject_position(emitter.global_position))=="emitter")
    camera.position=Vector3(0,3.4,0);camera.look_at(Vector3.ZERO,Vector3.FORWARD)
    assert(music.staff.pointer_target(camera,camera.unproject_position(emitter.global_position))=="","Rear view must not click through the mouth")
    camera.queue_free()
    await create_timer(.15).timeout;music.toggle();music.tick(0.)
    var paused:Dictionary=music.transport.snapshot();var staff:Dictionary=music.staff.status.duplicate(true)
    await create_timer(.15).timeout;music.tick(.1)
    assert(music.transport.state=="paused" and is_equal_approx(music.transport.position_seconds(),paused.total_seconds))
    assert(is_equal_approx(music.staff.status.quarter_estimate,staff.quarter_estimate))
    await advance(180)
    assert(rig.suspension.settled() and rig.music_level==0.,"Paused music must gently settle its membrane")
    var samples:Array=[]
    for time in [20.,350.,490.,920.]:
        music.seek(time);await advance(12)
        assert(music.transport.state=="paused" and absf(music.transport.position_seconds()-time)<.002)
        assert(music.staff.status.ready and music.staff.status.movement==music.transport.index+1)
        assert(music.staff.cache.size()<=4)
        samples.append(music.status.duplicate(true))
    music.toggle();assert(music.transport.state=="playing")
    music.tick(1./60.);rig.tick(1./60.)
    assert(rig.music_level>0. and is_equal_approx(rig.music_level,music.transport.response_level()))
    music.stop();music.transport.work_finished.emit()
    assert(not music.active and music.stopping,"A late natural-end event must not resurrect music")
    music.toggle()
    assert(music.start_pending and music.transport.state=="stopped" and is_zero_approx(music.transport.position_seconds()),"Restart during fade must discard the old transport position")
    await advance(60);assert(music.transport.state=="playing")
    music.stop(true);assert(music.engaged() and rig.wants_open)
    await advance(50);assert(not music.engaged() and music.transport.state=="stopped" and not echo._music_mode and not rig.wants_open)
    await advance(240);assert(rig.stage=="closed" and rig.music_level==0. and rig.suspension.settled())
    FileAccess.open(output_path,FileAccess.WRITE).store_string(JSON.stringify({"source_sha256":spec.source_sha256,"component_sha256":spec.component_sha256,"optics_sha256":music.staff.layout.component_sha256,"passed":true,"samples":samples,"scope":"Current IAM optics, full three-track transport, ready-before-play, paused score stability, three-movement seeks, tile cache bounds, music cue suppression and fade-before-close. Dummy audio; fine musical alignment/native/audio quality not accepted."},"  "))
    print("I_CURRENT_MUSIC_QA true");music.queue_free();echo.queue_free();asset.queue_free();await process_frame;quit()
