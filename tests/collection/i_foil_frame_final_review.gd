extends SceneTree
var world:Node3D
var camera:Camera3D
var out:="res://../review/I_refinement/part_a_mouth/shutter_r2/foil_frame/final_shader/"
var report_path:="res://../review/I_refinement/part_a_mouth/shutter_r2/diaphragm/build.json"
func _initialize()->void:run.call_deferred()
var timings:Dictionary={}
func capture(name:String)->void:
    var gpu:Array=[]
    for i in range(10):
        await RenderingServer.frame_post_draw
        if i>=5:gpu.append(RenderingServer.viewport_get_measured_render_time_gpu(root.get_viewport_rid()))
    timings[name]={"gpu_ms":gpu}
    root.get_texture().get_image().save_png(out+name+".png")
func run()->void:
    for argument in OS.get_cmdline_user_args():
        if argument.begins_with("--report="):
            report_path=argument.trim_prefix("--report=")
            out=report_path.get_base_dir()+"/studio/"
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



    var receipt:Dictionary=load("res://review/i_mouth_studio.gd").apply(root,env,lights)
    var legacy_shader:=Shader.new();legacy_shader.code=FileAccess.get_file_as_string("res://../review/I_refinement/part_a_mouth/shutter_r2/foil_frame/source_baseline/i_tongue_fields.gdshader")
    var foils:Array=[];var original_shaders:Array=[];var corrected_shaders:Array=[];var material_receipts:Array=[]
    for group in spec.tongues:
        for name in group.mesh_names:
            var node:=asset.find_child(name,true,false) as MeshInstance3D
            foils.append(node);var legacy_material:ShaderMaterial=node.material_override.duplicate();legacy_material.shader=legacy_shader;original_shaders.append(legacy_material)
            var candidate:ShaderMaterial=node.material_override.duplicate()
            candidate.shader=load("res://collection/i_tongue_fields.gdshader");corrected_shaders.append(candidate)
            var base:=node.mesh.surface_get_material(0) as StandardMaterial3D
            material_receipts.append({"mesh":name,"normal_scale":base.normal_scale,"roughness":base.roughness,"metallic":base.metallic,"has_normal":base.normal_enabled,"normal_texture":base.normal_texture.resource_path if base.normal_texture else ""})
    root.mesh_lod_threshold=0.
    var views={"whole": [Vector3(-2.55,-2.4,-.82),Vector3(0,.13,0)],"close": [Vector3(-.7,-1.25,-.24),Vector3(.0,.01,-.08)]}
    for view in views:
        camera.position=views[view][0];camera.look_at(views[view][1],Vector3.FORWARD)
        driver.set_opening(0.)
        for mode in ["source_rest","legacy","corrected"]:
            for i in range(foils.size()):foils[i].material_override=null if mode=="source_rest" else original_shaders[i] if mode=="legacy" else corrected_shaders[i]
            await capture(view+"_"+mode)
    for opening in [.25,.5]:
        driver.set_opening(opening)
        for mode in ["legacy","corrected"]:
            for i in range(foils.size()):
                var feed:float=driver.controllers[i/2].materials[i%2].get_shader_parameter("feed")
                original_shaders[i].set_shader_parameter("feed",feed)
                corrected_shaders[i].set_shader_parameter("feed",feed)
                foils[i].material_override=original_shaders[i] if mode=="legacy" else corrected_shaders[i]
            await capture("motion_%d_"%int(opening*100)+mode)
    FileAccess.open(out+"review.json",FileAccess.WRITE).store_string(JSON.stringify({"source_sha256":spec.source_sha256,"component_sha256":spec.component_sha256,"legacy_shader_sha256":FileAccess.get_sha256("res://../review/I_refinement/part_a_mouth/shutter_r2/foil_frame/source_baseline/i_tongue_fields.gdshader"),"candidate_shader_sha256":FileAccess.get_sha256("res://collection/i_tongue_fields.gdshader"),"materials":material_receipts,"studio":receipt,"scope":"Actual Metal fixed-camera A/B of imported StandardMaterial REST, original dynamic tangent frame, and orthogonal imported-handedness candidate. Original geometry/material textures preserved. Source-rest comparison only at REST; moving comparisons are not an art or collision acceptance."},"  "))
    print("I_FOIL_FRAME_REVIEW_FINISHED");world.queue_free();await process_frame;quit()
