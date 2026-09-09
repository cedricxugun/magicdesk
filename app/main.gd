extends Node3D

var TITLES = ["唤醒 / 休眠", "绽放 / 闭合", "过载脉冲", "零件展开", "组装 / 收拢", "旋转 / 暂停", "收拢并退出"]
var HINTS = ["1 · 电源与核心灯光", "2 · 六瓣外壳同步展开", "3 · 转环加速，释放能量脉冲", "4 · 按机构层次拆分真实零件", "5 · 从当前位置收拢并锁定", "6 · 只旋转上部，底座保持静止", "7 · 泄能、收拢、熄灯后关闭"]
var metadata: Dictionary
var model: Node3D
var turntable: Node3D
var fixed_base: Node3D
var camera: Camera3D
var env: Environment
var core_light: OmniLight3D
var glow_material: StandardMaterial3D
var energy_material: StandardMaterial3D
var core_materials: Array = []
var parts: Array = []
var controls: Array = []
var buttons: Array = []
var meshes: Array[MeshInstance3D] = []
var gyros: Dictionary = {}
var pulse_rings: Array[MeshInstance3D] = []
var openness := 0.0
var explosion := 0.0
var power := 0.0
var power_target := 1.0
var open_target := 0.0
var explode_target := 0.0
var transition: Dictionary = {}
var rotation_enabled := true
var angle := 0.0
var phase := 0.0
var overload := 0.0
var elapsed := 0.0
var muted := false
var zoom := 1.0
var hover := -1
var pressed := -1
var drag_kind := 0
var drag_start := Vector2.ZERO
var window_start := Vector2i.ZERO
var drag_distance := 0.0
var tooltip: PanelContainer
var tooltip_title: Label
var tooltip_text: Label
var toast: Label
var toast_timer := 0.0
var toolbar: HBoxContainer
var menu: PopupMenu
var sound_players: Array[AudioStreamPlayer] = []
var audio_streams:Dictionary={}
var hum: AudioStreamPlayer
var sample_clock := 0.0
var tray: StatusIndicator
var test_mode := false
var demo_mode := false
var capture_dir := ""
var demo_events: Dictionary = {}
var tests: Array = []
var effects: Node3D
var surface_materials: Dictionary = {}
var control_path := ""
var control_stamp := 0
var passthrough_active := false
var hit_polygon := PackedVector2Array()
var presentation: SubViewportContainer
var render_view: SubViewport
var crop_rect := Rect2i()
var desktop_anchor := Vector2i.ZERO
var canonical_size := Vector2i(1920,1400)
var reference_focal_pixels := 1500.0
var native_mode := false
var native_port := 0
var native_cursor := Vector2(-10000,-10000)
var native_bridge: Node
var shutdown_time := -1.0
var display_fade := 1.0
var activation_time := -1.0
var activation_energy := 0.0
var activation_start := 0.0
var closing_time := -1.0
var activation_display_time := -1.0
var mac_desktop := false
var collection:Node3D
var collection_enabled:=true

func opening_fraction(display_time:float)->float:
	if display_time<.40:return 0.0
	if display_time<.85:return .035*smooth01((display_time-.40)/.45)
	# One continuous stroke after unlocking. The previous 84% hand-off stopped
	# the petals before starting a second easing segment, creating a false hitch.
	var u:=clampf((display_time-.85)/2.65,0.0,1.0)
	var quintic:=u*u*u*(10.0+u*(-15.0+6.0*u))
	return .035+.965*quintic

func v3(a: Array) -> Vector3:
	return Vector3(float(a[0]), float(a[1]), float(a[2]))

func q4(a: Array) -> Quaternion:
	return Quaternion(float(a[0]), float(a[1]), float(a[2]), float(a[3])).normalized()

func pose_transform(data: Dictionary) -> Transform3D:
	return Transform3D(Basis(q4(data.q))*Basis.from_scale(v3(data.s)), v3(data.p))

func named(name_string: String) -> Node3D:
	return model.find_child(name_string, true, false) as Node3D

func smooth01(t: float) -> float:
	t = clampf(t, 0.0, 1.0)
	return t * t * (3.0 - 2.0 * t)

