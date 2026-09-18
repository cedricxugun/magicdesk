extends RefCounted
## Same closed four-bar solution as the independent Blender source.
var module:Node3D
var player:RefCounted:
	get:return module.play.g_instrument
var spec:Dictionary
var rigs:Array=[]
var aperture:=0.0
var clock:=0.0
var error:=0.0
func from_blender(p:Vector3)->Vector3:return Vector3(p.x,p.z,-p.y)
func setup(owner:Node3D,definition:Dictionary)->void:
	module=owner;spec=definition
	for r in spec.linkages:rigs.append({"wing":module.named(r.wing),"crank":module.named(r.crank),"rod":module.named(r.rod),"source":r})
	apply()
func tick(delta:float)->void:
	var showing:bool=player.loaded_index==1 and player.stage in ["playing","paused"] and player.print_amount>.999 and not module.stowing and player.selected==1
	var target:float=player.parameters[1] if showing else 0.0
	if showing and player.writing:target=maxf(target,.65)
	aperture=move_toward(aperture,target,delta*.95)
	if showing and player.stage=="playing":clock+=delta
func apply()->void:
	var a:=Vector3(spec.drive.a[0],spec.drive.a[1],0);var cr:float=spec.drive.crank_length;var length:float=spec.drive.rod_length;var horn:float=spec.drive.horn_radius
	error=0.
	for rig in rigs:
		var r:Dictionary=rig.source;var side:float=r.side
		var phase:float=clock*TAU*1.3-(0.0 if r.upper else .28)
		var energy:float=player.action_energy if player.loaded_index==1 else 0.0
		var theta:float=.20+(1-aperture)*.98+sin(phase)*(.010+energy*.16*smoothstep(.15,.60,aperture))*(1.0 if r.upper else .70)
		var b:=Vector3(horn*cos(theta),-horn*sin(theta),0);var d:=b-a;var distance:=d.length()
		var cosine:float=(distance*distance+cr*cr-length*length)/(2*distance*cr)
		assert(absf(cosine)<1.0,"Butterfly linkage exceeded physical reach")
		var phi:=atan2(d.y,d.x)+acos(cosine);var c:=a+Vector3(cr*cos(phi),cr*sin(phi),0)
		b.x*=side;c.x*=side;var mirrored_a:=Vector3(a.x*side,a.y,0)
		var center:Vector3=module.v3(r.center);var origin:Vector3=center+Vector3(0,0,r.link_height)
		rig.wing.transform=Transform3D(Basis(Vector3.UP,-side*theta),from_blender(center))
		rig.crank.transform=Transform3D(Basis(Vector3.UP,side*phi),from_blender(origin+mirrored_a))
		var axis:=from_blender(b-c).normalized()
		# Godot local Y is the converted Blender longitudinal Z; -Z is cup up.
		rig.rod.transform=Transform3D(Basis(Vector3.UP.cross(axis),axis,Vector3.DOWN),from_blender(origin+c))
		error=maxf(error,maxf(absf((b-c).length()-length),absf((c-mirrored_a).length()-cr)))
func state()->Dictionary:return {"aperture":aperture,"clock":clock,"link_error":error}
