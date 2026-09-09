extends Node3D
## One permanent base, a mechanical archive and replaceable upper assemblies.

var host:Node3D
var registry:Array=[]
var active_id:="B"
var current:Node3D
var prepared:Node3D
var requested:=""
var state:="idle"
var state_time:=0.0
var closing:=false
var sleep_pending:=false
var ticket:=0
var warm_view:SubViewport
var selector:Node3D
var selector_data:Dictionary
var selector_controls:Array=[]
var card_nodes:Array=[]
var selector_amount:=0.0
var selector_target:=0.0
var browse_start:=0
var pointer_down:=-2
var pressure_strip:Node3D
var seam:MeshInstance3D
var custom_panel:Node3D
var custom_controls:Array=[]
var widget_templates:Dictionary={}
var base_display:MeshInstance3D
var base_materials:Array=[]
var base_frames:Dictionary
var base_collision_cache:Dictionary={}
var base_mesh_cache:Dictionary={}
var control_shape_cache:Dictionary={}
var original_base_mesh:Mesh
var legacy_bodies:Array=[]
var legacy_control_bodies:Array=[]
var scan_overrides:Array=[]
var scan_materials:Array=[]
var legacy_scan_shaders:Dictionary={}
var last_error:=""
var action_log:Array=[]
var card_hint_active:=false
var selector_hit:Dictionary={}
var index_spindle:Node3D
var browse_pending:=0
var browse_time:=-1.0
var index_rotation:=0.0
var index_dragging:=false
var index_drag_distance:=0.0
var card_hover:Array[float]=[]
var prepare_started:=0
var load_metrics:Dictionary={}
var abandoned_loads:Array[String]=[]
const DISCOVERY_VERSION:=1
var intro_pending:=false
var archive_guide:PanelContainer
var archive_guide_text:Label
var scanner_controls:Array=[]
var scanner_aims:Array=[]
var scanner_emitters:Array=[]
var scanner_amount:=0.0
var scanner_target:=0.0
var transition_vfx:Node3D
var selector_wait:=false
var pending_action:=-1
var selected_slot:=-1
var control_driver:RefCounted
var native_regions:Array[Rect2i]=[]
var regions_clock:=0.0
var control_library:Node3D
var read_time:=-1.0
var help_index:=-1
var help_since_ms:=0
var help_point:=Vector2.ZERO
var help_owned:=false
var signal_materials:Array[ShaderMaterial]=[]
var legacy_mount_homes:Array[Transform3D]=[]
const ARCHIVE_SECONDS:=1.55
const RECAST_SECONDS:=1.85

func _pose(p:Dictionary)->Transform3D:
	var q:Quaternion=Quaternion(p.q[0],p.q[1],p.q[2],p.q[3])
	return Transform3D(Basis(q)*Basis.from_scale(Vector3(p.s[0],p.s[1],p.s[2])),Vector3(p.p[0],p.p[1],p.p[2]))

func setup(owner:Node3D)->void:
	host=owner
	control_driver=load("res://collection/control_driver.gd").new();control_driver.setup(self)
	var config:Dictionary=JSON.parse_string(FileAccess.get_file_as_string("res://assets/collection/registry.json"))
	registry=config.models
	base_display=host.named("BASE_FIXED_DisplayMesh");original_base_mesh=base_display.mesh
	for i in range(base_display.mesh.get_surface_count()):base_materials.append(base_display.get_active_material(i))
	base_frames=JSON.parse_string(FileAccess.get_file_as_string("res://assets/collection/base_frames.json"))
	_collect_bodies(host.turntable,legacy_bodies)
	for i in range(1,6):_collect_bodies(host.buttons[i].mount,legacy_control_bodies);legacy_mount_homes.append(host.buttons[i].mount.transform)
	_setup_selector()
	_set_base_frame("helios")
	base_mesh_cache["shared"]=load(base_frames.variants.shared.path)
	base_collision_cache["shared"]=base_mesh_cache.shared.create_trimesh_shape()
	host.menu.add_separator();host.menu.add_item("展示旋转 / 暂停",24)
	_update_actions()
	_setup_archive_guide()
	transition_vfx=load("res://collection/transition_vfx.gd").new();add_child(transition_vfx);transition_vfx.setup(self)
	if not get_tree().get_meta("collection_skip_intro",false):
		var preferences:=ConfigFile.new();preferences.load("user://collection.cfg")
		intro_pending=int(preferences.get_value("archive","discovery_version",0))<DISCOVERY_VERSION
		if intro_pending:host.message("点击左前侧白色舱罩，展开装置档案",7)

func _setup_archive_guide()->void:
	archive_guide=PanelContainer.new();archive_guide.mouse_filter=Control.MOUSE_FILTER_IGNORE
	var style:=StyleBoxFlat.new();style.bg_color=Color(.045,.04,.03,.93);style.border_color=Color(.45,.32,.17,.85);style.set_border_width_all(1);style.set_corner_radius_all(6)
	style.content_margin_left=14;style.content_margin_right=14;style.content_margin_top=9;style.content_margin_bottom=9
	archive_guide.add_theme_stylebox_override("panel",style)
	archive_guide_text=Label.new();archive_guide_text.mouse_filter=Control.MOUSE_FILTER_IGNORE
	archive_guide_text.add_theme_font_size_override("font_size",int(12*DisplayServer.screen_get_scale()))
	archive_guide_text.add_theme_color_override("font_color",Color(.95,.83,.63))
	archive_guide_text.text="点铭牌切换 · 共 %d 款\n滚轮翻阅 · 环沿盖板 / Tab 收起"%registry.size()
	archive_guide.add_child(archive_guide_text);host.toast.get_parent().add_child(archive_guide);archive_guide.hide()

func _acknowledge_intro()->void:
	if not intro_pending:return
	intro_pending=false
	if get_tree().get_meta("collection_skip_intro",false) or get_tree().get_meta("collection_no_save",false):return
	var preferences:=ConfigFile.new();preferences.load("user://collection.cfg")
	preferences.set_value("archive","discovery_version",DISCOVERY_VERSION);preferences.save("user://collection.cfg")

func _definition(id:String)->Dictionary:
	for item in registry:
		if item.id==id:return item
	return {}

func _collect_bodies(node:Node,into:Array)->void:
	if node is StaticBody3D:into.append({"body":node,"layer":node.collision_layer})
	for child in node.get_children():_collect_bodies(child,into)

