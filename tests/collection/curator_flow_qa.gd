extends SceneTree
## Verify visible geometry behavior: reverse transport, release and quiet end.
func _initialize()->void:run.call_deferred()
func run()->void:
	set_meta("collection_skip_intro",true);set_meta("collection_no_save",true)
	var scene:Node=load("res://main.tscn").instantiate();root.add_child(scene)
	for i in range(10):await process_frame
	var host:Node3D=scene.get_node("Render/HeliosDesktop");host.set_process(false);host.muted=true
	host.collection._legacy_set_visible(false)
	var data:Dictionary=JSON.parse_string(FileAccess.get_file_as_string("res://assets/collection/models/G_optical_curator.json"))
	var module:Node3D=load("res://collection/module.gd").new();host.add_child(module);module.setup(host,data,load("res://assets/collection/models/G_optical_curator.glb"))
	var player:RefCounted=module.play.g_instrument;var fx:Node3D=module.effect.g_visuals;var checks:Array=[]
	player.loaded_index=0;player.owners[0]="platter";player.print_amount=.55;player.stage="printing";player.apply();fx.flow_phase=.25;fx.tick(0,0)
	var before:Vector3=fx.spark_mesh.multimesh.get_instance_transform(0).origin
	fx.tick(.1,0);var forward:Vector3=fx.spark_mesh.multimesh.get_instance_transform(0).origin
	checks.append({"check":"build_particle_rises_from_record","passed":forward.y>before.y+.001})
	player.stage="erasing";fx.tick(0,0);var at_reverse:Vector3=fx.spark_mesh.multimesh.get_instance_transform(0).origin
	checks.append({"check":"reverse_does_not_teleport_particle","passed":at_reverse.distance_to(forward)<.000001})
	fx.tick(.1,0);var returning:Vector3=fx.spark_mesh.multimesh.get_instance_transform(0).origin
	checks.append({"check":"recovery_particle_returns_to_record","passed":returning.y<at_reverse.y-.001})
	player.stage="reading";player.print_amount=0;player.tone_lift=0;player.tone_angle=player.scan_angle(.22);player.apply();fx.tick(0,0)
	checks.append({"check":"reading_beam_points_down_to_record","passed":fx.scan_line.visible and fx.scan_line.global_basis.y.y<-.001})
	player.stage="releasing_field";player.beam_gain=1.;fx.tick(0,0)
	var full_length:float=fx.capture_lines[0].global_basis.y.length()
	player.stage="carrying_record";player.beam_gain=.5;fx.tick(0,0)
	checks.append({"check":"carrying_field_keeps_full_span","passed":absf(fx.capture_lines[0].global_basis.y.length()-full_length)<.00001})
	player.stage="releasing_field"
	player.beam_gain=.5;fx.tick(.1,0);var half_length:float=fx.capture_lines[0].global_basis.y.length()
	checks.append({"check":"release_retracts_actual_light_geometry","passed":absf(half_length/full_length-.5)<.0001})
	checks.append({"check":"disc_contacts_fade_before_remaining_field","passed":fx.effect_levels.capture_contacts<fx.effect_levels.capture})
	player.stage="sleep";player.beam_gain=0;player.print_amount=0;fx.tick(.1,0)
	checks.append({"check":"quiet_end_has_no_temporary_geometry_or_lights","passed":not fx.spark_mesh.visible and not fx.scan_line.visible and fx.contacts.all(func(c):return not c.visible) and fx.glints.all(func(g):return not g.visible) and not fx.groove.visible and not fx.field_volume.visible and fx.wires.all(func(w):return not w.visible) and fx.capture_lines.all(func(l):return not l.visible) and fx.feed_lines.all(func(l):return not l.visible) and is_zero_approx(fx.lamp.light_energy) and is_zero_approx(fx.accent.light_energy) and is_zero_approx(fx.capture_lamp.light_energy)})
	var report:={"passed":checks.all(func(c):return c.passed),"checks":checks,"scope":"Actual VFX object transforms and gains, not native input or visual acceptance"}
	FileAccess.open("res://../review/G_optical_curator/operating/flow_qa.json",FileAccess.WRITE).store_string(JSON.stringify(report,"  "));print("CURATOR_FLOW_QA ",JSON.stringify(report));player=null;fx=null;module=null;host=null;scene.queue_free();await process_frame;await process_frame;quit(0 if report.passed else 2)
