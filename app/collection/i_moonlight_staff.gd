extends Node3D
## Current IAM mouth, authored optical geometry and deterministic score glyphs.
var sheet:MeshInstance3D
var material:ShaderMaterial
var catalog:Dictionary
var layout:Dictionary
var optics:Node3D
var cache:Dictionary={}
var requested:Dictionary={}
var wanted:Array=[]
var status:Dictionary={}
var pick_faces:PackedVector3Array
var emitter_centers:Array[Node3D]=[]
var emitter_materials:Array[BaseMaterial3D]=[]
var blank_tile:ImageTexture
var scan_materials:Array[ShaderMaterial]=[]
var scan_tips:Array=[]
var scanner_caps:Array[Node3D]=[]
var cap_status:Dictionary={}
var mouth:Node3D
func setup(asset:Node3D,component_sha256:String,layout_path:String="res://assets/collection/art/I/moonlight_candidate/current_mouth/layout.json")->void:
    layout=JSON.parse_string(FileAccess.get_file_as_string(layout_path))
    assert(layout.mouth_component_sha256==component_sha256)
    var path:String="res://"+str(layout.component).trim_prefix("app/")
    assert(FileAccess.get_sha256(path)==layout.component_sha256)
    mouth=asset.find_child(str(layout.mouth_node),true,false) as Node3D;assert(mouth!=null)
    optics=load(path).instantiate();mouth.add_child(optics)
    sheet=optics.find_child(str(layout.sheet),true,false) as MeshInstance3D;assert(sheet!=null)
    pick_faces=sheet.mesh.get_faces()
    for suffix in ["L","R"]:
        emitter_centers.append(optics.find_child("I_StaffProjectorHousing"+suffix,true,false))
        var glass:=optics.find_child("I_StaffProjectorGlass"+suffix,true,false) as MeshInstance3D
        var finish:=glass.get_active_material(0).duplicate() as BaseMaterial3D
        finish.emission_enabled=true;finish.emission=Color(1.,.70,.30);finish.emission_energy_multiplier=0.
        glass.set_surface_override_material(0,finish);emitter_materials.append(finish)
    material=ShaderMaterial.new();material.shader=load("res://collection/i_moonlight_staff.gdshader");sheet.material_override=material;sheet.cast_shadow=GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
    material.set_shader_parameter("score_gain",float(layout.get("score_gain",1.)))
    material.set_shader_parameter("optical_backing",float(layout.get("optical_backing",0.)))
    material.set_shader_parameter("correct_alpha",bool(layout.get("correct_alpha",true)))
    material.set_shader_parameter("cursor_width",float(layout.get("cursor_width",.010)))
    material.set_shader_parameter("edge_fade",float(layout.get("edge_fade",.025)))
    material.set_shader_parameter("ink_coverage_gain",float(layout.get("ink_coverage_gain",1.)))
    material.set_shader_parameter("center_z",-float(layout.center_y))
    if bool(layout.get("oriented_reveal",false)):
        material.set_shader_parameter("oriented_reveal",true)
        material.set_shader_parameter("reveal_center",_from_blender(layout.reveal_center_blender))
        material.set_shader_parameter("reveal_axis",_from_blender(layout.reveal_axis_blender).normalized())
    catalog=JSON.parse_string(FileAccess.get_file_as_string("res://assets/collection/art/I/moonlight_candidate/score/manifest.json"))
    var blank:=Image.create(1,1,false,Image.FORMAT_RGBA8);blank.fill(Color.TRANSPARENT)
    blank_tile=ImageTexture.create_from_image(blank)
    if layout.has("scanner"):_setup_scanner(asset)
    sheet.hide()
