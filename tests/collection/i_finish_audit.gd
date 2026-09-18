extends SceneTree
var world:Node3D
var camera:Camera3D
var out:="res://../review/I_refinement/part_a_mouth/shutter_r2/finish_audit/"
var report_path:="res://../review/I_refinement/part_a_mouth/shutter_r2/front_guides/build.json"
func _initialize()->void:run.call_deferred()
func capture(name:String)->void:
    for i in range(24):await RenderingServer.frame_post_draw
    root.get_texture().get_image().save_png(out+name+".png")
func run()->void:
    root.size=Vector2i(1200,1000);root.msaa_3d=Viewport.MSAA_4X;DirAccess.make_dir_recursive_absolute(out)
    world=Node3D.new();root.add_child(world)
    var env:=Environment.new();env.background_mode=Environment.BG_COLOR;env.background_color=Color(.030,.029,.026)
    var panorama:=PanoramaSkyMaterial.new();panorama.panorama=load("res://assets/studio_small_09_4k.exr");panorama.energy_multiplier=.20
    var sky:=Sky.new();sky.sky_material=panorama;env.sky=sky;env.ambient_light_source=Environment.AMBIENT_SOURCE_SKY;env.ambient_light_energy=.30;env.reflected_light_source=Environment.REFLECTION_SOURCE_SKY;env.tonemap_mode=Environment.TONE_MAPPER_AGX
    env.ssao_enabled=true;env.ssao_radius=.04;env.ssao_intensity=.6;env.glow_enabled=false
    var environment:=WorldEnvironment.new();environment.environment=env;world.add_child(environment)
    camera=Camera3D.new();world.add_child(camera);camera.fov=32.;camera.near=.02;camera.position=Vector3(1.3,-3.2,-.80);camera.look_at(Vector3(0,.13,0),Vector3.FORWARD)
    var lights:Array[AreaLight3D]=[]
    for row in [[Vector3(-2,-2,-2.5),5.,Vector2(1.5,2.3)],[Vector3(2,-.3,-.7),3.,Vector2(1.,2.)],[Vector3(-.5,2,-2),4.,Vector2(1.5,2.)]]:
        var light:=AreaLight3D.new();world.add_child(light);light.position=row[0];light.look_at(Vector3.ZERO,Vector3.FORWARD);light.light_energy=row[1];light.area_size=row[2];light.area_normalize_energy=true;light.area_range=10.;light.light_size=.25;light.shadow_enabled=true;light.shadow_normal_bias=.012;lights.append(light)
    var spec:Dictionary=JSON.parse_string(FileAccess.get_file_as_string(report_path))
    var component:String="res://"+str(spec.component).trim_prefix("app/");var asset:Node3D=load(component).instantiate();world.add_child(asset)
    assert(FileAccess.get_sha256(component)==spec.component_sha256)
    var driver=load("res://collection/i_tongue_set_driver.gd").new();driver.bind(asset,spec)

    var standards:Array=[];var shaders:Array=[]
    for node in asset.find_children("*","MeshInstance3D",true,false):
        if node.material_override is ShaderMaterial:
            shaders.append([node.material_override,node.material_override.get_shader_parameter("finish_normal_strength")])
        else:
            for surface in range(node.mesh.get_surface_count()):
                var material=node.get_active_material(surface)
                if material is BaseMaterial3D:
                    var copy=material.duplicate();node.set_surface_override_material(surface,copy);standards.append([copy,copy.normal_enabled])
    var variants=["base","no_ssao","no_shadows","no_normal_maps","bias_03","bias_06","bias_10","hard_shadow","taa"]
    for variant in variants:
        env.ssao_enabled=variant!="no_ssao";root.use_taa=variant=="taa"
        for light in lights:
            light.shadow_enabled=variant!="no_shadows";light.light_size=0. if variant=="hard_shadow" else .25
            light.shadow_normal_bias={"bias_03":.3,"bias_06":.6,"bias_10":1.}.get(variant,.012)
        for pair in standards:pair[0].normal_enabled=pair[1] and variant!="no_normal_maps"
        for pair in shaders:pair[0].set_shader_parameter("finish_normal_strength",0. if variant=="no_normal_maps" else pair[1])
        camera.position=Vector3(-.20,-.6,.16);camera.look_at(Vector3(-.49,.02,.565),Vector3.FORWARD);driver.set_opening(.05)
        await capture(variant+"_close")
        camera.position=Vector3(-2.55,-2.4,-.82);camera.look_at(Vector3(0,.13,0),Vector3.FORWARD);driver.set_opening(.5)
        await capture(variant+"_whole")
    var settings={}
    for property in root.get_property_list():
        if "shadow_atlas" in str(property.name):settings[str(property.name)]=root.get(property.name)
    FileAccess.open(out+"audit.json",FileAccess.WRITE).store_string(JSON.stringify({"source_sha256":spec.source_sha256,"component_sha256":spec.component_sha256,"variants":variants,"viewport_shadow_settings":settings,"scope":"One-variable diagnostic A/B of current source under identical fixed cameras/material/light setup. Disabled effects are diagnostic, not a proposed final quality profile."},"  "))
    print("I_FINISH_AUDIT_FINISHED");world.queue_free();await process_frame;quit()
