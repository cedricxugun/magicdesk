extends SceneTree
func _initialize()->void:run.call_deferred()
func run()->void:
    RenderingServer.set_render_loop_enabled(false)
    root.size=Vector2i(1040,940)
    RenderingServer.viewport_set_update_mode(root.get_viewport_rid(),RenderingServer.VIEWPORT_UPDATE_ALWAYS)
    var world:=Node3D.new();root.add_child(world)
    var mesh:=MeshInstance3D.new();mesh.mesh=SphereMesh.new();world.add_child(mesh)
    var camera:=Camera3D.new();world.add_child(camera);camera.position=Vector3(0,0,3)
    var light:=DirectionalLight3D.new();world.add_child(light);light.rotation_degrees=Vector3(-30,-30,0)
    var frames:=0
    for i in range(120):
        await process_frame
        if i==3:
            root.mode=Window.MODE_MINIMIZED
            RenderingServer.viewport_set_update_mode(root.get_viewport_rid(),RenderingServer.VIEWPORT_UPDATE_ALWAYS)
        mesh.position.x=sin(float(i)*.1)*.4
        RenderingServer.force_draw(false,1./30.)
        var capture:=root.get_texture().get_image();assert(not capture.is_empty())
        if i==119:capture.save_png("res://../review/I_refinement/nautilus_r1/chamber_motion_r36/force_render_hidden_probe.png")
        frames+=1
        if i%10==0:print("FORCE_DRAW_PROBE ",i," can_draw=",DisplayServer.window_can_draw()," size=",capture.get_size())
    print("FORCE_DRAW_PROBE_COMPLETE ",frames);quit()