func _set_bodies(items:Array,enabled:bool)->void:
	for item in items:item.body.collision_layer=item.layer if enabled else 0

func _set_base_frame(kind:String)->void:
	var info:Dictionary=base_frames.variants[kind]
	# ResourceLoader's cache is weak. Keep the mesh (and its texture resources)
	# alive after warmup so first exchange never synchronously reloads them.
	if not base_mesh_cache.has(kind):base_mesh_cache[kind]=load(info.path)
	base_display.mesh=base_mesh_cache[kind]
	if not base_collision_cache.has(kind):base_collision_cache[kind]=base_display.mesh.create_trimesh_shape()
	for i in range(info.source_surfaces.size()):base_display.set_surface_override_material(i,base_materials[int(info.source_surfaces[i])])
	for child in base_display.get_children():
		if child is StaticBody3D:
			for shape in child.get_children():
				if shape is CollisionShape3D:shape.set_deferred("shape",base_collision_cache[kind])

func _setup_selector()->void:
	selector_data=JSON.parse_string(FileAccess.get_file_as_string("res://assets/collection/models/S.json"))
	selector=load("res://assets/collection/models/S.glb").instantiate();add_child(selector)
	for item in selector_data.controls:
		var samples:Array[Transform3D]=[]
		for p in item.samples:samples.append(_pose(p))
		var control:={"node":selector.find_child(item.name,true,false),"samples":samples}
		if item.name in selector_data.get("scan_controls",[]):scanner_controls.append(control)
		else:selector_controls.append(control)
	for label in selector_data.get("scanner_aims",[]):
		var node:Node3D=selector.find_child(label,true,false);scanner_aims.append({"node":node,"home":node.transform})
	for label in selector_data.get("scanner_emitters",[]):scanner_emitters.append(selector.find_child(label,true,false))
	pressure_strip=selector.find_child(selector_data.pressure_strip,true,false)
	seam=selector.find_child("S_SeamLight",true,false)
	index_spindle=selector.find_child(selector_data.get("index_spindle",""),true,false)
	if index_spindle:
		var index_body:=StaticBody3D.new();index_body.collision_layer=8;index_body.collision_mask=0;index_body.set_meta("index_spindle",true);index_spindle.add_child(index_body)
		var shape:=CollisionShape3D.new();var cylinder:=CylinderShape3D.new();cylinder.radius=.069;cylinder.height=.07;shape.shape=cylinder;index_body.add_child(shape)
	for kind in selector_data.widgets:widget_templates[kind]=selector.find_child(selector_data.widgets[kind],true,false)
	if ResourceLoader.exists("res://assets/collection/control_library.glb"):
		control_library=load("res://assets/collection/control_library.glb").instantiate();add_child(control_library);control_library.hide()
	selector.find_child("S_WIDGET_LIBRARY",true,false).hide()
	selector.find_child("S_PANEL",true,false).hide()
	_smoke_glass(selector)
	# The visible hatch belongs to the same mechanism as the narrow pressure
	# strip. Make both real surfaces clickable; don't add an invisible button.
	for label in selector_data.get("click_surfaces",["S_PressureStrip","S_HatchCover"]):
		var surface:MeshInstance3D=selector.find_child(label,true,false)
		var entry_body:=StaticBody3D.new();entry_body.collision_layer=8;entry_body.collision_mask=0;entry_body.set_meta("entry",true);surface.add_child(entry_body)
		var entry_shape:=CollisionShape3D.new();entry_shape.shape=surface.mesh.create_trimesh_shape();entry_body.add_child(entry_shape)
	var font:=SystemFont.new();font.font_names=PackedStringArray(["PingFang SC","Helvetica Neue"])
	for i in range(selector_data.cards.size()):
		var root:Node3D=selector.find_child(selector_data.cards[i],true,false)
		var body:=StaticBody3D.new();body.collision_layer=0;body.collision_mask=0;body.set_meta("card_slot",i);root.add_child(body)
		var shape:=CollisionShape3D.new();var box:=BoxShape3D.new();box.size=Vector3(.27,.42,.016);shape.shape=box;shape.position=Vector3(0,.21,0);body.add_child(shape)
		var label:=Label3D.new();label.font=font;label.font_size=72;label.pixel_size=.0015;label.position=Vector3(0,.355,.012);label.modulate=Color(1,.63,.27);label.outline_size=0;root.add_child(label)
		var name_label:=Label3D.new();name_label.font=font;name_label.font_size=26;name_label.pixel_size=.0012;name_label.position=Vector3(0,.055,.012);name_label.modulate=Color(.95,.82,.61);name_label.outline_size=0;root.add_child(name_label)
		var preview:=MeshInstance3D.new();var quad:=QuadMesh.new();quad.size=Vector2(.225,.22);preview.mesh=quad;preview.position=Vector3(0,.205,.012);root.add_child(preview)
		var mat:=ShaderMaterial.new();mat.shader=load("res://collection/plaque_etch.gdshader");preview.material_override=mat
		var border:=MeshInstance3D.new();var frame:=QuadMesh.new();frame.size=Vector2(.268,.419);border.mesh=frame;border.position=Vector3(0,.21,.015);root.add_child(border)
		var border_mat:=ShaderMaterial.new();border_mat.shader=load("res://collection/archive_atlas.gdshader");border_mat.set_shader_parameter("atlas",load("res://assets/collection/art/archive_atlas.png"));border_mat.set_shader_parameter("tile",2.0);border.material_override=border_mat
		card_nodes.append({"node":root,"label":label,"name":name_label,"body":body,"preview":preview,"mat":mat,"border":border_mat})
		card_hover.append(0.0)
	_refresh_cards()
	_setup_signal_materials(selector)

func _setup_signal_materials(node:Node)->void:
	if node is MeshInstance3D and (str(node.name).contains("ArchiveSignalRail") or str(node.name).contains("CarrierTrim")):
		var mat:=ShaderMaterial.new();mat.shader=load("res://collection/archive_atlas.gdshader");mat.set_shader_parameter("atlas",load("res://assets/collection/art/archive_atlas.png"));mat.set_shader_parameter("crop",Vector2(1,.055));mat.set_shader_parameter("center",Vector2(.5,.450));node.material_override=mat;signal_materials.append(mat)
	for child in node.get_children():_setup_signal_materials(child)