func _ready() -> void:
	for arg in OS.get_cmdline_user_args():
		if arg.begins_with("--collection-qa="):
			get_tree().set_meta("collection_skip_intro",true);get_tree().set_meta("collection_no_save",true)
		if arg=="--helios-only":collection_enabled=false
		if arg == "--self-test": test_mode = true
		if arg == "--demo": demo_mode = true
		if arg == "--render-probe":native_mode=true
		if arg.begins_with("--capture="): capture_dir = arg.trim_prefix("--capture=")
		if arg.begins_with("--control="): control_path = arg.trim_prefix("--control=")
		if arg.begins_with("--native-port="):
			native_port=int(arg.trim_prefix("--native-port="));native_mode=true
	mac_desktop = OS.get_name() == "macOS" and not native_mode
	if mac_desktop:
		# Cmd-Q and Dock Quit must finish the same shutdown as the red X.
		get_tree().auto_accept_quit = false
		Engine.max_fps = 60
	if test_mode: get_window().mode=Window.MODE_MINIMIZED
	get_window().transparent = true
	get_window().borderless = true
	get_viewport().transparent_bg = true
	get_tree().root.transparent_bg = true
	get_viewport().use_taa = false
	get_viewport().scaling_3d_scale = 1.0
	get_window().title = "HELIOS · 孵日器"
	var usable := DisplayServer.screen_get_usable_rect()
	if usable.size.x<=0 or usable.size.y<=0:usable=Rect2i(0,0,1920,1040)
	var wh := mini(940, int(usable.size.y * 0.88))
	if mac_desktop:
		canonical_size = Vector2i(mini(1920,usable.size.x),mini(1400,usable.size.y))
	# Reserve enough horizontal desktop space for the open mechanism at its original scale.
	get_window().size = Vector2i(mini(int(wh * 1.70),int(usable.size.x*.94)), wh)
	get_window().position = usable.position + (usable.size - get_window().size) / 2
	reference_focal_pixels = wh/(2.0*tan(deg_to_rad(34.0)*.5))
	desktop_anchor = usable.position + usable.size/2-canonical_size/2
	render_view=get_parent() as SubViewport
	presentation=render_view.get_parent() as SubViewportContainer
	render_view.size=canonical_size
	render_view.transparent_bg=true
	render_view.own_world_3d=true
	render_view.msaa_3d=Viewport.MSAA_4X
	render_view.use_taa=false
	render_view.scaling_3d_scale=1.0
	render_view.render_target_update_mode=SubViewport.UPDATE_ALWAYS
	if native_mode:
		get_window().transparent=false
		get_window().unfocusable=true
		get_window().title="HELIOS Renderer"
		get_window().size=Vector2i(32,32)
		get_window().position=Vector2i(-32000,-32000)
		print("HELIOS_WORKER_HWND ",DisplayServer.window_get_native_handle(DisplayServer.WINDOW_HANDLE))
		crop_rect=Rect2i(Vector2i.ZERO,canonical_size)
		Engine.max_fps=60
	metadata = JSON.parse_string(FileAccess.get_file_as_string("res://assets/mechanism.json"))
	model = load("res://assets/helios_model.glb").instantiate()
	add_child(model)
	turntable = named(metadata.turntable)
	fixed_base = named(metadata.base)
	assert(turntable != null and fixed_base != null, "Mechanism roots missing")
	for d in metadata.parts:
		var n := named(d.name)
		assert(n != null, "Missing real component: " + d.name)
		var explode_path:Array=[]
		for keyframe in d.get("explode_path",[]):explode_path.append({"at":float(keyframe.at),"offset":v3(keyframe.offset)})
		parts.append({"node": n, "home": pose_transform(d.home), "offset": v3(d.offset), "stage": float(d.stage), "spin": float(d.get("explode_spin",d.spin)),"explode_path":explode_path})
	for d in metadata.controls:
		var poses: Array[Transform3D] = []
		for s in d.samples: poses.append(pose_transform(s))
		controls.append({"node": named(d.name), "petal": int(d.petal), "poses": poses})
	for key in metadata.gyro: gyros[key] = named(metadata.gyro[key])
	for d in metadata.buttons:
		var mount := named(d.mount)
		var cap := named(d.cap)
		var indicator := MeshInstance3D.new()
		var lens := SphereMesh.new()
		lens.radius = .008
		lens.height = .016
		lens.radial_segments = 16
		lens.rings = 8
		indicator.mesh = lens
		var indicator_mat := StandardMaterial3D.new()
		indicator_mat.albedo_color = Color(.30,.08,.015)
		indicator_mat.metallic = .3
		indicator_mat.roughness = .22
		indicator_mat.emission_enabled = true
		indicator_mat.emission = Color(1,.26,.025)
		indicator.material_override = indicator_mat
		mount.add_child(indicator)
		indicator.position = Vector3(0,.01,-.152)
		buttons.append({"mount": mount, "cap": cap, "home": pose_transform(d.home), "press": 0.0, "indicator":indicator_mat})
		var body := StaticBody3D.new()
		body.collision_layer = 1
		body.set_meta("button", int(d.index))
		mount.add_child(body)
		var shape := CollisionShape3D.new()
		var cylinder := CylinderShape3D.new()
		cylinder.radius = 0.118
		cylinder.height = 0.024
		shape.shape = cylinder
		shape.position.y = 0.055
		body.add_child(shape)
	_collect_meshes(model)
	_make_studio()
	load("res://quality_lighting.gd").apply(self,env,surface_materials)
	_make_ui()
	_make_audio()
	effects = Node3D.new()
	effects.set_script(load("res://cinematic_effects.gd"))
	add_child(effects)
	effects.setup(self)
	_apply_mechanism()
	_load_settings()
	_fit_window(false)
	await get_tree().physics_frame
	# Keep the native window region stable. Reassigning it during animation causes
	# Windows to repaint/recreate the layered region and can visibly blink.
	get_window().mouse_passthrough_polygon = PackedVector2Array()
	if test_mode: _run_tests()
	if not capture_dir.is_empty(): DirAccess.make_dir_recursive_absolute(capture_dir)
	if collection_enabled and not test_mode:
		if ResourceLoader.exists("res://assets/collection/models/S.glb"):
			collection=load("res://collection/service.gd").new();add_child(collection);collection.setup(self)
		else:message("装置档案未能加载，请重新打开完整的 MagicDesk App。",12)
	if native_mode and native_port>0:
		native_bridge=Node.new();native_bridge.set_script(load("res://native_bridge.gd"));add_child(native_bridge);native_bridge.setup(self,native_port)

