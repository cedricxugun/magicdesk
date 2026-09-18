extends SceneTree
var world:Node3D
func _initialize()->void:run.call_deferred()
func opening_at(t:float)->float:
    var keys:Array=[[0.,0.],[.7,0.],[2.,1.],[3.2,1.],[4.4,0.],[5.2,0.],[6.,.6],[6.8,.1],[8.,1.],[9.,1.],[10.6,0.],[12.,0.]]
    for i in range(keys.size()-1):
        if t<=keys[i+1][0]:
            var f:=smoothstep(float(keys[i][0]),float(keys[i+1][0]),t)
            return lerpf(keys[i][1],keys[i+1][1],f)
    return 0.
func run()->void:
    var folder:="res://../review/I_refinement/nautilus_r1/hinge_r1/"
    var panel_number:=4
    var whole:=false
    var coupled_mouth:=false
    var music_review:=false
    var pause_test:=false
    var presentation_seconds:=60
    var detail_cell:=0
    var trace_frames:=false
    var diagnostic_no_spill:=false
    var capture_visible:=false
    var force_capture:=OS.has_feature("movie")
    for arg in OS.get_cmdline_user_args():
        if arg.begins_with("--report="):folder=arg.trim_prefix("--report=").get_base_dir()+"/"
        elif arg.begins_with("--panel="):panel_number=arg.trim_prefix("--panel=").to_int()
        elif arg=="--whole":whole=true
        elif arg=="--coupled-mouth":coupled_mouth=true
        elif arg=="--music-review":music_review=true;whole=true;coupled_mouth=true
        elif arg=="--test-pause-resume":pause_test=true;music_review=true;whole=true;coupled_mouth=true
        elif arg.begins_with("--presentation-seconds="):presentation_seconds=arg.trim_prefix("--presentation-seconds=").to_int();assert(presentation_seconds>=2 and presentation_seconds<=300)
        elif arg.begins_with("--detail-cell="):detail_cell=arg.trim_prefix("--detail-cell=").to_int()
        elif arg=="--trace-frames":trace_frames=true
        elif arg=="--diagnostic-no-spill":diagnostic_no_spill=true
        elif arg=="--capture-visible":capture_visible=true
        elif arg=="--force-capture":force_capture=true
        elif arg=="--diagnostic-auto-render":force_capture=false
    var spec:Dictionary=JSON.parse_string(FileAccess.get_file_as_string(folder+"build.json"))
    var out:=folder+"take_"+str(spec.source_sha256).substr(0,8)+"/"
    for arg in OS.get_cmdline_user_args():
        if arg.begins_with("--take-out="):out=arg.trim_prefix("--take-out=").trim_suffix("/")+"/"
    DirAccess.make_dir_recursive_absolute(out)
    root.size=Vector2i(1040,1040) if whole and not force_capture else Vector2i(1040,940);root.transparent_bg=false;root.msaa_3d=Viewport.MSAA_4X
    if force_capture:
        RenderingServer.set_render_loop_enabled(false)
        RenderingServer.viewport_set_update_mode(root.get_viewport_rid(),RenderingServer.VIEWPORT_UPDATE_ALWAYS)
    if capture_visible:root.always_on_top=true
    if trace_frames:
        var observer:=Timer.new();root.add_child(observer);observer.wait_time=1.
        observer.timeout.connect(func():print("TAKE_WINDOW process=",Engine.get_process_frames()," drawn=",Engine.get_frames_drawn()," can_draw=",DisplayServer.window_can_draw()," visible=",root.visible," low_cpu=",OS.low_processor_usage_mode));observer.start()
    world=Node3D.new();root.add_child(world)
    var env:=Environment.new();env.background_mode=Environment.BG_COLOR;env.background_color=Color(.035,.033,.030)
    var panorama:=PanoramaSkyMaterial.new();panorama.panorama=load("res://assets/studio_small_09_4k.exr");panorama.energy_multiplier=.20
    var sky:=Sky.new();sky.sky_material=panorama;env.sky=sky;env.ambient_light_source=Environment.AMBIENT_SOURCE_SKY;env.ambient_light_energy=.35;env.reflected_light_source=Environment.REFLECTION_SOURCE_SKY;env.tonemap_mode=Environment.TONE_MAPPER_AGX
    env.ssao_enabled=true;env.ssao_radius=.08;env.ssao_intensity=.55;env.glow_enabled=false
    if spec.get("optical_glow",false):load("res://collection/i_optical_finish_r40.gd").apply(env)
    var environment:=WorldEnvironment.new();environment.environment=env;world.add_child(environment)
    for row in [[Vector3(-3,5,4),8.,Color(1.,.91,.80)],[Vector3(4,3,1),4.,Color(.84,.91,1.)],[Vector3(-2,4,-4),5.,Color(1.,.95,.86)]]:
        var light:=AreaLight3D.new();world.add_child(light);light.position=row[0];light.look_at(Vector3(0,1.8,0));light.light_energy=row[1];light.light_color=row[2];light.area_size=Vector2(2.5,3.);light.area_normalize_energy=true;light.area_range=12.;light.shadow_enabled=true;light.light_size=.25
    var path:String="res://"+str(spec.component).trim_prefix("app/");assert(FileAccess.get_sha256(path)==spec.component_sha256)
    var asset:Node3D=load(path).instantiate();world.add_child(asset)
    var finish_record:Dictionary={}
    if spec.has("finish_profile"):finish_record=load("res://collection/i_finish_r38.gd").apply(asset,str(spec.finish_profile))
    var driver=load("res://collection/i_nautilus_form_driver.gd").new();driver.bind(asset,spec)
    var chamber_response:Variant=null
    if music_review and spec.has("chamber_response_layout"):
        chamber_response=load("res://collection/i_chamber_music_response.gd").new();chamber_response.bind(asset,spec)
        if diagnostic_no_spill:
            for binding in chamber_response.bindings:
                if binding.light!=null:binding.light.hide()
    var chosen:Dictionary=spec.real_cassettes.filter(func(m):return int(m.panel_number)==panel_number)[0]
    var frame:Node3D=asset.find_child(str(chosen.frame),true,false)
    var target:Vector3=frame.global_position-frame.global_basis.z*.055-frame.global_basis.y*.08
    var camera:=Camera3D.new();world.add_child(camera);camera.fov=32.;camera.near=.02
    camera.position=target-frame.global_basis.z*.60+frame.global_basis.x*.70+frame.global_basis.y*.45;camera.look_at(target,-frame.global_basis.x)
    var plan_path:String=folder+"cassette_review_cameras.json"
    if FileAccess.file_exists(plan_path):
        var plan:Dictionary=JSON.parse_string(FileAccess.get_file_as_string(plan_path));assert(plan.source_sha256==spec.source_sha256);var row:Dictionary=plan.cameras.filter(func(c):return int(c.panel_number)==panel_number)[0];var eye:Array=row.eye;var aim:Array=row.target;var up:Array=row.up;camera.position=Vector3(eye[0],eye[1],eye[2]);camera.fov=row.fov;camera.look_at(Vector3(aim[0],aim[1],aim[2]),Vector3(up[0],up[1],up[2]))
    var mouth_driver:Variant=null
    var staff:Variant=null
    var transport:Variant=null
    if whole:
        var donor:Node3D=load("res://assets/helios_model.glb").instantiate();world.add_child(donor);var base:=donor.find_child("BASE_FIXED",true,false);base.reparent(world,true);donor.queue_free()
        var mouth:Node3D=load("res://"+str(spec.mouth_component).trim_prefix("app/")).instantiate();world.add_child(mouth);var p:Array=spec.mouth_placement.p;var q:Array=spec.mouth_placement.q;var scale_values:Array=spec.mouth_placement.s;mouth.transform=Transform3D(Basis(Quaternion(q[0],q[1],q[2],q[3])).scaled(Vector3(scale_values[0],scale_values[1],scale_values[2])),Vector3(p[0],p[1],p[2]));var mouth_spec:Dictionary=JSON.parse_string(FileAccess.get_file_as_string("res://../"+str(spec.mouth_report)));mouth_driver=load("res://collection/i_tongue_set_driver.gd").new();mouth_driver.bind(mouth,mouth_spec);mouth_driver.set_opening(1.)
        camera.fov=32.;camera.position=Vector3(-3,3.55,7.70);camera.look_at(Vector3(0,1.66,0))
        if music_review:
            staff=load("res://collection/i_moonlight_staff.gd").new();world.add_child(staff);staff.setup(mouth,str(spec.mouth_component_sha256),str(spec.music_optics_layout))
            transport=load("res://collection/i_music_transport.gd").new();world.add_child(transport);transport.setup(str(spec.get("music_manifest","res://assets/collection/art/I/moonlight_candidate/manifest.json")))
            transport.offline_capture_clock=OS.has_feature("movie")
        if detail_cell>0:
            var film:=asset.find_child("IN1_CellDiaphragm_%02d"%detail_cell,true,false)as MeshInstance3D;assert(film!=null)
            var aim:Vector3=film.global_transform*film.get_aabb().get_center();camera.position=aim+Vector3(-.35,.24,.91).normalized()*2.8;camera.look_at(aim);camera.fov=34.
    var overlay:=CanvasLayer.new();root.add_child(overlay);var label:=Label.new();overlay.add_child(label);label.position=Vector2(24,22);label.add_theme_font_size_override("font_size",19)
    var font:=SystemFont.new();font.font_names=PackedStringArray(["PingFang SC","Arial"]);label.add_theme_font_override("font",font)
    label.text=("口部与上盖组合开合检查" if coupled_mouth else "三片上盖机构检查 · 喉闸保持开启") if whole else "机械鹦鹉螺 · %02d号导向与转轴检查"%panel_number
    if music_review:label.text="月光第一乐章 · 连续播放" if not pause_test else "功能测试 · 暂停 / 恢复 / 收回"
    if detail_cell>0:label.text="声学腔膜片局部 · 原始行程 · 月光响应"
    var samples:Array=[]
    var frame_count:=(750 if pause_test else (presentation_seconds+3)*30) if music_review else 360
    var held_quarter:=0.
    if force_capture:RenderingServer.force_draw(false,0.)
    var first_rendered_frame:=Engine.get_frames_drawn()
    for f in range(frame_count):
        # Update animation during scene processing. Movie frames are explicitly
        # drawn below so capture does not depend on window draw availability.
        await process_frame
        if trace_frames:print("TAKE_TRACE ",f," begin ",Time.get_ticks_msec())
        var opening:=opening_at(float(f)/30.)
        if music_review:opening=smoothstep(0.,60.,float(f))*(1.-smoothstep(660.,735.,float(f)) if pause_test else 1.)
        var cover_opening:=clampf((opening-.2)/.8,0.,1.) if coupled_mouth else opening
        var mouth_opening:=clampf(opening/.2,0.,1.) if coupled_mouth else 1.
        driver.set_opening(cover_opening)
        if whole and coupled_mouth:mouth_driver.set_opening(mouth_opening)
        if trace_frames:print("TAKE_TRACE ",f," geometry_updated ",Time.get_ticks_msec())
        if music_review:
            if f==90:
                transport.play_complete()
                if pause_test:transport.seek_total(4.15)
            if pause_test:
                if f==450:transport.pause()
                elif f==510:transport.resume()
                elif f==600:transport.pause()
                elif f==660:transport.stop()
            if not pause_test or f<660:held_quarter=transport.score_quarter_estimate()
            var reveal:=smoothstep(60.,90.,float(f))*(1.-smoothstep(600.,660.,float(f)) if pause_test else 1.)
            staff.set_score_position(transport.index+1,held_quarter,reveal);staff.set_music_response(transport.response_level(),transport.state=="playing",f>=90)
            if chamber_response!=null:chamber_response.update(transport.chamber_bands(),transport.local_clock,transport.state=="playing",cover_opening,1./30.)
        if trace_frames:print("TAKE_TRACE ",f," await_draw ",Time.get_ticks_msec())
        if force_capture:RenderingServer.force_draw(false,1./30.)
        else:await RenderingServer.frame_post_draw
        if trace_frames:print("TAKE_TRACE ",f," drawn ",Time.get_ticks_msec())
        if f%10==0:
            var sample:Dictionary={"frame":f,"engine_rendered_frame":Engine.get_frames_drawn(),"forced_draw_calls":f+1 if force_capture else 0,"window_can_draw":DisplayServer.window_can_draw(),"opening":opening,"cover_opening":cover_opening,"mouth_opening":mouth_opening}
            if music_review:sample["music"]=transport.snapshot();sample["staff"]=staff.status.duplicate(true)
            if chamber_response!=null:sample["chambers"]=chamber_response.status.duplicate(true)
            samples.append(sample)
        if f in [0,60,180,210,270,359,450,510,630,749] or f==frame_count-1:root.get_texture().get_image().save_png(out+"frame_%03d.png"%f)
        if trace_frames:print("TAKE_TRACE ",f," saved ",Time.get_ticks_msec())
    if not music_review or pause_test:driver.set_opening(0.)
    var scope:="Fixed-camera actual renderer with continuous cover input and mid-motion reversal. Coupled mode opens A before lifting covers and closes covers before A; otherwise A is held open. No complete music performance, native clicking, final drive/art or App acceptance."
    if music_review:
        if pause_test:
            assert(transport.state=="stopped"and not staff.sheet.visible)
            scope="Explicit pause/resume/closure functional test, first-movement excerpt from 4.15 seconds. Not a normal playback presentation or full-work/native/art acceptance."
        else:
            assert(transport.state=="playing"and staff.sheet.visible)
            scope="Continuous first-movement presentation from recording start: no artificial pause, seek, stop or closure. The declared presentation ends while the device is still playing; recorder cleanup tail is excluded at export. Not full-work playback, all-note synchronization or native/art acceptance."
    FileAccess.open(out+"take.json",FileAccess.WRITE).store_string(JSON.stringify({"source_sha256":spec.source_sha256,"component_sha256":spec.component_sha256,"finish_profile":finish_record,"music_optics_layout":spec.get("music_optics_layout",""),"frames":frame_count,"fps":30,"recorder_cleanup_tail":music_review and not pause_test,"capture_mode":("pause_resume_test" if pause_test else "continuous_music") if music_review else "mechanism","source_start_seconds":4.15 if pause_test else 0.,"force_capture":force_capture,"capture_size":[root.size.x,root.size.y],"first_engine_rendered_frame":first_rendered_frame,"last_engine_rendered_frame":Engine.get_frames_drawn(),"samples":samples,"whole_assembly":whole,"coupled_mouth":coupled_mouth,"music_review":music_review,"diagnostic_no_spill":diagnostic_no_spill,"detail_cell":detail_cell,"panel_number":panel_number,"scope":scope},"  "))
    if music_review and not pause_test:
        # Let the last presentation frame reach MovieWriter before stopping.
        # Export only the declared frames via export_i_presentation.py; these
        # extra cleanup frames are outside the user-facing continuous clip.
        await process_frame
        transport.stop()
        for cleanup_frame in range(8):
            await process_frame
            if force_capture:RenderingServer.force_draw(false,1./30.)
    print("NAUTILUS_MECHANISM_TAKE_FINISHED");quit()