func _smoke_glass(node:Node)->void:
	if node is MeshInstance3D and str(node.name).contains("EtchedGlass"):
		var mat:=StandardMaterial3D.new();mat.albedo_color=Color(.035,.025,.016,.26);mat.transparency=BaseMaterial3D.TRANSPARENCY_ALPHA;mat.metallic=.1;mat.roughness=.2;node.material_override=mat
	for child in node.get_children():_smoke_glass(child)

func update_hover_ui()->bool:
	if control_driver.index>=0 or host.drag_kind!=0 or host.pressed>=0 or state!="idle":
		host.tooltip.hide();help_index=-1;help_since_ms=Time.get_ticks_msec();help_owned=true;host.hover=-1
		return true
	if selector_hit.is_empty():
		if card_hint_active:card_hint_active=false;host.hover=-2
		if current and state=="idle" and selector_amount<.01:
			var index:int=hit_control(pointer_position())
			var info:Dictionary=control_driver.profile(index)
			if not info.is_empty():
				var pointer:=pointer_position()
				if index!=help_index or pointer.distance_to(help_point)>5:
					help_index=index;help_point=pointer;help_since_ms=Time.get_ticks_msec()
				help_owned=true;host.hover=-1
				if Time.get_ticks_msec()-help_since_ms<450:host.tooltip.hide();return true
				host.tooltip.visible=true;host.toast.hide()
				host.tooltip_title.text=str(info.label)
				host.tooltip_title.add_theme_color_override("font_color",Color(.95,.86,.68))
				var value:Variant=current.play.gauge_value() if info.gesture=="gauge" else current.play.value(str(info.key))
				host.tooltip_text.text=str(info.hint)
				host.tooltip.reset_size()
				var band:=control_band()
				host.tooltip.position=Vector2(clampf(band.get_center().x-host.tooltip.size.x*.5,12,host.canonical_size.x-host.tooltip.size.x-12),band.position.y-host.tooltip.size.y-28)
				return true
		if help_owned:host.tooltip.hide();host.hover=-2;help_owned=false;help_index=-1
		return false
	card_hint_active=true;host.hover=-1;host.tooltip.visible=true
	var body:StaticBody3D=selector_hit.collider
	var point:Vector3=pressure_strip.global_position+Vector3(-.68,.62,1.0)
	if body.has_meta("card_slot"):
		var slot:int=body.get_meta("card_slot")
		var item:Dictionary=registry[(browse_start+slot)%registry.size()]
		host.tooltip_title.text=str(item.id)+" · "+str(item.title);host.tooltip_text.text="点击选择 · 滚轮浏览其他装置"
		point=card_nodes[slot].node.global_position+Vector3(0,.45,0)
	elif body.has_meta("index_spindle"):
		host.tooltip_title.text="档案索引轴";host.tooltip_text.text="拖动滚轴或滚动鼠标，翻阅装置档案";point=index_spindle.global_position+Vector3(0,.20,0)
	else:
		host.tooltip_title.text="装置档案";host.tooltip_text.text="点击环沿，展开机械铭牌"
	var screen:Vector2=host.camera.unproject_position(point)
	host.tooltip.position=Vector2(clampf(screen.x-130,10,host.canonical_size.x-350),screen.y-75)
	return true

func control_band()->Rect2:
	var points:Array[Vector2]=[]
	for control in custom_controls:_screen_points(control.node,points)
	for i in [0,6]:_screen_points(host.buttons[i].mount,points)
	if points.is_empty():return Rect2(host.canonical_size*.5,Vector2.ONE)
	var band:=Rect2(points[0],Vector2.ZERO)
	for p in points:band=band.expand(p)
	return band.grow(12)

func _refresh_cards()->void:
	for i in range(card_nodes.size()):
		var entry:Dictionary=registry[(browse_start+i)%registry.size()]
		var card:Dictionary=card_nodes[i];card.label.text=entry.id;card.name.text=entry.title
		card.label.modulate=Color(1,.3,.12) if entry.id==active_id else Color(1,.67,.33)
		card.preview.visible=ResourceLoader.exists(entry.thumbnail)
		if card.preview.visible:card.mat.set_shader_parameter("portrait",load(entry.thumbnail))

func toggle_selector()->void:
	if closing:return
	control_driver.cancel()
	_acknowledge_intro()
	if selector_target>0 or selector_wait:
		selector_wait=false;selector_target=0
	else:
		if current:
			current.stow();selector_wait=true;selector_target=.13
		elif host.openness>.001 or host.explosion>.001:
			host.overload=0;host.change_pose(0,0,2.3);host.effects.trigger("close");selector_wait=true;selector_target=.13
		else:selector_target=1
	host.sound("click",.82)

func toggle_rotation()->void:
	host.rotation_enabled=not host.rotation_enabled
	host.message("展示旋转已开启" if host.rotation_enabled else "展示旋转已暂停",1.5)

func _ray(point:Vector2,mask:int)->Dictionary:
	var start:Vector3=host.camera.project_ray_origin(point)
	var query:=PhysicsRayQueryParameters3D.create(start,start+host.camera.project_ray_normal(point)*60,mask)
	return host.get_world_3d().direct_space_state.intersect_ray(query)

func _selector_ray(point:Vector2)->Dictionary:
	var hit:=_ray(point,31)
	if hit.is_empty():return hit
	var body:Node=hit.collider
	return hit if body.has_meta("entry") or body.has_meta("card_slot") or body.has_meta("index_spindle") else {}

func browse(direction:int)->void:
	if browse_time>=0 or selector_amount<.99 or state!="idle":return
	browse_pending=direction;browse_time=0;host.sound("click",1.10)

