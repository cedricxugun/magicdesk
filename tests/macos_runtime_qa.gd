extends SceneTree
## Run with Godot 4.7.1 --main-pack <exported PCK> --script <this file>.
## Release templates omit --script; test the final .app separately with --self-test
## and real desktop input. This driver tests the exact exported resources.
## This driver is outside app/ and is never included in the shipped PCK.

var host: Node3D
var checks: Array = []
var frame_ms: Array[float] = []
var collecting := false
var output := ""
var baseline_window: Rect2i
var baseline_camera: Transform3D
var baseline_fov: float
var baseline_base: Transform3D

func _initialize() -> void:
	_run.call_deferred()

func _process(delta: float) -> bool:
	if collecting: frame_ms.append(delta * 1000.0)
	return false

func check(label: String, passed: bool, detail: Variant = "") -> void:
	checks.append({"check": label, "passed": passed, "detail": str(detail)})
	print("MAC_QA ", label, " ", passed, " ", detail)

func wait_seconds(seconds: float) -> void:
	await create_timer(seconds).timeout

func capture_state(label: String) -> void:
	await RenderingServer.frame_post_draw
	var img := root.get_texture().get_image()
	img.save_png(output.path_join(label + ".png"))
	var used := img.get_used_rect()
	check(label + "_visible", used.size.x > 100 and used.size.y > 100, used)
	check(label + "_transparent", img.get_pixel(0,0).a < 0.01 and img.get_pixel(img.get_width()-1,0).a < 0.01)
	check(label + "_fixed_window", Rect2i(root.position,root.size) == baseline_window)
	check(label + "_fixed_camera", host.camera.global_transform.is_equal_approx(baseline_camera) and is_equal_approx(host.camera.fov,baseline_fov))
	check(label + "_fixed_base", host.fixed_base.global_transform.is_equal_approx(baseline_base))
	var points: Array = []
	for i in range(host.buttons.size()):
		var point: Vector2 = host.camera.unproject_position(host.buttons[i].cap.to_global(Vector3(0,.008,0)))
		check(label + "_button_" + str(i+1), host.hit_button(point) == i)
		points.append([point.x,point.y])
	var data := {"window_position":[root.position.x,root.position.y],"window_size":[root.size.x,root.size.y],"screen_scale":DisplayServer.screen_get_scale(),"buttons":points,"openness":host.openness,"explosion":host.explosion,"fps":Engine.get_frames_per_second(),"passthrough":host.passthrough_active}
	FileAccess.open(output.path_join(label+".json"),FileAccess.WRITE).store_string(JSON.stringify(data,"  "))

func _run() -> void:
	for arg in OS.get_cmdline_user_args():
		if arg.begins_with("--capture="): output = arg.trim_prefix("--capture=")
	if output.is_empty():
		push_error("Pass -- --capture=<output directory>")
		quit(2)
		return
	DirAccess.make_dir_recursive_absolute(output)
	var scene: Node = load("res://main.tscn").instantiate()
	root.add_child(scene)
	current_scene = scene
	host = scene.get_node("Render/HeliosDesktop")
	await wait_seconds(3.0)
	host.rotation_enabled = false
	host.angle = 0.0
	await process_frame
	baseline_window = Rect2i(root.position,root.size)
	baseline_camera = host.camera.global_transform
	baseline_fov = host.camera.fov
	baseline_base = host.fixed_base.global_transform
	check("macOS_direct_presentation", host.mac_desktop and not host.native_mode)
	check("graceful_system_quit", not auto_accept_quit)
	check("component_count", host.parts.size() == 70)
	check("button_count", host.buttons.size() == 7)
	check("pressure_cache", host.effects.pressure.physics_frames.size() == 61)
	await capture_state("closed")
	collecting = true
	host.activate(1)
	await wait_seconds(1.25)
	check("opening_advances", host.openness > 0.035 and host.openness < 1.0)
	check("steam_advances", host.effects.pressure.physics_time > 0.5, host.effects.pressure.physics_time)
	await capture_state("pressure")
	await wait_seconds(4.0)
	check("bloom_complete", is_equal_approx(host.openness,1.0))
	check("pressure_compute_ready", host.effects.pressure.compute_effect.get_diagnostics().get("ready",false))
	var idle: Node = host.effects.pressure.idle_controller
	check("idle_cache", idle.physics_frames.size() == 18)
	check("idle_compute_ready", idle.compositor.get_diagnostics().get("ready",false))
	await capture_state("open")
	host.activate(2)
	await wait_seconds(3.5)
	check("overload_peak", host.overload > 2.5 and host.overload < 4.0, host.overload)
	check("overload_no_ground_burst", not host.effects.pressure.is_burst_active())
	await capture_state("overload")
	host.activate(4)
	await wait_seconds(3.2)
	check("assemble_during_overload", host.shutdown_time < 0 and host.openness < .001 and host.explosion < .001)
	host.activate(3)
	await wait_seconds(2.8)
	check("explode_complete", host.explosion > .999)
	await capture_state("exploded")
	host.activate(4)
	await wait_seconds(3.2)
	var max_error := 0.0
	for part in host.parts: max_error = maxf(max_error,part.node.position.distance_to(part.home.origin))
	check("exact_reassembly", max_error < .00001,max_error)
	await capture_state("assembled")
	host.activate(1)
	await wait_seconds(1.3)
	host.activate(4)
	await wait_seconds(3.2)
	check("interrupt_bloom_assemble", host.openness < .001 and host.explosion < .001 and host.shutdown_time < 0)
	host.activate(3)
	await wait_seconds(.7)
	host.activate(4)
	await wait_seconds(3.2)
	check("interrupt_explode_assemble", host.openness < .001 and host.explosion < .001 and host.shutdown_time < 0)
	host.activate(0)
	await wait_seconds(2.7)
	check("sleep", host.power < .001 and host.openness < .001)
	host.activate(0)
	await wait_seconds(2.0)
	check("wake", host.power > .999)
	var previous: float = host.angle
	host.activate(5)
	await wait_seconds(.6)
	check("rotation", host.angle > previous)
	host.activate(5)
	previous = host.angle
	await wait_seconds(.3)
	check("pause_rotation", is_equal_approx(host.angle,previous))
	collecting = false
	frame_ms.sort()
	var sum_ms := 0.0
	for ms in frame_ms: sum_ms += ms
	var perf := {"frames":frame_ms.size(),"average_fps":1000.0*frame_ms.size()/sum_ms,"median_ms":frame_ms[frame_ms.size()/2],"p95_ms":frame_ms[int(frame_ms.size()*.95)],"max_ms":frame_ms[-1],"includes_capture_readbacks":true}
	root.close_requested.emit()
	check("system_quit_starts_shutdown", host.shutdown_time >= 0)
	await wait_seconds(1.0)
	check("shutdown_animation_alive", host.shutdown_time >= .9 and host.shutdown_time < 3.4)
	var report := {"all_passed":checks.all(func(item): return item.passed),"checks":checks,"performance":perf,"os":OS.get_name(),"device":RenderingServer.get_video_adapter_name(),"engine":Engine.get_version_info().string,"exported_runtime":not OS.has_feature("editor"),"pressure":host.effects.pressure.compute_effect.get_diagnostics(),"idle":idle.get_diagnostics()}
	FileAccess.open(output.path_join("runtime_report.json"),FileAccess.WRITE).store_string(JSON.stringify(report,"  "))
	print("MAC_QA_RESULT ",report.all_passed," output=",output)
	# main.gd owns the final close. A shell timeout catches regressions in shutdown.
	if not report.all_passed: quit(2)
