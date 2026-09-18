extends Node3D
var camera:Camera3D
var controller:RefCounted
var asset:Node3D
var spec:Dictionary
var openness:=0.
var target:=0.
var cycle:=false
var hold:=0.
var yaw:=.79
var pitch:=.224
var distance:=3.70
var down:=false
var dragged:=0.
var drag_last_position:=Vector2.ZERO
var drag_origin:=Vector2.ZERO
var pointer_debug:Dictionary={}
var echo_presentation:Node3D
var moonlight:Node
var status:Label
var diagnostics_path:=""
var report_timer:=0.
var input_count:=0
var last_action:="startup"
var inspect_center:=Vector3(0,.13,0)
var studio_receipt:Dictionary={}
var response_rig:RefCounted
var demo_charge_left:float=-1.
var body_mode:=false
var body_spec:Dictionary={}
var body_asset:Node3D
var body_driver:RefCounted
var sequence:RefCounted
var current_nautilus:=false
var assembly:Node3D
var quitting:=false
func _ready()->void:
    var window:=get_window();window.title="MagicDesk · 回声海螺喉口预览";window.transparent_bg=false
    var usable:=DisplayServer.screen_get_usable_rect(window.current_screen);var scale:=maxf(1.,DisplayServer.screen_get_scale(window.current_screen))
    window.size=Vector2i(minf(980.*scale,float(usable.size.x)*.90),minf(840.*scale,float(usable.size.y)*.90));window.position=usable.position+(usable.size-window.size)/2
    window.content_scale_size=Vector2i(980,840);window.content_scale_mode=Window.CONTENT_SCALE_MODE_CANVAS_ITEMS
    var review_config:="res://assets/collection/i_tongue_set_review.json"
    for arg in OS.get_cmdline_user_args():
        if arg.begins_with("--review-diagnostics="):diagnostics_path=arg.trim_prefix("--review-diagnostics=")
        elif arg.begins_with("--review-config="):review_config=arg.trim_prefix("--review-config=")
    spec=JSON.parse_string(FileAccess.get_file_as_string(review_config))
    current_nautilus=bool(spec.get("current_nautilus",false))
    if current_nautilus:
        window.transparent=false;window.transparent_bg=false;window.borderless=false
        get_tree().auto_accept_quit=false;window.close_requested.connect(_request_quit)
    if spec.has("conch_body_report"):
        body_mode=true;body_spec=JSON.parse_string(FileAccess.get_file_as_string(str(spec.conch_body_report)))
        assert(body_spec.mouth_component_sha256==spec.component_sha256)
        var body_path:String="res://"+str(body_spec.component).trim_prefix("app/")
        assert(FileAccess.get_sha256(body_path)==body_spec.component_sha256)
        assert(FileAccess.get_sha256("res://assets/helios_model.glb")==body_spec.base_sha256)
        var donor:Node3D=load("res://assets/helios_model.glb").instantiate();add_child(donor)
        var base:Node3D=donor.find_child("BASE_FIXED",true,false);assert(base!=null);base.reparent(self,true);donor.queue_free()
        if current_nautilus:
            assembly=load("res://collection/i_nautilus_assembly.gd").new();add_child(assembly);assembly.setup(body_spec)
            body_asset=assembly.body_asset;asset=assembly.mouth_asset;body_driver=assembly.body_driver;response_rig=assembly.rig;controller=response_rig.tongues;moonlight=assembly.music;echo_presentation=assembly.echo;sequence=assembly.sequence
            inspect_center=Vector3(0,1.66,0);yaw=-.3714;pitch=.225;distance=8.48
            window.title="MagicDesk · 海螺交互开发预览"
        else:
            body_asset=load(body_path).instantiate();add_child(body_asset)
            body_driver=load("res://collection/i_shell_linkage_b3_driver.gd").new();body_driver.bind(body_asset,body_spec)
            inspect_center=Vector3(0,1.73,0);yaw=.085;pitch=.256;distance=9.4
            window.title="MagicDesk · 回声海螺机构与月光预览"
    if not current_nautilus:
        var component:String="res://"+str(spec.component).trim_prefix("app/");assert(FileAccess.get_sha256(component)==spec.component_sha256)
        asset=load(component).instantiate();add_child(asset)
        if body_mode:
            var p:Array=body_spec.mouth_placement.p;var q:Array=body_spec.mouth_placement.q;var s:Array=body_spec.mouth_placement.s
            asset.transform=Transform3D(Basis(Quaternion(q[0],q[1],q[2],q[3])).scaled(Vector3(s[0],s[1],s[2])),Vector3(p[0],p[1],p[2]))
        if spec.has("diaphragm"):
            var aperture_path:String=str(spec.get("aperture_profile","res://assets/collection/art/I/diaphragm/aperture_profile.json"))
            var aperture:Dictionary=JSON.parse_string(FileAccess.get_file_as_string(aperture_path))
            response_rig=load("res://collection/i_mouth_response_rig.gd").new();response_rig.bind(asset,spec,aperture);controller=response_rig.tongues
            if ResourceLoader.exists("res://assets/collection/art/I/echo_r2/wavefront.glb"):
                echo_presentation=load("res://collection/i_echo_presentation.gd").new();add_child(echo_presentation);echo_presentation.setup(asset,true,2. if body_mode else 1.)
            if FileAccess.file_exists(str(spec.get("music_optics_layout","res://assets/collection/art/I/moonlight_candidate/current_mouth/layout.json"))):
                moonlight=load("res://collection/i_moonlight_controller.gd").new();add_child(moonlight);moonlight.setup(asset,spec,response_rig,echo_presentation)
        else:
            controller=load("res://collection/i_tongue_set_driver.gd").new();controller.bind(asset,spec)
        if body_mode:
            assert(response_rig!=null)
            sequence=load("res://review/i_conch_sequence.gd").new();sequence.bind(body_driver,response_rig,moonlight)
    var env:=Environment.new();env.background_mode=Environment.BG_COLOR;env.background_color=Color(.028,.030,.029)
    var panorama:=PanoramaSkyMaterial.new();panorama.panorama=load("res://assets/studio_small_09_4k.exr");panorama.energy_multiplier=.20
    var sky:=Sky.new();sky.sky_material=panorama;env.sky=sky;env.ambient_light_source=Environment.AMBIENT_SOURCE_SKY;env.ambient_light_energy=.30;env.reflected_light_source=Environment.REFLECTION_SOURCE_SKY;env.tonemap_mode=Environment.TONE_MAPPER_AGX
    env.ssao_enabled=true;env.ssao_radius=.04;env.ssao_intensity=.6;env.glow_enabled=false
    var environment:=WorldEnvironment.new();environment.environment=env;add_child(environment)
    var studio_lights:Array[AreaLight3D]=[]
    var light_rows:Array=[[Vector3(-2,-2,-2.5),5.,Vector2(1.5,2.3)],[Vector3(2,-.3,-.7),3.,Vector2(1.,2.)],[Vector3(-.5,2,-2),4.,Vector2(1.5,2.)]]
    if body_mode:light_rows=[[Vector3(-3,5,4),8.,Vector2(2.5,3.)],[Vector3(4,3,1),4.,Vector2(2.5,3.)],[Vector3(-2,4,-4),5.,Vector2(2.5,3.)]]
    for row in light_rows:
        var light:=AreaLight3D.new();add_child(light);light.position=row[0];light.look_at(inspect_center if body_mode else Vector3.ZERO,Vector3.UP if body_mode else Vector3.FORWARD);light.light_energy=row[1];light.area_size=row[2];light.area_normalize_energy=true;light.area_range=12. if body_mode else 10.;light.light_size=.25;light.shadow_enabled=true
        if not current_nautilus:light.shadow_normal_bias=.012
        studio_lights.append(light)
    if current_nautilus:
        get_viewport().msaa_3d=Viewport.MSAA_4X;get_viewport().use_taa=false
        RenderingServer.positional_soft_shadow_filter_set_quality(RenderingServer.SHADOW_QUALITY_SOFT_HIGH)
        env.ambient_light_energy=.35;env.ssao_radius=.08;env.ssao_intensity=.55
        var colors:Array=[Color(1.,.91,.80),Color(.84,.91,1.),Color(1.,.95,.86)]
        for i in range(studio_lights.size()):studio_lights[i].light_color=colors[i]
        load("res://collection/i_optical_finish_r40.gd").apply(env)
        studio_receipt={"profile":"nautilus_current_preview","scope":"Current assembly finish and reviewed studio lighting; no main App changes."}
    else:studio_receipt=load("res://review/i_mouth_studio.gd").apply(get_viewport(),env,studio_lights)
    if body_mode and not current_nautilus:studio_receipt["profile"]="conch_studio_r1";studio_receipt["scope"]="Independent conch inspection lighting; main App lighting unchanged."
    camera=Camera3D.new();add_child(camera);camera.fov=32.;camera.near=.02;camera.far=30.;update_camera()
    var canvas:=CanvasLayer.new();add_child(canvas)
    var ui:=Control.new();canvas.add_child(ui);ui.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT);ui.mouse_filter=Control.MOUSE_FILTER_IGNORE
    var font:=SystemFont.new();font.font_names=PackedStringArray(["PingFang SC","Hiragino Sans GB","Arial"])
    var title:=Label.new();ui.add_child(title);title.position=Vector2(26,18);title.text="回声海螺 · 喉口部件预览";title.add_theme_font_override("font",font);title.add_theme_font_size_override("font_size",21);title.mouse_filter=Control.MOUSE_FILTER_IGNORE
    var subtitle:=Label.new();ui.add_child(subtitle);subtitle.position=Vector2(27,49);subtitle.text="三片卷收与中心触须精修 · 尚非完整海螺";subtitle.add_theme_font_override("font",font);subtitle.add_theme_font_size_override("font_size",13);subtitle.modulate=Color(.70,.71,.68);subtitle.mouse_filter=Control.MOUSE_FILTER_IGNORE
    if response_rig:subtitle.text="三片、导轮与膜片联动 · 本轮无音频 · 尚非完整海螺"
    if echo_presentation:subtitle.text="喉口机械与回声反馈预览 · 尚非完整海螺"
    if moonlight:subtitle.text="月光奏鸣曲 · 完整三乐章与真实双谱表预演 · 同步仍待校准"
    if body_mode:
        title.text="回声海螺 · 机构与月光预览"
        subtitle.text="完整三乐章与真实双谱表 · 整体机构候选 · 造型与工艺精修中"
    status=Label.new();ui.add_child(status);status.set_anchors_and_offsets_preset(Control.PRESET_BOTTOM_LEFT);status.offset_left=27;status.offset_top=-69;status.offset_right=950;status.offset_bottom=-46;status.add_theme_font_override("font",font);status.add_theme_font_size_override("font_size",14);status.mouse_filter=Control.MOUSE_FILTER_IGNORE
    var help:=Label.new();ui.add_child(help);help.set_anchors_and_offsets_preset(Control.PRESET_BOTTOM_LEFT);help.offset_left=27;help.offset_top=-41;help.offset_right=950;help.offset_bottom=-18;help.text="点击开合  ·  拖拽旋转  ·  滚轮缩放  ·  空格开合  ·  L 循环  ·  R 复位";help.add_theme_font_override("font",font);help.add_theme_font_size_override("font_size",13);help.modulate=Color(.72,.73,.70);help.mouse_filter=Control.MOUSE_FILTER_IGNORE
    if response_rig:help.text="点击 / 空格开合 · H 按住蓄能 · E 单次演示 · 拖拽旋转 · 滚轮缩放 · L 循环 · R 复位"
    if moonlight:help.text="点投射器播放 / 点谱面暂停 · M 播放/暂停 · X 停止 · 点击口沿开合 · E 回声 · 拖拽/滚轮查看"
    write_report()