func consume_input(event:InputEvent)->bool:
	if control_driver.consume(event):return true
	if event is InputEventMouseMotion and index_dragging:
		index_drag_distance+=event.relative.y
		if absf(index_drag_distance)>14:browse(1 if index_drag_distance>0 else -1);index_drag_distance=0
		return true
	if event is InputEventKey and event.pressed and event.keycode==KEY_TAB:
		if not event.echo:toggle_selector()
		return true
	if event is InputEventKey and event.pressed and event.keycode==KEY_ESCAPE and state in ["loading","warming"]:
		_abandon_loading();ticket+=1;requested="";state="idle";selector_target=0;host.message("已取消准备，保留当前装置",1.5);return true
	if event is InputEventKey and event.pressed and event.keycode==KEY_ESCAPE and selector_target>0:
		_acknowledge_intro();selector_wait=false;selector_target=0;return true
	if event is InputEventMouseButton:
		if event.button_index in [MOUSE_BUTTON_WHEEL_UP,MOUSE_BUTTON_WHEEL_DOWN] and selector_amount>.8:
			if event.pressed:
				browse(1 if event.button_index==MOUSE_BUTTON_WHEEL_DOWN else -1)
			return true
		if event.button_index==MOUSE_BUTTON_LEFT:
			if not event.pressed and index_dragging:index_dragging=false;return true
			var hit:=_selector_ray(event.position)
			if event.pressed and not hit.is_empty() and hit.collider.has_meta("index_spindle"):
				index_dragging=true;index_drag_distance=0;return true
			var slot:=-2
			if not hit.is_empty():slot=-1 if hit.collider.has_meta("entry") else int(hit.collider.get_meta("card_slot",-2))
			if event.pressed and slot>=-1 and browse_time<0:pointer_down=slot;return true
			if not event.pressed and pointer_down>=-1:
				if slot==pointer_down:
					if slot==-1:toggle_selector()
					else:selected_slot=slot;request_model(str(registry[(browse_start+slot)%registry.size()].id))
				pointer_down=-2;return true
	return false

func _build_controls()->void:
	if custom_panel:custom_panel.queue_free()
	custom_controls.clear()
	if active_id=="B":return
	custom_panel=Node3D.new();add_child(custom_panel)
	var plate:Node3D=selector.find_child("S_PANEL",true,false).duplicate();custom_panel.add_child(plate);plate.show()
	_add_control_colliders(plate,-1,2)
	var definition:=_definition(active_id)
	var layout:Array=[1,2,5,3,4]
	if active_id in ["J","L"]:layout=[1,5,2,3,4]
	elif active_id=="M":layout=[1,2,3,5,4]
	elif active_id=="N":layout=[5,1,2,3,4]
	for i in range(1,6):
		var kind:String=definition.widgets[i-1]
		var profile:Dictionary=control_driver.profile(i)
		var template:Node3D=widget_templates[kind]
		if control_library and not profile.is_empty():
			var shape:String=profile.gesture
			if shape=="slider":shape+="_"+str(profile.get("axis","y"))
			var authored:Node3D=control_library.find_child("CTRL_"+shape,true,false)
			if authored:template=authored
		var widget:Node3D=template.duplicate();custom_panel.add_child(widget);widget.show()
		var slot:int=layout.find(i)+1
		var mount:Node3D=host.buttons[slot].mount
		# The outgoing cassette is already retracted during _commit. Its live
		# transform would bury new controls inside the ivory base panel.
		var home:Transform3D=legacy_mount_homes[slot-1]
		var point:Vector3=mount.get_parent().to_global(home.origin)
		widget.global_position=point;widget.look_at(point+Vector3(point.x,0,point.z).normalized(),Vector3.UP,true)
		_add_control_colliders(widget,i,16)
		_skin_control(widget)
		var moving:Array=[]
		for node in widget.get_children():
			var label:String=str(node.name)
			if label.contains("WidgetSocket") or label.contains("WidgetRim"):continue
			if node is Node3D:moving.append({"node":node,"home":node.transform})
		var initial:Variant=current.play.value(str(profile.key)) if current and profile.has("key") else 0.0
		var initial_turn:=0.0
		if profile.get("gesture","") in ["rotary","crank"]:
			initial_turn=float(initial)*TAU if profile.gesture=="crank" else inverse_lerp(float(profile.min),float(profile.max),float(initial))*PI*1.6
			if active_id=="F" and profile.gesture=="rotary":initial_turn-=PI*.8
		custom_controls.append({"node":widget,"home":widget.transform,"index":i,"kind":kind,"press":0.0,"moving":moving,"turn":initial_turn,"turn_target":initial_turn,"input_value":initial})

func hit_control(point:Vector2)->int:
	if active_id=="B" or state!="idle":return -1
	if point.x<0 or point.y<0 or point.x>host.canonical_size.x or point.y>host.canonical_size.y:return -1
	var archive_hit:=_selector_ray(point)
	if not archive_hit.is_empty() and archive_hit.collider.has_meta("entry"):return -1
	var hit:=_ray(point,22)
	var direct:int=int(hit.collider.get_meta("collection_action",-1)) if not hit.is_empty() else -1
	if direct>=0:return direct
	var chosen:=-1;var nearest:=INF
	for c in custom_controls:
		var points:Array[Vector2]=[];_screen_points(c.node,points)
		if points.is_empty():continue
		var box:=Rect2(points[0],Vector2.ZERO)
		for p in points:box=box.expand(p)
		if not box.grow(9).has_point(point):continue
		var distance:float=point.distance_squared_to(box.get_center())
		if distance<nearest:nearest=distance;chosen=int(c.index)
	return chosen

func _add_control_colliders(node:Node,index:int,layer:int)->void:
	if node is MeshInstance3D:
		var body:=StaticBody3D.new();body.collision_layer=layer;body.collision_mask=0;body.set_meta("collection_action",index)
		var key:int=node.mesh.get_instance_id()
		if not control_shape_cache.has(key):control_shape_cache[key]=node.mesh.create_trimesh_shape()
		var shape:=CollisionShape3D.new();shape.shape=control_shape_cache[key];body.add_child(shape);node.add_child(body)
	for child in node.get_children():
		if not child is StaticBody3D:_add_control_colliders(child,index,layer)

func _prepare_control_shapes(node:Node)->void:
	if node is MeshInstance3D:
		var key:int=node.mesh.get_instance_id()
		if not control_shape_cache.has(key):control_shape_cache[key]=node.mesh.create_trimesh_shape()
	for child in node.get_children():_prepare_control_shapes(child)