func _collect_meshes(node: Node) -> void:
	if node is MeshInstance3D:
		meshes.append(node)
		if not native_mode:
			var hull: ConvexPolygonShape3D = node.mesh.create_convex_shape()
			node.set_meta("outline",hull.points)
			var surface_body := StaticBody3D.new()
			surface_body.collision_layer=2
			surface_body.collision_mask=0
			node.add_child(surface_body)
			var surface_shape := CollisionShape3D.new()
			surface_shape.shape=node.mesh.create_trimesh_shape()
			surface_body.add_child(surface_shape)
		for i in range(node.mesh.get_surface_count()):
			var m = node.get_active_material(i)
			if m is StandardMaterial3D and (m.resource_name.contains("Solar_Core") or m.resource_name.contains("Amber_Light")):
				m = m.duplicate()
				node.set_surface_override_material(i, m)
				core_materials.append({"mat": m, "energy": m.emission_energy_multiplier, "color": m.emission})
			elif m is StandardMaterial3D:
				var key: String = m.resource_name
				if not surface_materials.has(key):
					var shader_material := ShaderMaterial.new()
					shader_material.shader = load("res://surface.gdshader")
					shader_material.set_shader_parameter("base_color",m.albedo_color)
					shader_material.set_shader_parameter("metalness",m.metallic)
					shader_material.set_shader_parameter("surface_roughness",m.roughness)
					shader_material.set_shader_parameter("use_color_map",m.albedo_texture != null)
					shader_material.set_shader_parameter("use_rough_map",m.roughness_texture != null)
					shader_material.set_shader_parameter("use_normal_map",m.normal_texture != null)
					if m.albedo_texture: shader_material.set_shader_parameter("color_map",m.albedo_texture)
					if m.roughness_texture: shader_material.set_shader_parameter("rough_map",m.roughness_texture)
					if m.normal_texture: shader_material.set_shader_parameter("normal_map",m.normal_texture)
					shader_material.set_shader_parameter("normal_depth",.12)
					shader_material.set_shader_parameter("coat",.26 if key=="Ivory_Enamel" else .07 if key=="Cherry_Enamel" else 0.0)
					shader_material.set_shader_parameter("brushed",0.0)
					surface_materials[key] = shader_material
				node.set_surface_override_material(i,surface_materials[key])
	for child in node.get_children(): _collect_meshes(child)

func _make_studio() -> void:
	camera = Camera3D.new()
	add_child(camera)
	camera.projection = Camera3D.PROJECTION_PERSPECTIVE
	camera.fov = rad_to_deg(2.0*atan(canonical_size.y/(2.0*reference_focal_pixels)))
	camera.keep_aspect = Camera3D.KEEP_HEIGHT
	camera.position = Vector3(0.65, 3.95, 7.65)
	camera.look_at(Vector3(0, 1.92, 0))
	camera.near = 0.05
	camera.far = 60.0
	camera.current = true
	var environment_node := WorldEnvironment.new()
	env = Environment.new()
	env.background_mode = Environment.BG_CLEAR_COLOR
	env.ambient_light_source = Environment.AMBIENT_SOURCE_SKY
	env.ambient_light_energy = 0.60
	env.reflected_light_source = Environment.REFLECTION_SOURCE_SKY
	var sky := Sky.new()
	var panorama := PanoramaSkyMaterial.new()
	panorama.panorama = load("res://assets/studio_small_09_4k.exr")
	panorama.energy_multiplier = 0.30
	sky.sky_material = panorama
	sky.radiance_size = Sky.RADIANCE_SIZE_1024
	env.sky = sky
	env.sky_rotation = Vector3(0,0.65,0)
	env.tonemap_mode = Environment.TONE_MAPPER_AGX
	env.tonemap_exposure = 1.0
	env.ssao_enabled = true
	env.ssao_radius = 0.12
	env.ssao_intensity = 1.4
	env.ssil_enabled = true
	env.ssil_radius = 1.0
	# Transparent desktop rendering uses the HDR reflection environment; SSR requires opaque viewports.
	env.ssr_enabled = false
	env.glow_enabled = false
	env.glow_intensity = 0.65
	env.glow_bloom = 0.0
	env.glow_hdr_threshold = 4.0
	environment_node.environment = env
	add_child(environment_node)
	for d in [[Vector3(-3.2,4.8,4), 24.0, Color(1,.94,.85),Vector2(2.6,4.0)], [Vector3(3.5,4,-2),32.0,Color(.85,.90,1),Vector2(1.2,3.5)], [Vector3(0,2.5,6),7.0,Color(1,.97,.90),Vector2(4.0,2.0)]]:
		var light := AreaLight3D.new()
		add_child(light)
		light.position = d[0]
		light.look_at(Vector3(0,1.8,0))
		light.light_energy = d[1]
		light.light_color = d[2]
		light.shadow_enabled = true
		light.area_size = d[3]
		light.area_range = 18.0
		light.area_attenuation = 2.0
		light.area_normalize_energy = true
		light.light_size = .65
		light.shadow_normal_bias = .10
	core_light = OmniLight3D.new()
	add_child(core_light)
	core_light.position = Vector3(0,2.19,0)
	core_light.light_color = Color(1,.28,.045)
	core_light.omni_range = 2.0
	core_light.light_energy = 0.4
	core_light.shadow_enabled = true
	core_light.light_size = .12
	energy_material = StandardMaterial3D.new()
	energy_material.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
	energy_material.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA
	energy_material.albedo_color = Color(1,.25,.015,.0)
	energy_material.emission_enabled = true
	energy_material.emission = Color(1,.12,.004)
	energy_material.emission_energy_multiplier = 3.0
	for i in range(3):
		var ring := MeshInstance3D.new()
		var torus := TorusMesh.new()
		torus.inner_radius = 0.985
		torus.outer_radius = 1.0
		torus.rings = 64
		torus.ring_segments = 8
		ring.mesh = torus
		ring.material_override = energy_material.duplicate()
		add_child(ring)
		ring.position = Vector3(0,2.3,0)
		pulse_rings.append(ring)

