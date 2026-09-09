extends RefCounted
## Actual lens materials mounted in the authored console; no Canvas UI.
var service:Node3D
var lamps:Dictionary={}
var levels:Dictionary={}

func setup(owner:Node3D)->void:
	service=owner
	for c in service.custom_controls:
		for key in ["Read","Print","Play","Spin","Stop"]:
			var lens:Node3D=c.node.find_child("ConsoleLamp"+key,true,false)
			if lens==null:continue
			var material:=StandardMaterial3D.new();material.albedo_color=Color(.13,.026,.008);material.metallic=.2;material.roughness=.18;material.clearcoat_enabled=true;material.clearcoat=.55;material.emission_enabled=true
			material.emission=Color(.85,.32,.075) if key!="Stop" else Color(.66,.065,.025)
			for child in lens.get_children():
				if child is MeshInstance3D:child.material_override=material
			lamps[key]=material;levels[key]=0.0

func tick(delta:float)->void:
	var player:RefCounted=service.current.play.g_instrument
	var powered:bool=service.host.power>.10 and not player.ready_to_fold()
	var targets:={"Read":1.0 if player.stage=="reading" else 0.0,"Print":1.0 if player.stage in ["printing","erasing"] else 0.0,"Play":.45+player.action_energy*.55 if player.stage in ["playing","paused"] else 0.0,"Spin":1.0 if powered and player.spin_enabled else 0.0,"Stop":1.0 if powered and not player.spin_enabled else 0.0}
	for key in lamps:
		levels[key]=move_toward(float(levels[key]),float(targets[key]),delta*5.0)
		lamps[key].emission_energy_multiplier=.025+float(levels[key])*1.65