func prewarm_shared_surfaces()->void:
	if not host.native_mode or RenderingServer.get_rendering_device()==null:return
	var started:=Time.get_ticks_msec()
	_prepare_control_shapes(control_library)
	_prepare_control_shapes(selector.find_child("S_PANEL",true,false))
	var view:=SubViewport.new();view.size=Vector2i(96,96);view.own_world_3d=true;view.transparent_bg=true;view.msaa_3d=Viewport.MSAA_4X;view.render_target_update_mode=SubViewport.UPDATE_ALWAYS;add_child(view)
	var scene:=Node3D.new();view.add_child(scene)
	var camera:=Camera3D.new();scene.add_child(camera);camera.position=Vector3(1.4,2.0,4);camera.look_at(Vector3(.65,.8,0));camera.current=true
	var world:=WorldEnvironment.new();world.environment=host.env;scene.add_child(world)
	var library:Node3D=control_library.duplicate();scene.add_child(library);library.show();library.position.y=1.0
	var plate:Node3D=selector.find_child("S_PANEL",true,false).duplicate();scene.add_child(plate);plate.show()
	var base:=MeshInstance3D.new();base.mesh=base_mesh_cache.shared;scene.add_child(base)
	for i in range(base_frames.variants.shared.source_surfaces.size()):base.set_surface_override_material(i,base_materials[int(base_frames.variants.shared.source_surfaces[i])])
	for child in host.get_children():
		if child is AreaLight3D:scene.add_child(child.duplicate())
	for i in range(6):await RenderingServer.frame_post_draw
	view.queue_free()
	print("COLLECTION_SHARED_PREWARM ",Time.get_ticks_msec()-started," ms, shapes=",control_shape_cache.size())

func action_anchor(index:int)->Vector3:
	for c in custom_controls:
		if c.index==index:return c.node.to_global(Vector3(0,0,.045))
	return host.buttons[index].mount.global_position

func dispatch(index:int)->bool:
	if index==6 and (active_id!="B" or state!="idle"):
		request_shutdown();return true
	if state!="idle" or closing:return true
	if index!=6 and (selector_amount>.15 or selector_wait):
		pending_action=index;selector_wait=false;selector_target=0;return true
	if active_id=="B":return false
	action_log.append({"id":active_id,"action":index,"time":Time.get_ticks_msec()})
	for c in custom_controls:
		if c.index==index:
			c.press=1.0
			if c.kind=="knob":c.turn_target+=PI/5
	host.sound("click",.92+index*.04)
	if index==0:
		if host.power_target>.5:current.stow();sleep_pending=true
		else:host.power_target=1;current.effect.resume()
	elif index==5:
		if active_id=="N":current.effect.orbit_time+=.7
		else:toggle_rotation()
	else:
		host.power_target=1;current.activate(index)
		host.sound("assemble" if index==4 else "explode" if index==3 else "open" if index==1 else "overload")
	host.message(str(_definition(active_id).actions[index]),1.8)
	return true

func request_model(id:String)->void:
	if closing:return
	if id==active_id and state=="idle":_acknowledge_intro();selector_target=0;return
	if state not in ["idle","loading"]:return
	var definition:=_definition(id)
	if definition.is_empty():return
	control_driver.cancel()
	_acknowledge_intro()
	_abandon_loading()
	ticket+=1;requested=id;state="loading";state_time=0;last_error=""
	read_time=0
	prepare_started=Time.get_ticks_msec();load_metrics={"id":id,"started_ms":prepare_started}
	if id=="B":_begin_stow();return
	var error:=ResourceLoader.load_threaded_request(definition.scene,"PackedScene",false)
	if error!=OK:_fail("装置资源无法准备");return
	host.message("正在准备 · "+str(definition.title),2)

func _abandon_loading()->void:
	if state=="loading" and requested!="B":
		var definition:=_definition(requested)
		if not definition.is_empty() and str(definition.scene) not in abandoned_loads:abandoned_loads.append(str(definition.scene))

func _drain_abandoned_loads()->void:
	for path in abandoned_loads.duplicate():
		if state=="loading" and _definition(requested).get("scene","")==path:abandoned_loads.erase(path);continue
		var status:=ResourceLoader.load_threaded_get_status(path)
		if status in [ResourceLoader.THREAD_LOAD_LOADED,ResourceLoader.THREAD_LOAD_FAILED]:
			ResourceLoader.load_threaded_get(path);abandoned_loads.erase(path)

func _begin_stow()->void:
	if selected_slot>=0 and read_time<.70:state="reading";return
	state="stowing";state_time=0
	load_metrics.stow_started_ms=Time.get_ticks_msec()-prepare_started
	if current:current.stow()
	else:
		host.overload=0;host.change_pose(0,0,2.5);host.effects.trigger("close");host.power_target=0
	host.sound("seal_close")

func _prepare(packed:PackedScene,definition:Dictionary,version:int)->void:
	state="warming"
	load_metrics.resource_ready_ms=Time.get_ticks_msec()-prepare_started
	var raw:Variant=JSON.parse_string(FileAccess.get_file_as_string(definition.metadata))
	if not raw is Dictionary or raw.get("id","")!=definition.id or not raw.has_all(["parts","controls","motions","sockets"]):_fail("装置数据不完整");return
	var warming:=SubViewport.new();warm_view=warming;warming.size=Vector2i(64,64);warming.own_world_3d=true;warming.transparent_bg=true;warming.msaa_3d=Viewport.MSAA_4X;warming.render_target_update_mode=SubViewport.UPDATE_ALWAYS;add_child(warming)
	var scene:=Node3D.new();warming.add_child(scene)
	var camera:=Camera3D.new();scene.add_child(camera);camera.position=Vector3(.5,3.5,6);camera.look_at(Vector3(0,1.7,0));camera.current=true
	var environment:=WorldEnvironment.new();environment.environment=host.env;scene.add_child(environment)
	var setup_started:=Time.get_ticks_msec()
	var candidate:Node3D=load("res://collection/module.gd").new();prepared=candidate;scene.add_child(candidate);candidate.setup(host,raw,packed);candidate.set_interactive(false)
	load_metrics.setup_ms=Time.get_ticks_msec()-setup_started
	var gpu_started:=Time.get_ticks_msec()
	if candidate.play.instrument:
		candidate.openness=1;candidate.play.instrument.physics.theta=candidate.play.instrument.physics.RELEASE;candidate.apply_pose()
		candidate.effect.f_visuals.force_warm=true;candidate.effect.tick(0)
	if candidate.play.g_instrument:
		candidate.openness=1;candidate.apply_pose();candidate.effect.g_visuals.force_warm=true;candidate.effect.tick(0)
	for i in range(4):await RenderingServer.frame_post_draw
	if candidate.play.instrument:
		candidate.openness=0;candidate.play.instrument.physics.transport(0,0,10);candidate.apply_pose()
		candidate.effect.f_visuals.force_warm=false;candidate.effect.tick(0)
		load_metrics["F_all_effect_pools_warmed"]=true
	if candidate.play.g_instrument:
		candidate.openness=0;candidate.apply_pose();candidate.effect.g_visuals.force_warm=false;candidate.effect.tick(0)
		load_metrics["G_all_effect_pools_warmed"]=true
	load_metrics.gpu_warm_ms=Time.get_ticks_msec()-gpu_started
	if version!=ticket or closing:
		candidate.queue_free();warming.queue_free()
		if prepared==candidate:prepared=null
		if warm_view==warming:warm_view=null
		return
	candidate.reparent(self,false);candidate.hide();warming.queue_free();warm_view=null
	_begin_stow()