func _make_ui() -> void:
	var layer := CanvasLayer.new()
	add_child(layer)
	var font := SystemFont.new()
	font.font_names = PackedStringArray(["PingFang SC", "Heiti SC", "Microsoft YaHei UI", "Microsoft YaHei", "Segoe UI"])
	var theme := Theme.new()
	var ui_scale:float=DisplayServer.screen_get_scale() if mac_desktop else 1.0
	theme.default_font = font
	theme.default_font_size = int(14*ui_scale)
	var root := Control.new()
	root.theme = theme
	root.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	root.mouse_filter = Control.MOUSE_FILTER_IGNORE
	layer.add_child(root)
	tooltip = PanelContainer.new()
	tooltip.mouse_filter = Control.MOUSE_FILTER_IGNORE
	var box := StyleBoxFlat.new()
	box.bg_color = Color(.065,.060,.050,.95)
	box.border_color = Color(.45,.36,.22,.9)
	box.set_border_width_all(1)
	box.set_corner_radius_all(9)
	box.content_margin_left = 16
	box.content_margin_right = 16
	box.content_margin_top = 10
	box.content_margin_bottom = 10
	tooltip.add_theme_stylebox_override("panel",box)
	root.add_child(tooltip)
	var rows := VBoxContainer.new()
	rows.mouse_filter = Control.MOUSE_FILTER_IGNORE
	tooltip.add_child(rows)
	tooltip_title = Label.new()
	tooltip_title.add_theme_color_override("font_color",Color(.95,.87,.70))
	tooltip_text = Label.new()
	tooltip_text.add_theme_font_size_override("font_size",int(12*ui_scale))
	tooltip_text.add_theme_color_override("font_color",Color(.70,.66,.57))
	rows.add_child(tooltip_title)
	rows.add_child(tooltip_text)
	tooltip.hide()
	toast = Label.new()
	toast.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	toast.add_theme_font_size_override("font_size",int(13*ui_scale))
	toast.add_theme_color_override("font_color",Color(.95,.87,.73))
	toast.add_theme_color_override("font_shadow_color",Color(0,0,0,.95))
	toast.add_theme_constant_override("shadow_offset_x",1)
	toast.add_theme_constant_override("shadow_offset_y",1)
	toast.mouse_filter = Control.MOUSE_FILTER_IGNORE
	root.add_child(toast)
	menu = PopupMenu.new()
	menu.theme = theme
	menu.add_item("HELIOS · 孵日器",0)
	menu.set_item_disabled(0,true)
	menu.add_separator()
	if mac_desktop:
		menu.add_item("装置档案 · 切换模型（Tab）",25)
		menu.add_separator()
	for i in range(TITLES.size()): menu.add_item(str(i+1)+"   "+TITLES[i],10+i)
	menu.add_separator()
	menu.add_check_item("静音",21)
	menu.add_check_item("始终置顶",22)
	menu.add_item("重置视角与位置",23)
	menu.add_separator()
	menu.add_item("退出",99)
	menu.id_pressed.connect(_menu_action)
	root.add_child(menu)
	get_window().close_requested.connect(_quit)

func _make_audio() -> void:
	for audio_name in ["assemble","click","explode","hum","ignition","open","overload","pressure_open","seal_close","shutdown","wake"]:
		audio_streams[audio_name]=load("res://assets/"+audio_name+".wav")
	for i in range(6):
		var p := AudioStreamPlayer.new()
		p.volume_db = -19
		add_child(p)
		sound_players.append(p)
	hum = AudioStreamPlayer.new()
	hum.stream = load("res://assets/hum.wav").duplicate()
	if hum.stream is AudioStreamWAV:
		hum.stream.loop_mode = AudioStreamWAV.LOOP_FORWARD
		hum.stream.loop_begin = 0
		hum.stream.loop_end = 44100
	hum.volume_db = -40
	add_child(hum)
	hum.play()

func sound(name_string: String, pitch := 1.0) -> void:
	if muted or test_mode: return
	var chosen: AudioStreamPlayer = sound_players[0]
	for p in sound_players:
		if not p.playing: chosen = p; break
	chosen.stream = audio_streams.get(name_string)
	chosen.pitch_scale = pitch
	chosen.play()

func message(text: String, seconds := 3.5) -> void:
	toast.text = text
	toast_timer = seconds

func change_pose(open_value: float, exploded_value: float, duration: float) -> void:
	activation_time=-1.0
	activation_display_time=-1.0
	activation_energy=0.0
	open_target = open_value
	explode_target = exploded_value
	transition = {"open_from":openness,"open_to":open_value,"explode_from":explosion,"explode_to":exploded_value,"time":0.0,"duration":duration}
	_fit_window(true)

func start_bloom(emit_pressure:=true)->void:
	power_target=1.0
	if explosion>.01:
		change_pose(1.0,0.0,2.8)
		effects.trigger("assemble")
		sound("assemble")
	else:
		activation_start=openness
		activation_time=0.0
		activation_display_time=0.0
		activation_energy=0.0
		open_target=1.0
		explode_target=0.0
		transition.clear()
		effects.trigger("open" if emit_pressure else "core_open")
		sound("pressure_open" if emit_pressure else "open")
	_fit_window(true)

func activate(index: int) -> void:
	if index<0 or index>=7:return
	if shutdown_time>=0:return
	if collection and collection.dispatch(index):return
	print("HELIOS_ACTION index=",index," openness=",openness," explosion=",explosion)
	buttons[index].press = 1.0
	sound("click",1.0 + index * .045)
	match index:
		0:
			power_target = 0.0 if power_target > .5 else 1.0
			sound("ignition" if power_target>.5 else "seal_close")
			if power_target < .5:
				overload = 0.0
				change_pose(0.0,0.0,2.2)
			effects.trigger("ignition" if power_target>.5 else "close")
			message("孵日器已唤醒" if power_target > .5 else "外壳收拢 · 核心休眠")
		1:
			if open_target>.5 and explode_target<.5:
				change_pose(0.0,0.0,2.6)
				effects.trigger("close")
				sound("seal_close")
			else:start_bloom()
			message("解除锁定 · 六瓣展开" if open_target > .5 else "六瓣闭合 · 机械锁定")
		2:
			power_target = 1.0
			if openness<.8:
				start_bloom(false)
				if effects.core:effects.core.trigger("overload")
			else:effects.trigger("overload")
			overload = 7.0
			sound("overload")
			message("过载 · 核心升速",5.0)
		3:
			power_target = 1.0
			overload = 0.0
			change_pose(0.0,1.0,2.4)
			effects.trigger("explode")
			sound("explode")
			message(str(parts.size())+" 组真实组件 · 分层悬停",4.0)
		4:
			change_pose(0.0,0.0,2.7)
			effects.trigger("assemble")
			overload = 0.0
			sound("assemble")
			message("轴心归位 → 机构锁定 → 外壳合拢",3.0)
		5:
			rotation_enabled = not rotation_enabled
			message("展示旋转已开启" if rotation_enabled else "展示旋转已暂停")
		6:
			begin_shutdown()
	# Mechanical buttons do not change persisted mute/topmost preferences.
	# Avoid a synchronous filesystem write on every opening action.

