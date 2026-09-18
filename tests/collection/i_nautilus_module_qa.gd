extends SceneTree
var module:Node3D
var checks:Array=[]
class Host extends Node3D:
	var power_target:=1.
func _initialize()->void:run.call_deferred()
func advance(seconds:float)->void:
	for i in range(ceili(seconds*60.)):
		module.tick(1./60.,1.);await process_frame
func check(label:String,result:bool)->void:
	checks.append({"check":label,"passed":result});assert(result,label)
func run()->void:
	var host:=Host.new();root.add_child(host)
	var data:Dictionary=JSON.parse_string(FileAccess.get_file_as_string("res://assets/collection/models/I_nautilus_r59.json"))
	module=load("res://collection/i_nautilus_module.gd").new();host.add_child(module);module.setup(host,data,null)
	check("current_body_single_pick_volume",module.bodies.size()==1 and module.assembly.body_asset!=null)
	var receiver:=Node3D.new();root.add_child(receiver);module.transfer_to(receiver);await process_frame
	check("host_transfer_keeps_optics",is_instance_valid(module.assembly.echo.light) and is_instance_valid(module.assembly.music.staff.optics) and module.assembly.music.staff.scanner_caps.all(func(c):return is_instance_valid(c)))
	var originals:Array=[]
	for mesh in module.meshes:
		originals.append({"mesh":mesh,"override":mesh.material_override,"surfaces":range(mesh.mesh.get_surface_count()).map(func(i):return mesh.get_surface_override_material(i))})
	for amount in [1.,.7,.2,0.]:module.set_scan(amount)
	for item in originals:
		assert(item.mesh.material_override==item.override)
		for i in range(item.surfaces.size()):assert(item.mesh.get_surface_override_material(i)==item.surfaces[i])
	check("scan_restores_exact_material_references",true)
	module.play.input("music",1.,"change");await advance(6.)
	check("console_starts_current_music",module.assembly.music.transport.state=="playing")
	module.play.input("music",0.,"change");await advance(.2)
	check("console_pause",module.assembly.music.transport.state=="paused")
	module.play.input("music",1.,"change");await advance(.2)
	check("console_resume",module.assembly.music.transport.state=="playing")
	module.play.input("volume",.5,"change");check("volume_applies_to_actual_player",is_equal_approx(module.assembly.music.transport.player.volume_db,linear_to_db(.5)))
	module.stow();await advance(.3);check("not_ready_while_score_visible",not module.settled())
	await advance(7.);check("stowed_audio_stopped",module.settled() and module.assembly.music.transport.state=="stopped")
	module.play.input("bellows",1.,"begin");await advance(.3);module.play.input("bellows",0.,"cancel");await advance(4.)
	check("cancel_hold_does_not_emit",not module.assembly.rig.user_pressed and module.assembly.rig.acoustics.outgoing_count==0)
	module.stow();await advance(7.)
	check("ready_to_replace",module.settled())
	module.activate(2);await advance(5.)
	check("single_echo_action_charges_and_emits",module.assembly.rig.acoustics.outgoing_count>0 and not module.assembly.rig.user_pressed)
	module.stow();await advance(7.)
	var report:={"passed":true,"checks":checks,"module":module.diagnostics(),"scope":"Actual compound module and physical-console intent interface; headless Dummy audio. No OS input or rendered scan acceptance."}
	FileAccess.open("res://../review/I_refinement/nautilus_r1/main_adapter_r59/module_qa.json",FileAccess.WRITE).store_string(JSON.stringify(report,"  "))
	await module.assembly.shutdown();module.queue_free();await process_frame;print("I_NAUTILUS_MODULE_QA true");quit()
