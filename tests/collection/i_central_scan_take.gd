extends SceneTree
var viewer:Node3D
var samples:Array=[]
func _initialize()->void:run.call_deferred()
func run()->void:
    viewer=load("res://review/i_mouth_viewer.tscn").instantiate();root.add_child(viewer)
    viewer.yaw=.20;viewer.pitch=.08;viewer.distance=3.55;viewer.update_camera()
    # Start the excerpt with the mouth already open; only the music reveal is shown.
    viewer.response_rig.set_open(true)
    for i in range(260):viewer.response_rig.tick(1./60.)
    viewer.moonlight.toggle();viewer.target=1.
    var moved:=false
    var out:="res://../review/I_refinement/moonlight/central_scan_r1/take_r1/"
    for arg in OS.get_cmdline_user_args():
        if arg.begins_with("--take-out="):out=arg.trim_prefix("--take-out=").trim_suffix("/")+"/"
    DirAccess.make_dir_recursive_absolute(out)
    for frame in range(1320):
        if not moved and viewer.moonlight.transport.state=="playing":
            viewer.moonlight.seek(4.15);moved=true
        if frame==960:viewer.moonlight.toggle()
        if frame==1080:viewer.moonlight.stop(true)
        await RenderingServer.frame_post_draw
        if frame%60==0:
            samples.append({"frame":frame,"music":viewer.moonlight.status.duplicate(true)})
        if frame in [90,480,900,1020,1300]:root.get_texture().get_image().save_png(out+"frame_%04d.png"%frame)
    assert(moved and viewer.moonlight.transport.state=="stopped")
    FileAccess.open(out+"take.json",FileAccess.WRITE).store_string(JSON.stringify({"samples":samples,"frames":1320,"fps":60,"scope":"Actual renderer/audio transport excerpt of central scan on preserved A mouth. Seek past recording intro, then play/pause/stop. Not the new whole-nautilus model or all-note synchronization acceptance."},"  "))
    viewer.queue_free();await process_frame;print("I_CENTRAL_SCAN_TAKE_FINISHED");quit()