func begin_shutdown() -> void:
	if collection and collection.request_shutdown():return
	_start_final_shutdown()

func _start_final_shutdown() -> void:
	if shutdown_time>=0:return
	print("HELIOS_SHUTDOWN_REQUEST openness=",openness," explosion=",explosion)
	shutdown_time=0.0
	rotation_enabled=false
	overload=0.0
	change_pose(0.0,0.0,2.3)
	sound("shutdown")
	effects.trigger("shutdown")
	message("压力释放 · 机构收拢",2.4)

func _process(delta: float) -> void:
	var wall_delta:=maxf(delta,0.0)
	delta = minf(delta,0.05)
	var fx_delta:=delta
	elapsed += delta
	if shutdown_time>=0:
		shutdown_time+=delta
		if shutdown_time>.45:power_target=0.0
		display_fade=1.0-smooth01((shutdown_time-2.7)/.55)
		if not native_mode:presentation.modulate.a=display_fade
		if shutdown_time>3.4:
			_save_settings();get_tree().quit();return
	power = move_toward(power,power_target,delta*.7)
	if activation_time>=0:
		activation_display_time+=delta
		activation_time=activation_display_time
		var t:=activation_time
		var value:=opening_fraction(t)
		openness=lerpf(activation_start,1.0,value)
		activation_energy=smoothstep(.30,.65,value)*(1.0-smoothstep(3.30,4.70,t))
		if t>5.5:activation_time=-1.0;activation_display_time=-1.0;activation_energy=0.0;_fit_window(false)
	if not transition.is_empty():
		transition.time += delta
		var t: float = smooth01(transition.time / transition.duration)
		openness = lerpf(transition.open_from,transition.open_to,t)
		explosion = lerpf(transition.explode_from,transition.explode_to,t)
		if transition.time >= transition.duration:
			transition.clear()
			_fit_window(false)
	overload = maxf(0.0,overload-delta)
	var boost := sin(clampf(overload/7.0,0,1)*PI)
	if explosion < .02:
		phase += fx_delta * power * (.50+boost*6.0+activation_energy*3.0)
	var pressure_active:=false
	if effects!=null and effects.pressure!=null:
		pressure_active=effects.pressure.is_burst_active() if effects.pressure.has_method("is_burst_active") else effects.pressure.active_volume_count>0
	if rotation_enabled and drag_kind != 2 and activation_time<0.0 and not pressure_active and (collection==null or (collection.selector_amount<.01 and collection.state=="idle")):angle+=delta*.17
	turntable.rotation.y = angle
	if collection==null or collection.active_id=="B":
		_apply_mechanism()
		effects.tick(fx_delta,wall_delta)
	if collection:collection.tick(delta)
	for i in range(buttons.size()):
		var b: Dictionary = buttons[i]
		b.press = move_toward(b.press,0.0,delta*3.4)
		b.cap.transform = b.home
		b.cap.position.y -= .018*maxf(b.press,1.0 if pressed == i else 0.0)
		var lamp_states := [power,openness,1.0 if overload>0 else 0.0,explosion,1.0 if explosion<.01 and power>.5 else 0.0,1.0 if rotation_enabled else 0.0,1.0 if shutdown_time>=0 else .20]
		b.indicator.emission_energy_multiplier = .12+lamp_states[i]*.7+b.press*2.4+(.8 if hover==i else 0.0)
	hum.volume_db = -80.0 if muted else lerpf(-65.0,-38.0,power)+boost*4.0
	# Camera transform and lens stay fixed during every action, including bloom/explode.
	toast_timer = maxf(0.0,toast_timer-delta)
	toast.visible = toast_timer>0.0
	toast.modulate.a = minf(1.0,toast_timer*2.0)
	var screen := get_viewport().get_visible_rect().size
	var toast_anchor:=camera.unproject_position(Vector3(0,.83,.85))
	toast.position = toast_anchor-Vector2(200,25)
	toast.size.x = 400
	_update_hover()
	_update_hit_region()
	sample_clock += delta
	if sample_clock > .15:
		sample_clock = 0.0
		_live_commands()
	if demo_mode: _demo()

func _apply_mechanism() -> void:
	for c in controls:
		var v := openness
		# Six shells share one velocity curve and settle at the same moment.
		var f := clampf(v*100,0,100)
		var lo := int(f)
		c.node.transform = c.poses[lo].interpolate_with(c.poses[mini(100,lo+1)],f-lo)
	gyros.outer.rotation = Vector3(0,.2+phase*.65,0)
	gyros.middle.rotation = Vector3(.6+sin(phase*.55)*.9,0,0)
	gyros.inner.rotation = Vector3(0,.7+phase,0)
	gyros.core.rotation = Vector3(phase*.8,0,0)
	var choreography:Dictionary=metadata.get("explosion_choreography",{})
	var gyro_alignment:Dictionary=metadata.get("gyro_align",{})
	if not gyro_alignment.is_empty():
		var aligned:=smooth01(explosion/maxf(.001,float(choreography.get("align_end",.18))))
		for key in gyro_alignment:
			if gyros.has(key):gyros[key].quaternion=gyros[key].quaternion.slerp(q4(gyro_alignment[key]),aligned)
	for p in parts:
		var amount := smooth01((explosion-p.stage)/.70)
		var n: Node3D = p.node
		var offset:Vector3=p.offset*amount
		var path:Array=p.explode_path
		if not path.is_empty():
			offset=path[0].offset
			for i in range(path.size()-1):
				var a:Dictionary=path[i];var b:Dictionary=path[i+1]
				if explosion>=float(b.at):offset=b.offset;continue
				if explosion>=float(a.at):offset=(a.offset as Vector3).lerp(b.offset,smooth01((explosion-float(a.at))/maxf(.0001,float(b.at)-float(a.at))))
				break
		var local_offset: Vector3 = n.get_parent().global_basis.inverse()*turntable.global_basis*offset
		n.transform = p.home
		n.position += local_offset
		n.quaternion = p.home.basis.get_rotation_quaternion()*Quaternion(Vector3.UP,p.spin*amount)

