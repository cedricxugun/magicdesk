extends "res://collection/play_state.gd"
## Physical console intents for the current acoustic/music assembly.
func setup(owner:Node3D)->void:
	module=owner
	for item in module.data.control_profiles:values[item.key]=float(item.default)
func input(key:String,requested:Variant,event:String)->void:
	values[key]=requested
	if event=="cancel":
		if key=="bellows":module.cancel_pressure()
		return
	if key=="music" and event=="change":module.activate(1)
	elif key=="shell" and event=="change":module.set_open(float(requested)>.5)
	elif key=="bellows":
		if event=="begin":module.pressure(true)
		elif event=="release":module.pressure(false)
	elif key=="volume":
		var db:float=linear_to_db(maxf(.001,float(requested)))
		module.assembly.music.music_volume_db=db
		if not module.assembly.music.stopping:module.assembly.music.transport.player.volume_db=db
func tick(_delta:float)->void:
	var a:Node3D=module.assembly
	active=a.sequence.desired_open;gain=a.sequence.shell_open
	values.shell=1. if active else 0.
	values.music=1. if a.music.start_pending and not a.music.pause_pending or a.music.transport.state=="playing" else 0.
func gauge_value()->float:
	return maxf(module.assembly.rig.music_level,module.assembly.rig.acoustics.compression)
func diagnostics()->Dictionary:
	return {"active":active,"values":values.duplicate(),"gain":gain,"music":module.assembly.music.status,"sequence":module.assembly.sequence.snapshot()}