func _from_blender(values:Array)->Vector3:return Vector3(float(values[0]),float(values[2]),-float(values[1]))
func _setup_scanner(asset:Node3D)->void:
    var spec:Dictionary=layout.scanner
    var cap:Dictionary={}
    var cap_scene:PackedScene=null
    if spec.has("cap_manifest"):
        cap=JSON.parse_string(FileAccess.get_file_as_string(str(spec.cap_manifest)))
        assert(cap.mouth_component_sha256==layout.mouth_component_sha256)
        var cap_path:String="res://"+str(cap.component).trim_prefix("app/")
        assert(FileAccess.get_sha256(cap_path)==cap.component_sha256)
        cap_scene=load(cap_path)
        cap_status={"source_sha256":cap.source_sha256,"component_sha256":cap.component_sha256,"attached":0}
    var names:Array=[spec.line]
    for tip in spec.tips:names.append(tip.ray)
    for index in range(names.size()):
        var mesh:=optics.find_child(str(names[index]),true,false) as MeshInstance3D;assert(mesh!=null)
        var finish:=ShaderMaterial.new();finish.shader=load("res://collection/i_moonlight_scan.gdshader")
        finish.set_shader_parameter("filament",load(str(spec.mask)))
        finish.set_shader_parameter("follows_tip",index>0)
        finish.set_shader_parameter("filament_u_span",float(layout.get("filament_u_span",1.)))
        finish.set_shader_parameter("minimum_pixel_width",float(layout.get("scan_minimum_pixel_width",0.)))
        finish.set_shader_parameter("mask_power",float(layout.get("scan_mask_power",1.)))
        mesh.material_override=finish;mesh.cast_shadow=GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
        scan_materials.append(finish)
    for tip in spec.tips:
        var node:=asset.find_child(str(tip.node),true,false) as MeshInstance3D;assert(node!=null)
        var finish_node:MeshInstance3D=node
        var point_node:Node3D=node
        var local_point:Vector3=_from_blender(tip.local_point)
        if tip.has("lens_node"):
            finish_node=asset.find_child(str(tip.lens_node),true,false) as MeshInstance3D
            assert(finish_node!=null,"Missing authored reading lens")
            point_node=finish_node
            local_point=_from_blender(tip.lens_focus_local_blender)
            cap_status={"mode":"authored_directional_heads","attached":int(cap_status.get("attached",0))+1}
        elif cap_scene!=null:
            var attachment:Node3D=cap_scene.instantiate();node.add_child(attachment)
            assert(attachment.transform==Transform3D.IDENTITY)
            scanner_caps.append(attachment)
            finish_node=attachment.find_child(str(cap.lens),true,false)as MeshInstance3D;assert(finish_node!=null)
            local_point=_from_blender(cap.focus_local_blender)
            cap_status.attached+=1
        var original:=finish_node.get_surface_override_material(0)
        var finish:=finish_node.get_active_material(0).duplicate() as BaseMaterial3D
        if cap_scene!=null:
            finish.metallic=0.
            finish.clearcoat_enabled=true;finish.clearcoat=.85;finish.clearcoat_roughness=.08
        finish.emission_enabled=true;finish.emission=Color(1.,.55,.13);finish.emission_energy_multiplier=0.
        finish_node.set_surface_override_material(0,finish)
        var binding:Dictionary={"node":point_node,"finish_node":finish_node,"local_point":local_point,"rest_point":_from_blender(tip.mouth_point),"finish":finish,"original":original}
        if tip.has("head_node"):
            var head:=asset.find_child(str(tip.head_node),true,false) as Node3D
            assert(head!=null,"Missing reading-head gimbal")
            binding["head"]=head;binding["head_rest_basis"]=head.basis
            binding["head_forward"]=_from_blender(tip.head_forward_local_blender).normalized()
            binding["head_target"]=_from_blender(spec.focus)
        scan_tips.append(binding)
func pointer_target(camera:Camera3D,screen:Vector2)->String:
    var toward_viewer:Vector3=(camera.global_position-optics.global_position).normalized()
    var reading_normal:Vector3=_from_blender(layout.reading_normal_blender) if layout.has("reading_normal_blender") else Vector3(0,-1,0)
    if (optics.global_basis*reading_normal).normalized().dot(toward_viewer)<.15:return ""
    var origin:=camera.project_ray_origin(screen);var direction:=camera.project_ray_normal(screen)
    if sheet.visible and float(status.get("reveal",0.))>.98:
        var inverse:=sheet.global_transform.affine_inverse();var local_origin:=inverse*origin;var local_direction:=inverse.basis*direction
        for index in range(0,pick_faces.size(),3):
            if Geometry3D.ray_intersects_triangle(local_origin,local_direction,pick_faces[index],pick_faces[index+1],pick_faces[index+2])!=null:return "staff"
    for emitter in emitter_centers:
        var t:=maxf(0.,(emitter.global_position-origin).dot(direction))
        if (origin+direction*t).distance_to(emitter.global_position)<.060:return "emitter"
    return ""
func show_pointer_target(target:String)->void:
    for finish in emitter_materials:finish.emission_energy_multiplier=.28 if not target.is_empty() else .07 if sheet.visible else 0.
func _request(path:String)->void:
    if cache.has(path) or requested.has(path):return
    var err:=ResourceLoader.load_threaded_request(path,"Texture2D")
    assert(err==OK,"Unable to request real score tile: "+path)
    requested[path]=true
func _poll()->void:
    for path in requested.keys():
        var state:=ResourceLoader.load_threaded_get_status(path)
        assert(state!=ResourceLoader.THREAD_LOAD_FAILED and state!=ResourceLoader.THREAD_LOAD_INVALID_RESOURCE)
        if state==ResourceLoader.THREAD_LOAD_LOADED:
            var texture=ResourceLoader.load_threaded_get(path)
            if path in wanted:cache[path]=texture
            requested.erase(path)