func hit_button(screen_pos: Vector2) -> int:
	if collection and collection.active_id!="B":
		var control:int=collection.hit_control(screen_pos)
		if control>=0:return control
	var origin:=camera.project_ray_origin(screen_pos)
	var direction:=camera.project_ray_normal(screen_pos)
	var nearest:=INF
	var selected:=-1
	for i in range(buttons.size()):
		if collection and collection.active_id!="B" and i>0 and i<6:continue
		var cap:Node3D=buttons[i].cap
		var inverse:=cap.global_transform.affine_inverse()
		var local_origin:=inverse*origin
		var local_direction:=inverse.basis*direction
		# Test the actual front of the cylindrical cap, not an enlarged invisible
		# collider. Godot Y is the cap axis after the Blender Z-up conversion.
		if local_direction.y>=-.00001:continue
		var distance:=(.008-local_origin.y)/local_direction.y
		if distance<=0.0 or distance>=nearest:continue
		var point:=local_origin+local_direction*distance
		var radius:=.113 if i==6 else .118
		if Vector2(point.x,point.z).length_squared()>radius*radius:continue
		nearest=distance;selected=i
	return selected

func _update_hover() -> void:
	if collection and collection.update_hover_ui():return
	var pointer := native_cursor if native_mode else Vector2(DisplayServer.mouse_get_position()-get_window().position+crop_rect.position)
	var new_hover := hit_button(pointer)
	if drag_kind != 0 or menu.visible: new_hover = -1
	if new_hover != hover:
		hover = new_hover
		tooltip.visible = hover >= 0
		if hover >= 0:
			tooltip_title.text = "关闭应用" if hover==6 else TITLES[hover]
			tooltip_title.add_theme_color_override("font_color",Color(1.0,.28,.18) if hover==6 else Color(.95,.86,.68))
			tooltip_text.text = HINTS[hover]
			tooltip.reset_size()
	if hover >= 0:
		var anchor:Vector3=collection.action_anchor(hover) if collection and collection.active_id!="B" else buttons[hover].mount.global_position
		var pt := camera.unproject_position(anchor)
		tooltip.position = Vector2(clampf(pt.x-tooltip.size.x*.5,crop_rect.position.x+8,crop_rect.end.x-tooltip.size.x-8),pt.y-tooltip.size.y-25)
	if not native_mode:Input.set_default_cursor_shape(Input.CURSOR_POINTING_HAND if hover >= 0 else Input.CURSOR_ARROW)

func _input(event: InputEvent) -> void:
	if native_mode:return
	if collection and collection.consume_input(event):
		get_viewport().set_input_as_handled();return
	if event is InputEventKey and event.pressed and not event.echo:
		if event.keycode >= KEY_1 and event.keycode <= KEY_7: activate(event.keycode-KEY_1)
		if event.keycode == KEY_ESCAPE: _show_menu()
		if event.keycode == KEY_SPACE:
			if collection:collection.toggle_rotation()
			else:activate(5)
	if event is InputEventMouseButton:
		if event.button_index == MOUSE_BUTTON_RIGHT and event.pressed: _show_menu(); return
		if event.button_index == MOUSE_BUTTON_LEFT:
			if event.pressed:
				pressed = hit_button(event.position)
				drag_start = Vector2(DisplayServer.mouse_get_position())
				window_start = get_window().position
				drag_distance = 0
				if pressed < 0:
					var base_top := camera.unproject_position(Vector3(0,.60,1.0))
					drag_kind = 1 if event.position.y > base_top.y-20 else 2
			else:
				if pressed >= 0 and hit_button(event.position) == pressed: activate(pressed)
				pressed = -1
				drag_kind = 0
	if event is InputEventMouseMotion:
		if drag_kind == 1:
			var diff := Vector2(DisplayServer.mouse_get_position())-drag_start
			get_window().position = window_start+Vector2i(diff)
			desktop_anchor=get_window().position-crop_rect.position
		elif drag_kind == 2: angle += event.relative.x*.008

func _show_menu() -> void:
	menu.set_item_checked(menu.get_item_index(21),muted)
	menu.set_item_checked(menu.get_item_index(22),get_window().always_on_top)
	menu.position = DisplayServer.mouse_get_position()
	menu.popup()

func _menu_action(id: int) -> void:
	if id==24 and collection:collection.toggle_rotation()
	if id==25 and collection:collection.toggle_selector()
	if id >= 10 and id <= 16: activate(id-10)
	if id == 21: muted = not muted; _save_settings()
	if id == 22: get_window().always_on_top = not get_window().always_on_top; _save_settings()
	if id == 23:
		zoom = 1.0
		angle = 0.0
		var usable := DisplayServer.screen_get_usable_rect()
		desktop_anchor=usable.position+usable.size/2-canonical_size/2
		get_window().position=desktop_anchor+crop_rect.position
	if id == 99: _quit()