func update_camera()->void:
    if body_mode:
        camera.position=inspect_center+Vector3(sin(yaw)*cos(pitch),sin(pitch),cos(yaw)*cos(pitch))*distance;camera.look_at(inspect_center,Vector3.UP)
    else:
        camera.position=inspect_center+Vector3(-sin(yaw)*cos(pitch),-cos(yaw)*cos(pitch),-sin(pitch))*distance;camera.look_at(inspect_center,Vector3.FORWARD)
func toggle()->void:
    demo_charge_left=-1.
    if sequence and not sequence.desired_open and (sequence.shell_open>.00001 or openness>.00001):
        set_target(1.);cycle=false;input_count+=1;last_action="reverse_close"
        return
    if moonlight and moonlight.engaged():
        moonlight.stop(not body_mode)
        if body_mode:set_target(0.)
        else:target=0.
        cycle=false;input_count+=1;last_action="stop_music_close"
        return
    set_target(0. if target>.5 else 1.);cycle=false;input_count+=1;last_action="toggle"
func set_target(value:float)->void:
    target=value
    if sequence:sequence.set_open(value>.5)
    elif response_rig:response_rig.set_open(value>.5)
func _notification(what:int)->void:
    if what==NOTIFICATION_WM_WINDOW_FOCUS_OUT:
        down=false
        if response_rig and response_rig.user_pressed:
            cycle=false;demo_charge_left=-1.;set_target(0.);last_action="focus_cancel"