func set_score_position(movement_number:int,quarter:float,reveal:float)->void:
    assert(movement_number>=1 and movement_number<=3)
    var row:Dictionary=catalog.movements[movement_number-1];var anchors:Array=row.anchors
    var lo:=0;var hi:=anchors.size()-1
    while lo+1<hi:
        var mid:=(lo+hi)/2
        if float(anchors[mid].quarter)<=quarter:lo=mid
        else:hi=mid
    var a:Dictionary=anchors[lo];var b:Dictionary=anchors[hi]
    var fraction:=clampf((quarter-float(a.quarter))/maxf(.000001,float(b.quarter)-float(a.quarter)),0.,1.)
    var note_x:=lerpf(float(a.x),float(b.x),fraction)
    # Match score-window aspect to the actual geometry; do not stretch notes.
    var width:float=float(row.height)*float(layout.width)/float(layout.height)
    # Keep the played score coordinate at the physical scanner, including the
    # first/last notes. Off-score regions are blank, never clamped repeated tiles.
    var offset:=note_x-width*.5;var first:=int(floorf(offset/float(row.tile_width)))
    assert(width<=float(row.tile_width)*2.,"Score window exceeds the three-tile carrier")
    wanted=[]
    var slots:Array[String]=[]
    var valid:=Vector3.ZERO
    for n in range(4):
        var tile_index:=first+n
        var path:String=str(row.tiles[tile_index]) if tile_index>=0 and tile_index<row.tiles.size() else ""
        if n<3:
            slots.append(path)
            valid[n]=0. if path.is_empty() else 1.
        if not path.is_empty():wanted.append(path)
    for path in wanted:_request(path)
    _poll()
    var ready:=true
    for path in slots:ready=ready and (path.is_empty() or cache.has(path))
    if ready:
        for n in range(3):material.set_shader_parameter("page_"+str(n),blank_tile if slots[n].is_empty() else cache[slots[n]])
        material.set_shader_parameter("valid_tiles",valid)
        material.set_shader_parameter("score_offset",offset)
        material.set_shader_parameter("score_length",float(row.width))
        material.set_shader_parameter("offset_in_tile",offset-first*float(row.tile_width));material.set_shader_parameter("window_width",width);material.set_shader_parameter("tile_width",row.tile_width)
        material.set_shader_parameter("playhead",.5)
        status={"movement":movement_number,"quarter_estimate":quarter,"first_tile":first,"offset":offset,"width":width,"note_x":note_x,"playhead":.5,"valid_tiles":[valid.x,valid.y,valid.z],"ready":true}
    else:status["ready"]=false
    for path in cache.keys():
        if not path in wanted:cache.erase(path)
    var can_hold:bool=status.has("movement") and int(status.movement)==movement_number and is_equal_approx(float(status.quarter_estimate),quarter)
    material.set_shader_parameter("reveal",clampf(reveal,0.,1.));sheet.visible=reveal>.001 and (ready or can_hold)
    status["cache_size"]=cache.size();status["pending_tiles"]=requested.size();status["reveal"]=reveal
func set_music_response(level:float,playing:bool,started:bool=true)->void:
    material.set_shader_parameter("music_level",clampf(level,0.,1.))
    material.set_shader_parameter("playing",1. if playing else 0.)
    material.set_shader_parameter("reading_started",1. if started else 0.)
    status["scan_level"]=clampf(level,0.,1.);status["scan_playing"]=playing
    var visibility:=smoothstep(.82,1.,float(status.get("reveal",0.))) if sheet.visible else 0.
    var intensity:float=visibility*(.055+(.36+level*.75 if playing else 0.)) if started else 0.
    intensity*=float(layout.get("scan_gain",1.))
    for index in range(scan_materials.size()):
        scan_materials[index].set_shader_parameter("strength",intensity*(1. if index in [0,2] else .35))
    for index in range(scan_tips.size()):
        var tip:Dictionary=scan_tips[index]
        if tip.has("head"):
            var head:Node3D=tip.head
            var parent:=head.get_parent() as Node3D
            var rest_world:Basis=parent.global_basis*tip.head_rest_basis
            var from_axis:Vector3=(rest_world*tip.head_forward).normalized()
            var to_target:Vector3=mouth.to_global(tip.head_target)-head.global_position
            if to_target.length_squared()>.0000001:
                head.global_basis=Basis(Quaternion(from_axis,to_target.normalized()))*rest_world
        var point:Vector3=mouth.to_local(tip.node.to_global(tip.local_point))
        scan_materials[index+1].set_shader_parameter("tip_delta",point-tip.rest_point)
        tip.finish.emission_energy_multiplier=intensity*.85
    status["scan_intensity"]=intensity
    status["scanner_caps"]=cap_status
var preserve_attachments_on_exit:=false
func _exit_tree()->void:
    if preserve_attachments_on_exit:return
    # Finish outstanding tiny tile loads before releasing the owning component.
    for path in requested.keys():
        var state:=ResourceLoader.load_threaded_get_status(path)
        if state in [ResourceLoader.THREAD_LOAD_IN_PROGRESS,ResourceLoader.THREAD_LOAD_LOADED]:ResourceLoader.load_threaded_get(path)
    requested.clear();cache.clear()
    for tip in scan_tips:
        if is_instance_valid(tip.finish_node):tip.finish_node.set_surface_override_material(0,tip.original)
        if tip.has("head") and is_instance_valid(tip.head):tip.head.basis=tip.head_rest_basis
    for cap in scanner_caps:
        if is_instance_valid(cap):cap.queue_free()
    if is_instance_valid(optics):optics.queue_free()
