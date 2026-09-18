extends SceneTree
var world:Node3D
var camera:Camera3D
var out:="res://../review/I_refinement/part_a_mouth/shutter_r2/runtime/"
func _initialize()->void:run.call_deferred()
func capture(name:String)->void:
    for i in range(6):await RenderingServer.frame_post_draw
    root.get_texture().get_image().save_png(out+name+".png")
func run()->void:
    out="res://../review/I_refinement/part_a_mouth/shutter_r2/tongue_probe/raster_audit/"+("lit_" if OS.get_environment("MAGICDESK_RASTER_LIT")=="1" else "")+OS.get_environment("MAGICDESK_RASTER_MODE")+"/"
    root.size=Vector2i(1200,1000);root.msaa_3d=Viewport.MSAA_4X;DirAccess.make_dir_recursive_absolute(out)
    world=Node3D.new();root.add_child(world)
    var env:=Environment.new();env.background_mode=Environment.BG_COLOR;env.background_color=Color(.030,.029,.026)
    var panorama:=PanoramaSkyMaterial.new();panorama.panorama=load("res://assets/studio_small_09_4k.exr");panorama.energy_multiplier=.20
    var sky:=Sky.new();sky.sky_material=panorama;env.sky=sky;env.ambient_light_source=Environment.AMBIENT_SOURCE_SKY;env.ambient_light_energy=.30;env.reflected_light_source=Environment.REFLECTION_SOURCE_SKY;env.tonemap_mode=Environment.TONE_MAPPER_AGX
    env.ssao_enabled=true;env.ssao_radius=.04;env.ssao_intensity=.6;env.glow_enabled=false
    var environment:=WorldEnvironment.new();environment.environment=env;world.add_child(environment)
    camera=Camera3D.new();world.add_child(camera);camera.fov=32.;camera.near=.02;camera.position=Vector3(1.3,-3.2,-.80);camera.look_at(Vector3(0,.13,0),Vector3.FORWARD)
    for row in [[Vector3(-2,-2,-2.5),5.,Vector2(1.5,2.3)],[Vector3(2,-.3,-.7),3.,Vector2(1.,2.)],[Vector3(-.5,2,-2),4.,Vector2(1.5,2.)]]:
        var light:=AreaLight3D.new();world.add_child(light);light.position=row[0];light.look_at(Vector3.ZERO,Vector3.FORWARD);light.light_energy=row[1];light.area_size=row[2];light.area_normalize_energy=true;light.area_range=10.;light.light_size=.25;light.shadow_enabled=true;light.shadow_normal_bias=.012
    var mode:=OS.get_environment("MAGICDESK_RASTER_MODE")
    var asset:Node3D=load("res://assets/collection/components/I_tongue_probe.glb").instantiate();world.add_child(asset)
    var spec:Dictionary=JSON.parse_string(FileAccess.get_file_as_string("res://../review/I_refinement/part_a_mouth/shutter_r2/tongue_probe/build.json"))
    var driver=load("res://collection/i_tongue_fields.gd").new();driver.bind(asset,spec,mode!="fixed")
    var foils:Array[MeshInstance3D]=[];var bases:Array=[];var metadata:Array=[]
    for name in spec.mesh_names:
        var node:=asset.find_child(name,true,false) as MeshInstance3D;foils.append(node);bases.append(node.mesh.surface_get_arrays(0));metadata.append({"name":name,"format":node.mesh.surface_get_format(0),"shadow_mesh":node.mesh.shadow_mesh!=null,"lod_bias":node.lod_bias})
        if mode=="no_shadow":node.mesh.shadow_mesh=null
        if mode=="full_mesh":
            var full:=ArrayMesh.new();full.add_surface_from_arrays(Mesh.PRIMITIVE_TRIANGLES,node.mesh.surface_get_arrays(0),[],{},0);node.mesh=full
    if mode=="no_lod":root.mesh_lod_threshold=0.
    for node in asset.find_children("*","MeshInstance3D",true,false):
        if mode=="no_shadow_all":node.mesh.shadow_mesh=null
        if node in foils:continue
        if OS.get_environment("MAGICDESK_RASTER_LIT")=="1":continue
        var mat:=StandardMaterial3D.new();mat.shading_mode=BaseMaterial3D.SHADING_MODE_UNSHADED;mat.albedo_color=Color(.12,.25,.48)
        if "Tine" in str(node.name) or "ResonatorCap" in str(node.name):mat.albedo_color=Color(1,.03,.01)
        node.material_override=mat
    var shader:=Shader.new();var code:String=FileAccess.get_file_as_string("res://collection/i_tongue_fields.gdshader");code=code.substr(0,code.find("void fragment()"))+"void fragment(){ALBEDO=vec3(1.);}";code=code.replace("render_mode cull_back;","render_mode unshaded,cull_back;");shader.code=code
    if OS.get_environment("MAGICDESK_RASTER_LIT")!="1":
        for material in driver.materials:material.shader=shader
    camera.position=Vector3(2.55,-2.4,-.82);camera.look_at(Vector3(0,.13,0),Vector3.FORWARD)
    var images:Dictionary={}
    for key in spec.motion_textures:images[key]=load("res://"+str(spec.motion_textures[key]).trim_prefix("app/")).get_image()
    for index in range(7):
        var amount:float=[0.,.15,.25,.35,.5,.7,1.][index];driver.set_feed(amount)
        if mode=="cpu_reference":
            for skin in range(foils.size()):
                var arrays:Array=bases[skin].duplicate(true);var uv:PackedVector2Array=arrays[Mesh.ARRAY_TEX_UV2];var p:PackedVector3Array=arrays[Mesh.ARRAY_VERTEX];var k:=amount*float(spec.pose_steps);var lo:=int(floorf(k));var hi:=int(ceilf(k));var blend:=k-floorf(k)
                for j in range(p.size()):
                    var row:=clampi(roundi(uv[j].x*float(spec.rows)-.5),0,int(spec.rows)-1);var v:=1.-uv[j].y;var back:=1. if v>1.5 else 0.;var w:=clampf(v-2.*back,0.,1.)
                    var c:Color=images.center.get_pixel(row,lo).lerp(images.center.get_pixel(row,hi),blend);var wd:Color=images.width.get_pixel(row,lo).lerp(images.width.get_pixel(row,hi),blend);var n:Color=images.normal.get_pixel(row,lo).lerp(images.normal.get_pixel(row,hi),blend)
                    p[j]=Vector3(c.r,c.g,c.b)+Vector3(wd.r,wd.g,wd.b)*(.5-w)+Vector3(n.r,n.g,n.b)*((c.a-1.)*sin(PI*w)+float(skin)*.0036+(back-.5)*.0015)
                arrays[Mesh.ARRAY_VERTEX]=p;var mesh:=ArrayMesh.new();mesh.add_surface_from_arrays(Mesh.PRIMITIVE_TRIANGLES,arrays);foils[skin].mesh=mesh
                var mat:=StandardMaterial3D.new();mat.shading_mode=BaseMaterial3D.SHADING_MODE_UNSHADED;mat.albedo_color=Color.WHITE;foils[skin].material_override=mat
        await capture("mask_%02d"%index)
    FileAccess.open(out+"audit.json",FileAccess.WRITE).store_string(JSON.stringify({"mode":mode,"source":spec.source_sha256,"meshes":metadata,"scope":"White foil/red head + tines/blue stationary parts; GPU raster audit, not art render."},"  "))
    print("TONGUE_RASTER_AUDIT_DONE "+mode);world.queue_free();await process_frame;quit()