func _fail(message:String)->void:
	last_error=message;state="idle";requested="";host.message(message+" · 保留当前装置",3)
	if prepared:prepared.queue_free();prepared=null

func _legacy_set_visible(enabled:bool)->void:
	host.turntable.visible=enabled;host.effects.visible=enabled
	_set_bodies(legacy_bodies,enabled);_set_bodies(legacy_control_bodies,enabled)
	for i in range(1,6):host.buttons[i].mount.visible=enabled
	host.effects.pressure.compute_effect.enabled=enabled
	host.effects.pressure.idle_controller.compositor.enabled=enabled

func _wrap_scan(node:Node)->void:
	if node is MeshInstance3D:
		for i in range(node.mesh.get_surface_count()):
			var original:Material=node.get_active_material(i)
			var material:ShaderMaterial
			if original is ShaderMaterial:material=original.duplicate()
			elif original is StandardMaterial3D:
				material=ShaderMaterial.new();material.shader=load("res://collection/surface.gdshader");material.set_shader_parameter("tint",original.albedo_color);material.set_shader_parameter("metallic",original.metallic);material.set_shader_parameter("roughness",original.roughness)
				material.set_shader_parameter("has_color",original.albedo_texture!=null);material.set_shader_parameter("has_roughness",original.roughness_texture!=null);material.set_shader_parameter("has_normal",original.normal_texture!=null)
				if original.albedo_texture:material.set_shader_parameter("color_map",original.albedo_texture)
				if original.roughness_texture:material.set_shader_parameter("roughness_map",original.roughness_texture)
				if original.normal_texture:material.set_shader_parameter("normal_map",original.normal_texture)
			else:continue
			var source_code:String=material.shader.code
			var shader:Shader=legacy_scan_shaders.get(source_code)
			if shader:
				material.shader=shader;scan_overrides.append({"node":node,"surface":i,"material":original});scan_materials.append(material);node.set_surface_override_material(i,material);continue
			shader=Shader.new();var code:String=source_code
			var header:=code.find(";")+1
			code=code.insert(header,"\nuniform float collection_cut=100.0;\nvarying float collection_y;\n")
			var re:=RegEx.new();re.compile("void\\s+vertex\\s*\\(\\s*\\)\\s*\\{")
			var match_vertex:=re.search(code)
			if match_vertex:code=code.insert(match_vertex.get_end(),"collection_y=(MODEL_MATRIX*vec4(VERTEX,1.0)).y;")
			else:code+="\nvoid vertex(){collection_y=(MODEL_MATRIX*vec4(VERTEX,1.0)).y;}\n"
			re.compile("void\\s+fragment\\s*\\(\\s*\\)\\s*\\{")
			var match_fragment:=re.search(code)
			if match_fragment:code=code.insert(match_fragment.get_end(),"if(collection_y>collection_cut) discard;")
			shader.code=code;material.shader=shader
			legacy_scan_shaders[source_code]=shader
			scan_overrides.append({"node":node,"surface":i,"material":original});scan_materials.append(material);node.set_surface_override_material(i,material)
	for child in node.get_children():_wrap_scan(child)

func _restore_scan()->void:
	for item in scan_overrides:item.node.set_surface_override_material(item.surface,item.material)
	scan_overrides.clear();scan_materials.clear()

func _set_scan(value:float)->void:
	if current:current.set_scan(value)
	else:
		if scan_materials.is_empty():_wrap_scan(host.turntable)
		for mat in scan_materials:mat.set_shader_parameter("collection_cut",lerpf(3.9,.59,value))

func _commit()->void:
	var commit_start:=Time.get_ticks_msec()
	transition_vfx.finish()
	if current:current.queue_free();current=null
	_restore_scan();_legacy_set_visible(false)
	active_id=requested;requested=""
	if active_id=="B":
		_set_base_frame("helios");_legacy_set_visible(true);_set_scan(1.0)
		host.effects.hide();_legacy_panel_depth(.36)
	else:
		current=prepared;prepared=null;current.show();current.set_scan(1.0);current.stowing=true;current.effect.request_quiet();current.effect.quiet_gain=0;current.effect.tick(0);current.set_interactive(false);_set_base_frame("shared")
	load_metrics["commit_base_ms"]=Time.get_ticks_msec()-commit_start
	var control_start:=Time.get_ticks_msec()
	_build_controls();_update_actions();_refresh_cards();state="revealing";state_time=0
	load_metrics["commit_controls_ms"]=Time.get_ticks_msec()-control_start
	if custom_panel:custom_panel.position.z=-.36
	transition_vfx.begin(current.asset if current else host.turntable);transition_vfx.update(1.0,true,0)
	host.power_target=1;host.sound("wake")
	load_metrics["commit_total_ms"]=Time.get_ticks_msec()-commit_start

func _legacy_panel_depth(depth:float)->void:
	for i in range(1,6):
		var pose:Transform3D=legacy_mount_homes[i-1];pose.origin.z-=depth;host.buttons[i].mount.transform=pose

func _update_actions()->void:
	var definition:=_definition(active_id)
	host.menu.set_item_text(host.menu.get_item_index(0),"MagicDesk 0.3.0 · "+active_id+" "+str(definition.title))
	host.TITLES=definition.actions.duplicate()
	host.HINTS=[]
	for i in range(definition.actions.size()):
		host.HINTS.append(str(i+1)+" · "+str(definition.actions[i]))
		var index:int=host.menu.get_item_index(10+i)
		if index>=0:host.menu.set_item_text(index,str(i+1)+"   "+str(definition.actions[i]))
	host.get_window().title="MagicDesk · "+str(definition.title)

