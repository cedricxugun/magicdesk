extends "res://collection/module.gd"
## Adapter for the shared collection host. Never substitutes the old I rig.
var assembly:Node3D
var archive:RefCounted
var charge_pending:=false
var charge_held:=false
var pulse_remaining:=0.
func setup(owner:Node3D,definition:Dictionary,_packed:PackedScene)->void:
	host=owner;data=definition
	assembly=load("res://collection/i_nautilus_assembly.gd").new();add_child(assembly);assembly.setup(data.assembly);asset=assembly
	play=load("res://collection/i_nautilus_play.gd").new();play.setup(self)
	effect=load("res://collection/i_nautilus_effect_bridge.gd").new();add_child(effect);effect.setup(self)
	for mesh in asset.find_children("*","MeshInstance3D",true,false):meshes.append(mesh)
	bounds=_bounds()
	archive=load("res://collection/i_nautilus_archive.gd").new();archive.bind(asset)
	# One broad picking volume, not thousands of detail triangle colliders.
	var body:=StaticBody3D.new();body.collision_layer=4;body.collision_mask=0;asset.add_child(body)
	var shape:=CollisionShape3D.new();var box:=BoxShape3D.new();box.size=bounds.size;shape.shape=box;shape.position=bounds.get_center();body.add_child(shape);bodies.append(body)
func set_open(value:bool)->void:
	stowing=not value;open_target=1. if value else 0.
	if not value:charge_pending=false;charge_held=false;pulse_remaining=0.
	assembly.sequence.set_open(value)
	if value:host.power_target=1.
func transfer_to(parent:Node)->void:
	# Reparenting exits and re-enters the tree; the assembly is still alive.
	assembly.echo.preserve_attachments_on_exit=true
	assembly.music.staff.preserve_attachments_on_exit=true
	reparent(parent,false)
	assembly.echo.preserve_attachments_on_exit=false
	assembly.music.staff.preserve_attachments_on_exit=false
func activate(index:int)->void:
	match index:
		1:
			stowing=false;open_target=1.;host.power_target=1.;charge_pending=false;charge_held=false;pulse_remaining=0.
			if assembly.rig.user_pressed:assembly.rig.set_open(false)
			assembly.sequence.music_request();assembly.music.toggle()
		2:pressure(true);pulse_remaining=.8
		3:set_open(true)
		4:set_open(false)
func pressure(held:bool)->void:
	charge_held=held
	if held:
		stowing=false;open_target=1.;host.power_target=1.;assembly.music.stop();charge_pending=true
	elif not charge_pending:assembly.sequence.set_pressed(false)
func cancel_pressure()->void:
	charge_pending=false;charge_held=false;pulse_remaining=0.
	if assembly.rig.user_pressed:
		assembly.rig.set_open(false);assembly.sequence.set_open(true)
func stow()->void:set_open(false)
func settled()->bool:
	return not assembly.sequence.desired_open and assembly.sequence.shell_open<.00001 and assembly.rig.openness<.00001 and not assembly.music.engaged() and not assembly.music.stopping and assembly.rig.acoustics.ready_to_close() and assembly.rig.suspension.settled()
func tick(delta:float,enabled_power:float)->void:
	clock+=delta;power=enabled_power
	if charge_pending and not assembly.music.engaged() and not assembly.music.stopping:
		charge_pending=false;assembly.sequence.set_pressed(true)
		if not charge_held:assembly.sequence.set_pressed(false)
	if pulse_remaining>0. and not charge_pending:
		pulse_remaining=maxf(0.,pulse_remaining-delta)
		if pulse_remaining==0.:pressure(false)
	assembly.tick(delta);openness=assembly.sequence.shell_open;play.tick(delta)
	_sync_colliders()
func set_scan(value:float)->void:
	scan=value;archive.update(value,bounds)
func apply_pose()->void:pass
func advance_yaw(_delta:float,target:float)->void:
	rotation.y=target+float(data.get("display_yaw",0.))
func diagnostics()->Dictionary:
	return {"id":"I","runtime":"nautilus_r59","openness":openness,"explosion":0.,"base_owned":false,"source_sha256":data.assembly.source_sha256,"assembly":assembly.status,"pick_bodies":bodies.size(),"archive":archive.status(),"exploded_service_view":"pending"}
