extends Node3D
var model:Node3D
var power:=1.0
var openness:=1.0
var explosion:=0.0
var shutdown_time:=-1.0
var activation_time:=0.0
var activation_display_time:=-1.0
var activation_energy:=0.0
func named(s:String)->Node3D:return model.find_child(s,true,false) as Node3D