func over_model(pos:Vector2)->bool:
    var origin:=camera.project_ray_origin(pos);var direction:=camera.project_ray_normal(pos);var t:=maxf(0.,(inspect_center-origin).dot(direction))
    var closest:=origin+direction*t
    return closest.distance_to(inspect_center)<(1.95 if body_mode else 1.02) and (not body_mode or closest.y>.90)
func update_drag(position:Vector2)->void:
    var movement:=position-drag_last_position;drag_last_position=position
    dragged+=movement.length()
    if dragged>6. and not movement.is_zero_approx():
        yaw+=movement.x*.006;pitch=clampf(pitch+movement.y*.005,-1.1,1.1);update_camera();input_count+=1;last_action="orbit"
func _input(event:InputEvent)->void:
    if controller==null or quitting:return
    if event is InputEventKey and event.pressed and not event.echo and moonlight:
        if event.keycode==KEY_M:
            demo_charge_left=-1.;cycle=false
            if sequence:sequence.music_request()
            moonlight.toggle();target=1.;input_count+=1;last_action="music_toggle"
            return
        if event.keycode==KEY_X:
            moonlight.stop();input_count+=1;last_action="music_stop"
            return
        if moonlight.engaged() and event.keycode in [KEY_H,KEY_E,KEY_L]:return
    if event is InputEventKey and event.keycode==KEY_H and not event.echo and response_rig:
        demo_charge_left=-1.;cycle=false
        if sequence:sequence.set_pressed(event.pressed)
        else:response_rig.set_pressed(event.pressed)
        target=1. if response_rig.wants_open else 0.;input_count+=1;last_action="charge" if event.pressed else "release"
        return
    if event is InputEventKey and event.pressed and not event.echo:
        if event.keycode==KEY_SPACE:toggle()
        elif event.keycode==KEY_E and response_rig:
            cycle=false
            if sequence:sequence.set_pressed(true)
            else:response_rig.set_pressed(true)
            target=1.;demo_charge_left=1.;input_count+=1;last_action="single_response"
        elif event.keycode==KEY_L:
            demo_charge_left=-1.
            if response_rig:response_rig.set_pressed(false)
            cycle=not cycle;set_target(1.);hold=0.;input_count+=1;last_action="cycle"
        elif event.keycode==KEY_R:
            yaw=-.3714 if current_nautilus else .085 if body_mode else .79;pitch=.225 if current_nautilus else .256 if body_mode else .224;distance=8.48 if current_nautilus else 9.4 if body_mode else 3.70;update_camera();input_count+=1;last_action="reset_view"
        elif event.keycode==KEY_ESCAPE:_request_quit()
    if event is InputEventMouseButton:
        if event.button_index==MOUSE_BUTTON_LEFT:
            if event.pressed:
                down=true;dragged=0.;drag_last_position=event.position;drag_origin=event.position
                pointer_debug={"press":[event.position.x,event.position.y],"motion_count":0}
            else:
                if down:update_drag(event.position)
                pointer_debug["release"]=[event.position.x,event.position.y];pointer_debug["travel"]=dragged
                if down and dragged<6.:
                    var music_hit:String=moonlight.staff.pointer_target(camera,event.position) if moonlight else ""
                    if not music_hit.is_empty():
                        demo_charge_left=-1.;cycle=false
                        if sequence:sequence.music_request()
                        moonlight.toggle();target=1.;input_count+=1;last_action="music_pointer_"+music_hit
                    elif over_model(event.position):toggle()
                down=false
        elif event.pressed and event.button_index in [MOUSE_BUTTON_WHEEL_UP,MOUSE_BUTTON_WHEEL_DOWN]:
            distance=clampf(distance*(.92 if event.button_index==MOUSE_BUTTON_WHEEL_UP else 1.08),3.4 if body_mode else 2.65,12. if body_mode else 5.6);update_camera();input_count+=1;last_action="zoom"
    if event is InputEventMouseMotion and down:
        pointer_debug["motion_count"]=int(pointer_debug.get("motion_count",0))+1
        update_drag(event.position)
    elif event is InputEventMouseMotion and moonlight:
        var target_name:String=moonlight.staff.pointer_target(camera,event.position)
        moonlight.staff.show_pointer_target(target_name)
        Input.set_default_cursor_shape(Input.CURSOR_POINTING_HAND if not target_name.is_empty() else Input.CURSOR_ARROW)
    if event is InputEventPanGesture:
        distance=clampf(distance*exp(event.delta.y*.035),3.4 if body_mode else 2.65,12. if body_mode else 5.6);update_camera();input_count+=1;last_action="zoom"