func _update_hit_region() -> void:
	if native_mode:return
	# Raycast actual 3D surfaces. Empty spaces between petals also pass clicks through.
	var cursor := Vector2(DisplayServer.mouse_get_position()-get_window().position+crop_rect.position)
	var from:=camera.project_ray_origin(cursor)
	var query:=PhysicsRayQueryParameters3D.create(from,from+camera.project_ray_normal(cursor)*50,31)
	var on_model:=not get_world_3d().direct_space_state.intersect_ray(query).is_empty()
	var on_ui:=tooltip.visible and tooltip.get_global_rect().has_point(cursor)
	var should_pass := not on_model and not on_ui and drag_kind==0 and pressed<0 and not menu.visible
	if should_pass != passthrough_active:
		passthrough_active=should_pass
		DisplayServer.window_set_flag(DisplayServer.WINDOW_FLAG_MOUSE_PASSTHROUGH,should_pass)

func _model_bounds() -> Rect2:
	var bound := Rect2()
	var first := true
	for m in meshes:
		var points: PackedVector3Array = m.get_meta("outline")
		var view_points: PackedVector3Array = (camera.global_transform.affine_inverse()*m.global_transform)*points
		for p in view_points:
			var pt:=Vector2(canonical_size)*.5+Vector2(p.x,-p.y)*(reference_focal_pixels/maxf(.01,-p.z))
			if first:bound=Rect2(pt,Vector2.ZERO);first=false
			else:bound=bound.expand(pt)
	return bound

func _fit_window(include_path: bool) -> void:
	if native_mode:return
	if mac_desktop:
		# Keep the entire transparent render canvas resident. Mesh-only cropping
		# clips the orbit/steam and resizing a Cocoa window can move its anchor.
		# The existing surface raycast passes empty desktop space through.
		var canvas_rect := Rect2i(Vector2i.ZERO,canonical_size)
		if crop_rect == canvas_rect and get_window().size == canonical_size:return
		crop_rect = canvas_rect
		presentation.position = Vector2.ZERO
		if get_window().size != canonical_size:get_window().size = canonical_size
		get_window().position = desktop_anchor
		desktop_anchor = get_window().position
		return
	# Crop the fixed-resolution 3D render, preserving the model's exact desktop pixels.
	# Only resize before/after a mechanical action, never on every animation frame.
	var old_open:=openness
	var old_explode:=explosion
	var old_angle:=turntable.rotation.y
	var total:=_model_bounds()
	var count:=5 if include_path else 1
	for step in range(count):
		var t:=float(step)/float(maxi(count-1,1))
		if include_path:
			openness=lerpf(old_open,open_target,t)
			explosion=lerpf(old_explode,explode_target,t)
		for yaw in [0.0,PI/6.0,PI/3.0]:
			turntable.rotation.y=old_angle+yaw
			_apply_mechanism()
			total=total.merge(_model_bounds())
	openness=old_open;explosion=old_explode;turntable.rotation.y=old_angle
	_apply_mechanism()
	total=total.grow(16)
	var next_rect:=Rect2i(Vector2i(floor(total.position.x),floor(total.position.y)),Vector2i(ceil(total.size.x),ceil(total.size.y)))
	if next_rect==crop_rect:return
	crop_rect=next_rect
	presentation.position=-Vector2(crop_rect.position)
	get_window().size=crop_rect.size
	get_window().position=desktop_anchor+crop_rect.position

func _live_commands() -> void:
	if control_path.is_empty() or not FileAccess.file_exists(control_path): return
	var stamp := FileAccess.get_modified_time(control_path)
	if stamp == control_stamp: return
	control_stamp = stamp
	var cmd = JSON.parse_string(FileAccess.get_file_as_string(control_path))
	if not cmd is Dictionary: return
	if cmd.has("action"): activate(int(cmd.action))
	if cmd.has("model") and collection:collection.request_model(str(cmd.model))
	if cmd.has("selector") and collection:collection.selector_target=1.0 if cmd.selector else 0.0
	if cmd.has("capture"): capture(str(cmd.capture))
	if cmd.has("hide_ui"):
		toast_timer=0.0;native_cursor=Vector2(-10000,-10000)
	if cmd.has("rotate"): rotation_enabled=bool(cmd.rotate)
	if cmd.has("angle"): angle=float(cmd.angle)
	if cmd.has("background"):
		get_viewport().transparent_bg=not bool(cmd.background)
		RenderingServer.set_default_clear_color(Color(.025,.028,.032,1) if cmd.background else Color(0,0,0,0))
	if cmd.has("environment"):
		for key in cmd.environment: env.set(key,cmd.environment[key])
	if cmd.has("light_energies"):
		var n:=0
		for light in get_children():
			if light is AreaLight3D:
				light.light_energy=float(cmd.light_energies[n]);n+=1
	if cmd.has("reload_surface"):
		var shader: Shader = load("res://surface.gdshader")
		shader.code=FileAccess.get_file_as_string("res://surface.gdshader")
	if cmd.has("detach"): control_path=""
	if cmd.has("quit"): _quit()

func _save_settings() -> void:
	if test_mode or demo_mode or not control_path.is_empty(): return
	var cf := ConfigFile.new()
	cf.set_value("desktop","muted",muted)
	cf.set_value("desktop","top",get_window().always_on_top)
	cf.save("user://settings.cfg")

func _load_settings() -> void:
	var cf := ConfigFile.new()
	if cf.load("user://settings.cfg") == OK and not test_mode and not demo_mode:
		muted = cf.get_value("desktop","muted",false)
		get_window().always_on_top = cf.get_value("desktop","top",false)

func _quit() -> void:
	begin_shutdown()

func capture(name_string: String) -> void:
	if capture_dir.is_empty(): return
	await get_tree().process_frame
	await get_tree().process_frame
	await RenderingServer.frame_post_draw
	get_tree().root.get_texture().get_image().save_png(capture_dir.path_join(name_string+".png"))
	var info := {"window_position":[get_window().position.x,get_window().position.y],"window_size":[get_window().size.x,get_window().size.y],"camera_fov":camera.fov,"fps":Engine.get_frames_per_second(),"vertices":RenderingServer.get_rendering_info(RenderingServer.RENDERING_INFO_TOTAL_PRIMITIVES_IN_FRAME)}
	if collection:info["collection"]=collection.diagnostics()
	FileAccess.open(capture_dir.path_join(name_string+".json"),FileAccess.WRITE).store_string(JSON.stringify(info,"  "))