func request_shutdown()->bool:
	if active_id=="B" and state=="idle":return false
	if closing:return true
	control_driver.cancel()
	_abandon_loading();closing=true;ticket+=1;requested="";selector_target=0;state="shutdown_wait"
	selector_wait=false;scanner_target=0;transition_vfx.finish()
	if current:current.stow()
	else:host.change_pose(0,0,2.3);host.effects.trigger("close");host.power_target=0
	host.message("装置收束 · 准备关闭",3)
	return true

func tick(delta:float)->void:
	state_time+=delta
	_drain_abandoned_loads()
	if read_time>=0:read_time+=delta
	if selector_wait:
		var ready:bool=current.settled() if current else host.openness<.001 and host.explosion<.001
		if ready:selector_wait=false;selector_target=1
	var previous_amount:float=selector_amount
	selector_amount=move_toward(selector_amount,selector_target,delta/float(selector_data.get("selector_duration",2.0)))
	if selector_amount>previous_amount:
		if previous_amount<.10 and selector_amount>=.10:host.sound("click",.62)
		if previous_amount<.31 and selector_amount>=.31:host.sound("open",.70)
		if previous_amount<.995 and selector_amount>=.995:host.sound("click",.9)
	elif selector_amount<previous_amount:
		if previous_amount>.80 and selector_amount<=.80:host.sound("click",.75)
		if previous_amount>.30 and selector_amount<=.30:host.sound("seal_close",.85)
	if previous_amount>0 and selector_amount==0 and state=="idle" and current:current.stowing=false;current.effect.resume()
	for c in selector_controls:
		var position:float=selector_amount*(c.samples.size()-1);var lo:=int(position)
		var desired:Transform3D=c.samples[lo].interpolate_with(c.samples[mini(lo+1,c.samples.size()-1)],position-lo)
		if c.node.transform!=desired:c.node.transform=desired
	scanner_amount=move_toward(scanner_amount,scanner_target,delta/0.65)
	for c in scanner_controls:
		var frame:float=scanner_amount*(c.samples.size()-1);var low:=int(frame);c.node.transform=c.samples[low].interpolate_with(c.samples[mini(low+1,c.samples.size()-1)],frame-low)
	for item in scanner_aims:
		item.node.transform=item.home
		if scanner_amount>.6:
			var original:Transform3D=item.node.global_transform
			var pos:Vector3=original.origin;var radial:=Vector3(pos.x,0,pos.z).normalized()
			var target:Vector3=radial*transition_vfx.radius+Vector3(0,transition_vfx.front,0)
			var aimed:=Transform3D(Basis.looking_at(target-pos,Vector3.UP,true),pos)
			item.node.global_transform=original.interpolate_with(aimed,smoothstep(.6,1.,scanner_amount))
	if browse_time>=0:
		var previous:float=browse_time;browse_time+=delta
		if previous<.24 and browse_time>=.24:browse_start=posmod(browse_start+browse_pending,registry.size());_refresh_cards()
		index_rotation+=delta*browse_pending*TAU/1.9
		if browse_time>=.48:browse_time=-1;browse_pending=0;host.sound("click",.9)
	if index_spindle and index_spindle.rotation.y!=index_rotation:index_spindle.rotation.y=index_rotation
	if archive_guide:
		archive_guide.visible=selector_amount>.95 and state=="idle" and not closing
		if archive_guide.visible:
			var anchor:Vector2=host.camera.unproject_position(card_nodes[0].node.to_global(Vector3(-.13,.48,0)))
			archive_guide.position=Vector2(clampf(anchor.x,12,host.canonical_size.x-archive_guide.size.x-12),anchor.y-archive_guide.size.y-10)
	for c in card_nodes:c.body.collision_layer=8 if selector_amount>.9 else 0
	var cursor:=pointer_position()
	var hit:=_selector_ray(cursor)
	selector_hit=hit
	for i in range(card_nodes.size()):
		var hovered:bool=not hit.is_empty() and int(hit.collider.get_meta("card_slot",-1))==i
		card_hover[i]=move_toward(card_hover[i],1.0 if hovered else 0.0,delta*6)
		var fold:float=sin(clampf(browse_time/.48,0,1)*PI)*1.48 if browse_time>=0 else 0.0
		var tilt:float=(fold-card_hover[i]*.12)*smoothstep(.80,.99,selector_amount)
		var selected:bool=i==selected_slot and state!="idle" and read_time>=0
		if selected:tilt+=.23*smoothstep(.0,.6,read_time)
		if tilt!=0:
			var pivot:=Vector3(0,.02,0);var basis:=Basis(Vector3.RIGHT,tilt);card_nodes[i].node.transform*=Transform3D(basis,pivot-basis*pivot)
		card_nodes[i].border.set_shader_parameter("gain",2.5 if selected else .55+card_hover[i]*1.2)
		card_nodes[i].mat.set_shader_parameter("gain",1.4 if selected else .70+card_hover[i]*.45)
	for material in signal_materials:
		material.set_shader_parameter("gain",2.5 if state!="idle" else .25*selector_amount)
		material.set_shader_parameter("travel",-maxf(0,read_time)*.8)
	seam.visible=not hit.is_empty() or selector_amount>.01 or state!="idle" or intro_pending
	for c in custom_controls:
		if int(c.index)==3 and current:c["input_value"]=current.play.gauge_value()
		if active_id=="G" and int(c.index)==2 and current:c["input_value"]=current.play.number("fold")
		if not control_driver.held(int(c.index)):c.press=move_toward(c.press,0,delta*4)
		if c.node.transform!=c.home:c.node.transform=c.home
		c.turn=move_toward(c.turn,c.turn_target,delta*4)
		for item in c.moving:
			var movement:=Transform3D.IDENTITY
			var profile:Dictionary=control_driver.profile(int(c.index))
			var gesture:String=profile.get("gesture","")
			var input_value:Variant=c.get("input_value",0.0)
			if gesture in ["rotary","crank"]:movement.basis=Basis(Vector3.BACK,c.turn)
			elif gesture=="joystick" and input_value is Vector2:movement.basis=Basis.from_euler(Vector3(-input_value.y*.3,input_value.x*.3,0))
			elif gesture=="gauge":movement.basis=Basis(Vector3.BACK,lerpf(-1.0,1.0,float(input_value)))
			elif gesture=="service":movement.basis=Basis(Vector3.UP,float(input_value)*.26)
			elif gesture in ["slider","pump","detent"]:
				var normalized:float=inverse_lerp(float(profile.min),float(profile.max),float(input_value))
				if gesture=="detent":movement.basis=Basis(Vector3.RIGHT,(normalized-.5)*.65)
				else:movement.origin=Vector3((normalized-.5)*.075,0,0) if profile.get("axis","y")=="x" else Vector3(0,(normalized-.5)*.075,0)
			elif c.kind=="knob":movement.basis=Basis(Vector3.BACK,c.turn)
			elif c.kind=="lever":
				var pivot:=Vector3(0,-.025,.03);movement=Transform3D(Basis(Vector3.RIGHT,-c.press*.36),pivot)*Transform3D(Basis.IDENTITY,-pivot)
			elif c.kind=="rocker":movement.basis=Basis(Vector3.RIGHT,c.press*.16)
			else:movement.origin.z=-c.press*.014
			var desired:Transform3D=movement*item.home
			if item.node.transform!=desired:item.node.transform=desired
	regions_clock+=delta
	if regions_clock>.05:native_regions=_input_regions();regions_clock=0.0
	if current:
		current.advance_yaw(delta,host.angle)
		current.tick(delta,host.power)
	if sleep_pending and current and current.settled():host.power_target=0;sleep_pending=false
	if pending_action>=0 and selector_amount==0:
		var action:=pending_action;pending_action=-1;host.activate(action)
	match state:
		"reading":
			if read_time>=.70:_begin_stow()
		"loading":
			var definition:=_definition(requested)
			var status:int=ResourceLoader.load_threaded_get_status(definition.scene)
			if status==ResourceLoader.THREAD_LOAD_LOADED:_prepare(ResourceLoader.load_threaded_get(definition.scene),definition,ticket)
			elif status==ResourceLoader.THREAD_LOAD_FAILED:_fail("装置加载失败")
		"stowing":
			var settled:bool=current.settled() if current else host.openness<.001 and host.explosion<.001 and host.power<.05
			if settled:
				state="scan_rise";state_time=0;scanner_target=1;transition_vfx.begin(current.asset if current else host.turntable)
		"scan_rise":
			if scanner_amount>.999:state="archiving";state_time=0;load_metrics.archive_started_ms=Time.get_ticks_msec()-prepare_started;host.sound("assemble")
		"archiving":
			var amount:=smoothstep(0.0,ARCHIVE_SECONDS,state_time);_set_scan(amount);transition_vfx.update(amount,false,delta)
			var depth:=.36*smoothstep(.35,1.2,state_time)
			if custom_panel:custom_panel.position.z=-depth
			else:_legacy_panel_depth(depth)
			if state_time>=ARCHIVE_SECONDS:_commit()
		"revealing":
			var amount:=1.0-smoothstep(0.0,RECAST_SECONDS,state_time);_set_scan(amount);transition_vfx.update(amount,true,delta)
			var depth:=.36*(1.0-smoothstep(.55,1.65,state_time))
			if custom_panel:custom_panel.position.z=-depth
			else:_legacy_panel_depth(depth)
			if state_time>=RECAST_SECONDS:
				if current:current.set_scan(0);current.set_interactive(true);current.stowing=false;current.effect.resume()
				else:_restore_scan();host.effects.show();host.effects.trigger("ignition")
				transition_vfx.finish();scanner_target=0;state="sealing";selector_target=0;host.sound("seal_close")
		"sealing":
			if scanner_amount<.001 and selector_amount<.001:
				state="idle";selected_slot=-1;read_time=-1;host.message(str(_definition(active_id).title)+" · 已就位",2)
				load_metrics.total_ms=Time.get_ticks_msec()-prepare_started;print("COLLECTION_LOAD ",JSON.stringify(load_metrics))
		"shutdown_wait":
			var settled:bool=current.settled() if current else host.openness<.001 and host.explosion<.001
			if settled:state="shutdown_final";host._start_final_shutdown()

