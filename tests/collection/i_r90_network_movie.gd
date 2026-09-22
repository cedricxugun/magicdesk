extends SceneTree
## Isolated actual-renderer study. No main registry change and no screen UI overlay.
var world:Node3D
var camera:Camera3D
var music:Node
var rig:RefCounted
var driver:RefCounted
var sequence:RefCounted
var body:Node3D
var mouth:Node3D
var out:="res://../review/I_refinement/nautilus_reset_r82/chambers_r89/built_r3/native_default/"
var duration:=35.
var report_path:="res://../review/I_refinement/nautilus_reset_r82/chambers_r89/built_r3/build.json"
var polished:=false
var temporal_polish:=false
var rear_review:=false
var diagnostic_no_chamber_spill:=false
var studio_lights:Array[AreaLight3D]=[]
var optical_spill:Array[OmniLight3D]=[]
var chambers:RefCounted
func update_optical_spill()->void:
    if not polished:return
    var visibility:=smoothstep(.82,1.,float(music.staff.status.get("reveal",0.)))
    var level:float=music.transport.response_level()
    for i in range(optical_spill.size()):
        optical_spill[i].light_energy=visibility*(.12 if music.transport.state!="playing" else .45*(.7+level))
        music.staff.emitter_materials[i].emission_energy_multiplier=visibility*(.3 if music.transport.state!="playing" else 1.8*(.7+level))
func _initialize()->void:run.call_deferred()
func bvec(v:Vector3)->Vector3:return Vector3(v.x,v.z,-v.y)
func light_at(pos:Vector3,energy:float,size:Vector2)->void:
    var light:=AreaLight3D.new();world.add_child(light)
    light.position=bvec(pos);light.look_at(Vector3(0,1.7,0))
    light.light_energy=energy;light.area_size=size;light.area_normalize_energy=true
    light.area_range=12.;light.shadow_enabled=true;light.shadow_normal_bias=.004
    studio_lights.append(light)