func _demo() -> void:
	for entry in [[1.5,-1,"closed"],[3.0,1,""],[5.8,-1,"open"],[7.0,2,""],[9.6,-1,"overload"],[13.8,3,""],[17.0,-1,"exploded"],[19.0,4,""],[22.0,-1,"assembled"]]:
		var key := str(entry[0])
		if elapsed >= entry[0] and not demo_events.has(key):
			demo_events[key] = true
			if entry[1] >= 0: activate(entry[1])
			if not entry[2].is_empty(): capture(entry[2])
	if elapsed > 24: get_tree().quit()

func record_test(name_string: String, passed: bool, detail = "") -> void:
	tests.append({"test":name_string,"passed":passed,"detail":str(detail)})
	print("HELIOS_TEST ",name_string," ",passed," ",detail)

func _run_tests() -> void:
	set_process(false)
	var fixed_home := fixed_base.global_transform
	var camera_home := camera.global_transform
	var camera_fov := camera.fov
	var base_screen := camera.unproject_position(fixed_base.global_position)
	var base_desktop := Vector2(get_window().position-crop_rect.position)+base_screen
	record_test("component_count",parts.size()==int(metadata.part_count),parts.size())
	record_test("pressure_system_loaded",effects.pressure!=null)
	record_test("red_core_system_loaded",effects.core!=null)
	record_test("ceramic_is_dielectric",absf(float(surface_materials.Ivory_Enamel.get_shader_parameter("metalness")))<.00001)
	record_test("ceramic_uses_new_glaze",surface_materials.Ivory_Enamel.get_shader_parameter("rough_map").resource_path.ends_with("ceramic_glaze_roughness.png"))
	for i in range(buttons.size()):
		var pt := camera.unproject_position(buttons[i].mount.global_position+buttons[i].mount.global_basis.y*.055)
		record_test("physical_button_"+str(i+1),hit_button(pt)==i,hit_button(pt))
	var max_error := 0.0
	for open_value in [0.0,.25,.5,.75,1.0]:
		for explode_value in [0.0,.25,.55,.85,1.0]:
			openness = open_value
			explosion = explode_value
			angle = .73
			turntable.rotation.y = angle
			_apply_mechanism()
			for p in parts: record_finite(p.node)
		openness = 0.0
		explosion = 0.0
		_apply_mechanism()
		for p in parts: max_error = maxf(max_error,p.node.position.distance_to(p.home.origin))
	record_test("exact_reassembly",max_error<.00001,max_error)
	var max_petal_spread:=0.0
	for value in [.01,.10,.25,.50,.75,1.0]:
		openness=value;explosion=0.0;_apply_mechanism()
		var angles:Array[float]=[]
		for i in range(6):
			var hinge:=named("PETAL_HINGE_%02d"%i)
			var zero:=Basis(Vector3.UP,-PI/2+i*TAU/6)
			var relative:=zero.inverse()*hinge.basis
			angles.append(atan2(relative.y.x,relative.y.y))
		max_petal_spread=maxf(max_petal_spread,angles.max()-angles.min())
	record_test("six_petals_synchronized",max_petal_spread<.00001,max_petal_spread)
	openness=0.0;explosion=0.0;_apply_mechanism()
	record_test("stationary_pedestal",fixed_base.global_transform.is_equal_approx(fixed_home))
	record_test("no_camera_zoom_or_motion",camera.global_transform.is_equal_approx(camera_home) and camera.fov==camera_fov)
	record_test("pedestal_screen_position_fixed",camera.unproject_position(fixed_base.global_position).is_equal_approx(base_screen))
	open_target=1.0;explode_target=0.0
	_fit_window(true)
	var base_after_crop:=Vector2(get_window().position-crop_rect.position)+camera.unproject_position(fixed_base.global_position)
	record_test("crop_preserves_desktop_model_position",base_desktop.distance_to(base_after_crop)<.1,base_desktop.distance_to(base_after_crop))
	record_test("fixed_pixel_focal_length",absf(reference_focal_pixels-render_view.size.y/(2*tan(deg_to_rad(camera.fov)*.5)))<.1)
	var geometry_bodies:=0
	for m in meshes:
		for child in m.get_children():
			if child is StaticBody3D and child.collision_layer==2:geometry_bodies+=1
	record_test("exact_surface_hit_testing",geometry_bodies==meshes.size(),geometry_bodies)
	# Interrupt an outward transition at its current pose; retargeting must be continuous.
	openness=.45; explosion=.58
	var before := Vector2(openness,explosion)
	change_pose(0,0,2.7)
	record_test("interrupted_assembly_continuity",before==Vector2(transition.open_from,transition.explode_from))
	for i in range(buttons.size()): activate(i)
	record_test("seven_actions_dispatch",buttons.all(func(b): return b.press==1.0))
	record_test("transparent_window",get_window().transparent and get_viewport().transparent_bg)
	var report := {"tests":tests,"parts":parts.size(),"renderer":RenderingServer.get_current_rendering_method(),"all_passed":tests.all(func(t):return t.passed)}
	var path := "user://verification.json" if capture_dir.is_empty() else capture_dir.path_join("verification.json")
	DirAccess.make_dir_recursive_absolute(path.get_base_dir())
	FileAccess.open(path,FileAccess.WRITE).store_string(JSON.stringify(report,"  "))
	print("HELIOS_VERIFICATION ",path," ",report.all_passed)
	get_tree().quit(0 if report.all_passed else 2)

func record_finite(node: Node3D) -> void:
	if not node.global_position.is_finite(): record_test("finite_transform_"+node.name,false)