func diagnostics()->Dictionary:
	return {"active":active_id,"state":state,"requested":requested,"selector":selector_amount,"base_instances":_count_bases(host),"base_bounds":str(base_display.mesh.get_aabb()),"error":last_error,"module":current.diagnostics() if current else {"id":"B","parts":host.parts.size()},"play":current.play.diagnostics() if current else {},"actions":action_log,"load_metrics":load_metrics}

func pointer_position()->Vector2:
	return host.native_cursor if host.native_mode else host.get_viewport().get_mouse_position()

func _skin_control(node:Node)->void:
	if node is MeshInstance3D:
		for surface in range(node.mesh.get_surface_count()):
			var material:Material=node.get_active_material(surface)
			if material and host.surface_materials.has(material.resource_name):node.set_surface_override_material(surface,host.surface_materials[material.resource_name])
	for child in node.get_children():_skin_control(child)

func _screen_points(node:Node,points:Array[Vector2])->void:
	if node is Node3D and not node.is_visible_in_tree():return
	if node is MeshInstance3D:
		var box:AABB=node.get_aabb()
		for x in [0,1]:
			for y in [0,1]:
				for z in [0,1]:points.append(host.camera.unproject_position(node.to_global(box.position+box.size*Vector3(x,y,z))))
	for child in node.get_children():_screen_points(child,points)

func _input_regions()->Array[Rect2i]:
	var roots:Array[Node]=[]
	for label in selector_data.get("click_surfaces",[]):roots.append(selector.find_child(label,true,false))
	if selector_amount>.8:
		if index_spindle:roots.append(index_spindle)
		for card in card_nodes:roots.append(card.node)
	if current and state=="idle":
		for control in custom_controls:roots.append(control.node)
	var regions:Array[Rect2i]=[]
	for node in roots:
		if node==null:continue
		var points:Array[Vector2]=[];_screen_points(node,points)
		if points.is_empty():continue
		var box:=Rect2(points[0],Vector2.ZERO)
		for point in points:box=box.expand(point)
		regions.append(Rect2i(box.grow(10)))
	return regions

func _count_bases(node:Node)->int:
	var count:=1 if str(node.name)=="BASE_FIXED" else 0
	for child in node.get_children():count+=_count_bases(child)
	return count