func run()->void:
    RenderingServer.set_render_loop_enabled(false)
    RenderingServer.viewport_set_update_mode(root.get_viewport_rid(),RenderingServer.VIEWPORT_UPDATE_ALWAYS)
    if "--inspect-renderer" in OS.get_cmdline_user_args():
        for entry in RenderingServer.get_method_list():
            if str(entry.name) in ["environment_set_ssao_quality","positional_soft_shadow_filter_set_quality"]:print(JSON.stringify(entry))
        for name in ClassDB.class_get_integer_constant_list("RenderingServer"):
            if "SSAO_QUALITY" in name:print(name,"=",ClassDB.class_get_integer_constant("RenderingServer",name))
        var inspection_light:=AreaLight3D.new()
        for p in inspection_light.get_property_list():
            if "shadow" in str(p.name) or "sample" in str(p.name) or "area_" in str(p.name) or str(p.name)=="light_size":print(p.name," = ",inspection_light.get(p.name))
        inspection_light.free()
        quit();return
    Engine.max_fps=30
    for a in OS.get_cmdline_user_args():
        if a.begins_with("--seconds="):duration=a.trim_prefix("--seconds=").to_float()
        elif a.begins_with("--report="):report_path=a.trim_prefix("--report=")
        elif a.begins_with("--out="):out=a.trim_prefix("--out=").trim_suffix("/")+"/"
        elif a=="--studio-polish":polished=true
        elif a=="--temporal-polish":temporal_polish=true
        elif a=="--rear-review":rear_review=true
        elif a=="--diagnostic-no-chamber-spill":diagnostic_no_chamber_spill=true
    root.title="MagicDesk · 鹦鹉螺制作预览"
    root.position=Vector2i(-2000,-2000);root.set_flag(Window.FLAG_TRANSPARENT,false);root.set_flag(Window.FLAG_BORDERLESS,false)
    root.transparent_bg=false;root.size=Vector2i(900,990);root.msaa_3d=Viewport.MSAA_4X
    DirAccess.make_dir_recursive_absolute(ProjectSettings.globalize_path(out))
    world=Node3D.new();root.add_child(world)
    var env:=Environment.new();env.background_mode=Environment.BG_COLOR;env.background_color=Color(.035,.032,.028)
    var sky:=Sky.new();var pano:=PanoramaSkyMaterial.new();pano.panorama=load("res://assets/studio_small_09_4k.exr");pano.energy_multiplier=.24;sky.sky_material=pano;env.sky=sky
    env.ambient_light_source=Environment.AMBIENT_SOURCE_SKY;env.ambient_light_energy=.35;env.reflected_light_source=Environment.REFLECTION_SOURCE_SKY;env.tonemap_mode=Environment.TONE_MAPPER_AGX
    env.ssao_enabled=true;env.ssao_radius=.08;env.ssao_intensity=.5;env.glow_enabled=false
    var environment:=WorldEnvironment.new();environment.environment=env;world.add_child(environment)
    light_at(Vector3(-3,-4,5),20.,Vector2(4,1.6));light_at(Vector3(3,-2,3.6),24.,Vector2(3,1.));light_at(Vector3(1.5,3,4.8),8.,Vector2(3,2))
    if polished:
        root.msaa_3d=Viewport.MSAA_8X;root.use_taa=temporal_polish
        RenderingServer.positional_soft_shadow_filter_set_quality(RenderingServer.SHADOW_QUALITY_SOFT_HIGH)
        RenderingServer.environment_set_ssao_quality(RenderingServer.ENV_SSAO_QUALITY_HIGH,false,.5,4,50.,300.)
        env.ssao_intensity=.38
        var energies:=[14.,10.,19.]
        var colors:=[Color(1.,.88,.74),Color(.75,.85,1.),Color(1.,.92,.79)]
        for i in range(3):
            studio_lights[i].light_energy=energies[i];studio_lights[i].light_color=colors[i]
            studio_lights[i].light_size=1.;studio_lights[i].shadow_normal_bias=.010
    camera=Camera3D.new();world.add_child(camera);camera.projection=Camera3D.PROJECTION_ORTHOGONAL;camera.size=4.1
    camera.position=bvec(Vector3(-4,-7,3.65));camera.look_at(Vector3(0,1.57,0));camera.current=true;camera.near=.03
    if rear_review:
        camera.position=bvec(Vector3(4,7,3.65));camera.look_at(Vector3(0,1.57,0))
    var donor:Node3D=load("res://assets/helios_model.glb").instantiate();world.add_child(donor)
    var base:=donor.find_child("BASE_FIXED",true,false) as Node3D;assert(base!=null);base.reparent(world,true);donor.queue_free()
    var ground:=MeshInstance3D.new();var plane:=PlaneMesh.new();plane.size=Vector2(30,30);ground.mesh=plane
    var finish:=StandardMaterial3D.new();finish.albedo_color=Color(.034,.030,.025);finish.roughness=.42;ground.material_override=finish;ground.position.y=-.008;world.add_child(ground)
    var spec:Dictionary=JSON.parse_string(FileAccess.get_file_as_string(report_path))
    body=load("res://"+str(spec.component).trim_prefix("app/")).instantiate();world.add_child(body)
    mouth=load("res://"+str(spec.core_component).trim_prefix("app/")).instantiate();world.add_child(mouth)
    var mp:Dictionary=spec.mouth_placement;var p:Array=mp.p;var q:Array=mp.q;var s:Array=mp.s
    mouth.transform=Transform3D(Basis(Quaternion(q[0],q[1],q[2],q[3])).scaled(Vector3(s[0],s[1],s[2])),Vector3(p[0],p[1],p[2]))
    var core:Dictionary=JSON.parse_string(FileAccess.get_file_as_string("res://../"+str(spec.core_report)))
    driver=load("res://review/i_r82_body_driver.gd").new()
    if not driver.bind(body,spec):quit(1);return
    rig=load("res://collection/i_mouth_response_rig.gd").new();rig.bind(mouth,core,JSON.parse_string(FileAccess.get_file_as_string(core.aperture_profile)))
    music=load("res://collection/i_moonlight_controller.gd").new();world.add_child(music);music.setup(mouth,core,rig)
    if polished:
        for suffix in ["L","R"]:
            var glass:=music.staff.optics.find_child("I_StaffProjectorGlass"+suffix,true,false) as Node3D
            var spill:=OmniLight3D.new();glass.add_child(spill);spill.position=Vector3(0,-.018,0)
            spill.omni_range=.65;spill.light_color=Color(1.,.60,.22);spill.light_energy=.5
            spill.shadow_enabled=true;spill.shadow_normal_bias=.003;optical_spill.append(spill)
    music.transport.offline_capture_clock=OS.has_feature("movie")
    sequence=load("res://collection/i_nautilus_sequence.gd").new();sequence.shell_duration=driver.duration;sequence.bind(driver,rig,music)
    if spec.has("chamber_response_layout"):
        chambers=load("res://collection/i_chamber_music_response.gd").new();chambers.bind(body,spec)
        if diagnostic_no_chamber_spill:chambers.illumination.spill_gain=0.
    assert(OS.has_feature("movie"),"Use Movie Maker with --fixed-fps 30")
    root.position=Vector2i(220,60)
    var frame_count:=int(round(duration*30.))
    var samples:Array=[]
    RenderingServer.force_draw(false,0.)
    sequence.music_request();music.toggle()
    for f in range(frame_count):
        await process_frame
        sequence.tick(1./30.);rig.tick(1./30.);music.transport._process(0.);music.tick(1./30.)
        if chambers:chambers.update(music.transport.chamber_bands(),music.transport.position_seconds() if chambers.wants_work_clock() else music.transport.local_clock,music.transport.state=="playing",sequence.shell_open,1./30.)
        update_optical_spill()
        RenderingServer.force_draw(false,1./30.)
        if f%30==0:
            samples.append({"frame":f,"music":music.transport.snapshot(),"opening":sequence.shell_open,"network_clock":chambers.network_clock if chambers else 0.})
            print("R90_MOVIE_FRAME ",f," ",music.transport.state)
        if f in [0,240,330,420] or f==frame_count-1:root.get_texture().get_image().save_png(out+"frame_%04d.png"%f)
    FileAccess.open(out+"take.json",FileAccess.WRITE).store_string(JSON.stringify({"source_sha256":spec.source_sha256,"component_sha256":spec.component_sha256,"frames":frame_count+1,"fps":30,"recorder_cleanup_tail":true,"bootstrap_frames":1,"samples":samples,"scope":"Actual Godot movie frames and decoded Movie Maker audio, 30 fps open-and-play excerpt. Includes one closed bootstrap frame. No pause/seek/reversal; not native performance or full-work acceptance."},"  "))
    await process_frame
    music.transport.stop()
    for f in range(8):RenderingServer.force_draw(false,1./30.);await process_frame
    if chambers:chambers.release()
    world.queue_free();await process_frame
    print("R90_MOVIE_DONE");quit()