func _process(delta:float)->void:
    if controller==null:return
    if current_nautilus:
        if demo_charge_left>=0.:
            demo_charge_left-=delta
            if demo_charge_left<=0.:demo_charge_left=-1.;response_rig.set_pressed(false)
        assembly.tick(delta);openness=response_rig.openness
    elif response_rig:
        if sequence:sequence.tick(delta)
        if moonlight:moonlight.tick(delta)
        if demo_charge_left>=0.:
            demo_charge_left-=delta
            if demo_charge_left<=0.:demo_charge_left=-1.;response_rig.set_pressed(false)
        response_rig.tick(delta);openness=response_rig.openness
        var events:Array=response_rig.drain_events()
        if echo_presentation:echo_presentation.update(delta,response_rig,events)
    else:
        openness=move_toward(openness,target,delta/2.6);controller.set_opening(openness)
    var resting:bool=response_rig.stage in ["closed","listening"] if response_rig else is_equal_approx(openness,target)
    if sequence:resting=resting and sequence.stage in ["ready","closed"]
    if resting:
        hold+=delta
        if cycle and hold>1.2:set_target(1.-target);hold=0.
    else:hold=0.
    status.text=("循环演示 · " if cycle else "")+("已展开" if openness>.999 else "已合拢" if openness<.001 else "展开中" if target>.5 else "合拢中")
    if response_rig:
        status.text=("循环演示 · " if cycle else "")+str({"closed":"已合拢","listening":"已展开 · 按住 H 试试受力与回弹","charging":"蓄能 · 膜片受压","release_wait":"展开喉片 · 保持蓄能","outgoing":"发出响应","echo":"回声抵达 · 二次轻回弹","recovering":"卸压归位后收拢","closing":"收拢中","opening":"展开中"}.get(response_rig.stage,response_rig.stage))
    if sequence and sequence.stage in ["opening_mouth","opening_shell","closing_shell","closing_mouth","unloading"]:
        status.text=str({"opening_mouth":"喉口展开后打开外壳","opening_shell":"壳体依次展开","closing_shell":"壳体收拢 · 喉口保持打开","closing_mouth":"壳体已归位 · 合拢喉口","unloading":"卸压与收谱"}[sequence.stage])
    if moonlight and moonlight.engaged():
        var state:Dictionary=moonlight.transport.snapshot();var seconds:=int(state.total_seconds)
        var playback_label:String="展开谱带" if moonlight.start_pending else "收束中" if moonlight.stopping else str({"playing":"播放中","paused":"已暂停","ended":"已播完","stopped":"准备播放"}.get(state.state,state.state))
        if current_nautilus and moonlight.start_pending:
            playback_label="喉口展开中" if sequence.stage=="opening_mouth" else "外壳展开中" if sequence.stage=="opening_shell" else "谱面展开中"
        status.text="月光 · 第 %d 乐章 · %02d:%02d / 16:01 · %s"%[state.movement,seconds/60,seconds%60,playback_label]
    report_timer+=delta
    if report_timer>.5:report_timer=0.;write_report()
