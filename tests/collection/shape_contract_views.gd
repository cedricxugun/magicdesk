extends SceneTree
var host:Node3D
func _initialize()->void:run.call_deferred()
func run()->void:
    var contract_path:="res://../production/I_refinement/conch_r11/shape_contract.json"
    for arg in OS.get_cmdline_user_args():
        if arg.begins_with("--contract="):contract_path="res://../"+arg.trim_prefix("--contract=")
    var contract:Dictionary=JSON.parse_string(FileAccess.get_file_as_string(contract_path))
    var report:Dictionary=JSON.parse_string(FileAccess.get_file_as_string("res://../"+str(contract.build_report).get_base_dir()+"/measured_shape.json"))
    set_meta("collection_no_save",true);set_meta("collection_no_audio",true);set_meta("collection_skip_intro",true)
    var scene:Node=load("res://main.tscn").instantiate();root.add_child(scene)
    for i in range(12):await process_frame
    host=scene.get_node("Render/HeliosDesktop");host.set_process(false);host.power=1.;host.power_target=1.;host.muted=true
    var shared:Node3D=host.collection;shared._legacy_set_visible(false);shared._set_base_frame("shared")
    host.render_view.size=Vector2i(int(contract.views.resolution[0]),int(contract.views.resolution[1]));host.camera.projection=Camera3D.PROJECTION_ORTHOGONAL;host.camera.keep_aspect=Camera3D.KEEP_HEIGHT;host.camera.size=contract.views.ortho_span_scene_units
    var component:String="res://"+str(contract.component).trim_prefix("app/");assert(FileAccess.get_sha256(component)==report.component_sha256)
    var asset:Node3D=load(component).instantiate();host.add_child(asset)
    var clay:=StandardMaterial3D.new();clay.albedo_color=Color(.45,.48,.49);clay.roughness=.68
    var white:=StandardMaterial3D.new();white.shading_mode=BaseMaterial3D.SHADING_MODE_UNSHADED;white.albedo_color=Color.WHITE
    var meshes:Array=asset.find_children("*","MeshInstance3D",true,false)
    var background_meshes:Array=[]
    for mesh in host.find_children("*","MeshInstance3D",true,false):
        if not asset.is_ancestor_of(mesh):background_meshes.append({"node":mesh,"visible":mesh.visible})
    host.env.tonemap_mode=Environment.TONE_MAPPER_LINEAR;host.env.tonemap_exposure=1.;host.env.glow_enabled=false;host.env.adjustment_enabled=false
    var overlay:Node2D=load("res://../tests/collection/shape_measure_overlay.gd").new();host.render_view.add_child(overlay)
    var out:String="res://../"+str(contract.build_report).get_base_dir()+"/fixed_views/";DirAccess.make_dir_recursive_absolute(out);var records:Array=[]
    var target:=Vector3(contract.views.target_godot[0],contract.views.target_godot[1],contract.views.target_godot[2])
    for view in ["front","side","rear","top"]:
        var p:Array=contract.views[view];host.camera.position=Vector3(p[0],p[1],p[2]);host.camera.look_at(target,Vector3.FORWARD if view=="top" else Vector3.UP)
        overlay.heading=str(contract.source).get_file().get_basename()+" · "+view+" · candidate / NOT locked"
        var dims:Array=report.groups.body.size_D
        overlay.details="D=%.6f scene units   Body W/D/H = %.3f / %.3f / %.3f D"%[report.D,dims[0],dims[1],dims[2]];overlay.markers=[]
        var anchors:Dictionary={}
        for key in contract.anchors:
            var node:Node3D=asset.find_child(contract.anchors[key],true,false);var screen:Vector2=host.camera.unproject_position(node.global_position)
            var xyz:Array=report.anchors[key].world_D;overlay.markers.append({"point":screen,"text":"%s (%.3f, %.3f, %.3f)D"%[key,xyz[0],xyz[1],xyz[2]]});anchors[key]=[screen.x,screen.y]
        overlay.show();overlay.queue_redraw();shared.show()
        for item in background_meshes:item.node.visible=item.visible
        for mesh in meshes:mesh.material_override=clay
        for i in range(5):await RenderingServer.frame_post_draw
        host.render_view.get_texture().get_image().save_png(out+view+"_measured.png")
        overlay.hide();shared.hide()
        for item in background_meshes:item.node.hide()
        for mesh in meshes:mesh.material_override=white
        for i in range(4):await RenderingServer.frame_post_draw
        host.render_view.get_texture().get_image().save_png(out+view+"_silhouette.png")
        records.append({"view":view,"camera_position":p,"target":contract.views.target_godot,"ortho_span":host.camera.size,"resolution":contract.views.resolution,"landmarks_pixels":anchors})
    FileAccess.open(out+"views.json",FileAccess.WRITE).store_string(JSON.stringify({"source_sha256":report.source_sha256,"component_sha256":report.component_sha256,"contract_sha256":report.contract_sha256,"views":records,"status":"candidate_measured_not_locked","scope":"Fixed orthographic neutral views and unlabelled silhouettes, plus actual projected landmark coordinates. No reference matching score or art acceptance."},"  "))
    print("SHAPE_CONTRACT_VIEWS_FINISHED");host=null;scene.queue_free();await process_frame;quit()
