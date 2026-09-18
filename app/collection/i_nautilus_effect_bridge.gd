extends Node3D
## Collection lifecycle facade; visuals are the assembly's authored echo/score.
var module:Node3D
var quiet_gain:=0.
var atlas:Texture2D
func setup(owner:Node3D)->void:
	module=owner;atlas=load("res://assets/collection/art/archive_atlas.png")
func request_quiet()->void:quiet_gain=0.
func resume()->void:quiet_gain=1.
func tick(_delta:float)->void:pass
func ready_to_fold()->bool:return module.settled()