func write_report()->void:
    if diagnostics_path.is_empty():return
    var data={"source_sha256":spec.get("source_sha256",""),"component_sha256":spec.get("component_sha256",""),"openness":openness,"target":target,"cycle":cycle,"yaw":yaw,"pitch":pitch,"distance":distance,"input_count":input_count,"last_action":last_action,"window_pixels":[get_window().size.x,get_window().size.y],"content_points":[get_window().content_scale_size.x,get_window().content_scale_size.y],"field_receipts":controller.receipts if controller!=null else []}
    data["studio"]=studio_receipt
    data["pointer"]=pointer_debug
    if response_rig:data["response"]=response_rig.state()
    if echo_presentation:data["presentation"]=echo_presentation.receipt
    if moonlight:data["moonlight"]=moonlight.status
    if current_nautilus:data["assembly"]=assembly.status;data["finish"]=assembly.finish_receipt
    if sequence:
        data["conch"]=sequence.snapshot();data["body_source_sha256"]=body_spec.source_sha256;data["body_component_sha256"]=body_spec.component_sha256;data["base_sha256"]=body_spec.base_sha256
    FileAccess.open(diagnostics_path,FileAccess.WRITE).store_string(JSON.stringify(data,"  "))

func _request_quit()->void:
    if quitting:return
    quitting=true;set_process(false);set_process_input(false)
    if current_nautilus:await assembly.shutdown()
    elif moonlight:
        moonlight.transport.stop();await get_tree().create_timer(.20).timeout
    get_tree().quit()
