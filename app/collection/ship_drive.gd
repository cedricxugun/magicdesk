extends RefCounted
## Bounded sail trim, gimbal motion and exact eccentric-follower contact.
## Relative winch ropes rebuild only when trim changes, not every idle frame.
var module:Node3D
var player:RefCounted:
	get:return module.play.g_instrument
var spec:Dictionary
var homes:Dictionary={}
var pitch:Node3D
var carrier:Node3D
var sails:Array=[]
var waves:Array=[]
var cams:Array=[]
var sheets:Array=[]
var wave_drive_version:=2
var shaft:Node3D
var pinion:Node3D
var rockers:Array=[]
var rollers:Array=[]
var rods:Array=[]
var link_error:=0.0
var springs:Array=[]
var last_spring_phase:=-100.0
var trim_angle:=0.0
var motion_clock:=0.0
var cam_phase:=0.0
var last_rope_trim:=-100.0
var was_loaded:=false
var rope_error:=0.0
var contact_error:=0.0

func setup(owner:Node3D,definition:Dictionary)->void:
	module=owner;spec=definition
	wave_drive_version=int(spec.get("wave_drive_version",2))
	for r in module.data.g_archive.contents[2].rig:homes[r.name]=module.pose(r.home)
	pitch=module.named(spec.rig.pitch);carrier=module.named(spec.rig.roll)
	for name in spec.rig.sails:sails.append(module.named(name))
	for name in spec.rig.waves:waves.append(module.named(name))
	for name in spec.rig.cams:cams.append(module.named(name))
	if wave_drive_version==3:
		shaft=module.named(spec.rig.shaft);pinion=module.named(spec.rig.pinion)
		for name in spec.rig.rockers:rockers.append(module.named(name))
		for name in spec.rig.rollers:rollers.append(module.named(name))
		for name in spec.rig.rods:rods.append(module.named(name))
	for source in spec.sheets:
		var original:MeshInstance3D=module.named(source.node)
		assert(original!=null,"Ship rope must remain separate during mesh batching")
		var draw:=MeshInstance3D.new();draw.name=source.node+"_Driven";original.get_parent().add_child(draw);draw.transform=original.transform
		sheets.append({"source":source,"sail":module.named(source.sail),"draw":draw,"material":original.get_active_material(0),"points":PackedVector3Array()})
		original.visible=false
	for source in spec.get("springs",[]):
		var original:MeshInstance3D=module.named(source.node)
		var draw:=MeshInstance3D.new();draw.name=source.node+"_Driven";original.get_parent().add_child(draw);draw.transform=original.transform
		springs.append({"source":source,"draw":draw,"material":original.get_active_material(0),"points":PackedVector3Array()});original.visible=false
	apply()

func tick(delta:float)->void:
	var loaded:bool=player.loaded_index==2
	if loaded and not was_loaded:motion_clock=0.;cam_phase=0.;last_rope_trim=-100.
	was_loaded=loaded
	var showing:bool=loaded and player.stage in ["playing","paused"] and player.print_amount>.999 and player.selected==2 and not module.stowing
	var target:float=clampf(player.parameters[2],0.,1.)*deg_to_rad(20.) if showing else 0.
	trim_angle=move_toward(trim_angle,target,delta*.45)
	var energy:float=player.action_energy if loaded else 0.
	if loaded and (player.stage=="playing" or player.stage=="settling_ship"):
		motion_clock+=delta
		# Integrate velocity: changing force must not reverse/jump cam phase.
		cam_phase+=delta*((.9+energy*.9) if wave_drive_version==3 else (.55+energy*.70))

func apply()->void:
	var energy:float=player.action_energy if player.loaded_index==2 else 0.
	pitch.transform=homes[pitch.name];pitch.basis*=Basis(Vector3.FORWARD,deg_to_rad(5.)*energy*sin(motion_clock*1.7))
	carrier.transform=homes[carrier.name];carrier.basis*=Basis(Vector3.RIGHT,deg_to_rad(2.)*energy*sin(motion_clock*1.7+.65))
	for i in range(sails.size()):
		sails[i].transform=homes[sails[i].name];sails[i].basis*=Basis(Vector3.UP,trim_angle*(1.0 if i==0 else .70))
	contact_error=0.;link_error=0.
	if wave_drive_version==3:_apply_wave_r3()
	else:_apply_wave_r2()
	if absf(trim_angle-last_rope_trim)>.000001:
		_update_sheets();last_rope_trim=trim_angle

func _apply_wave_r2()->void:
	for i in range(3):
		var phase:float=cam_phase+i*TAU/3.0
		cams[i].transform=homes[cams[i].name];cams[i].basis=Basis(Vector3.FORWARD,-phase)
		var height:=sqrt(pow(.017+.006,2)-pow(.006*cos(phase),2))+.006*sin(phase)
		waves[i].transform=homes[waves[i].name];waves[i].position.y=.104+height+.017
		var center:Vector3=cams[i].to_global(Vector3(.006,0,0));var follower:Vector3=waves[i].to_global(Vector3(0,-.017,0))
		contact_error=maxf(contact_error,absf(center.distance_to(follower)-.023))

func _apply_wave_r3()->void:
	shaft.transform=homes[shaft.name];shaft.basis=Basis(Vector3.FORWARD,-cam_phase)
	pinion.transform=homes[pinion.name];pinion.basis=Basis(Vector3.FORWARD,-(-PI/4.+PI+PI/18.-2.*cam_phase))
	const AXLE:=Vector2(-.035,.125)
	const PIVOT:=Vector2(.010,.150)
	for i in range(3):
		var phase:float=cam_phase+i*TAU/3.
		var center:=AXLE+.009*Vector2(cos(phase),sin(phase))
		var d:=center-PIVOT;var distance:=d.length()
		var theta:=atan2(d.y,d.x)-acos(clampf((distance*distance+.040*.040-.030*.030)/(2.*distance*.040),-1.,1.))
		var output:=PIVOT-.068*Vector2(cos(theta),sin(theta))
		var slider:=Vector2(.088,output.y+sqrt(.035*.035-pow(.088-output.x,2)))
		rockers[i].transform=homes[rockers[i].name];rockers[i].basis=Basis(Vector3.FORWARD,-theta)
		rods[i].transform=homes[rods[i].name];rods[i].position=Vector3(output.x,output.y,-(-.10+i*.10+.020))
		rods[i].basis=Basis(Vector3.FORWARD,-atan2(slider.y-output.y,slider.x-output.x))
		waves[i].transform=homes[waves[i].name];waves[i].position.y=slider.y+.015
		rollers[i].transform=homes[rollers[i].name];rollers[i].basis=Basis(Vector3.FORWARD,phase*4.)
		if absf(cam_phase-last_spring_phase)>.000001 and i<springs.size():_update_spring(i,theta)
		var actual_center:Vector3=cams[i].to_global(Vector3(.009,0,0))
		contact_error=maxf(contact_error,absf(actual_center.distance_to(rollers[i].global_position)-.030))
		link_error=maxf(link_error,rods[i].global_position.distance_to(rockers[i].to_global(Vector3(-.068,0,-.010))))
		link_error=maxf(link_error,rods[i].to_global(Vector3(.035,0,0)).distance_to(waves[i].to_global(Vector3(.088,-.015,-.020))))
	last_spring_phase=cam_phase

func _update_spring(channel:int,theta:float)->void:
	var phase:float=channel*TAU/3.
	var d:=Vector2(-.035,.125)+.009*Vector2(cos(phase),sin(phase))-Vector2(.010,.150)
	var rest:=atan2(d.y,d.x)-acos(clampf((d.length_squared()+.040*.040-.030*.030)/(2.*d.length()*.040),-1.,1.))
	var start:=rest+PI-TAU*3.-PI/2.;var end:=theta+PI
	var points:=PackedVector3Array()
	for j in range(17):
		var angle:=start+PI+j*TAU/16.
		points.append(Vector3(.018*cos(start)+.0025*cos(angle),.018*sin(start)+.0025*sin(angle),.003))
	for j in range(73):
		var u:=j/72.;var angle:=lerpf(start,end,u)
		points.append(Vector3(.0105*cos(angle),.0105*sin(angle),-.006*u))
	for j in range(17):
		var angle:=end+PI+j*TAU/16.
		points.append(Vector3(.018*cos(end)+.0025*cos(angle),.018*sin(end)+.0025*sin(angle),-.006))
	var spring:Dictionary=springs[channel];var draw:MeshInstance3D=spring.draw
	var material:Material=draw.get_active_material(0) if draw.mesh else spring.material
	spring.points=points;draw.mesh=_tube(points,.00065);draw.set_surface_override_material(0,material)

func _update_sheets()->void:
	rope_error=0.
	for sheet in sheets:
		var source:Dictionary=sheet.source;var sail:Node3D=sheet.sail;var draw:MeshInstance3D=sheet.draw
		var tip:=Vector3(source.side*(source.length+.020),.028,0)
		var tip_local:Vector3=carrier.to_local(sail.to_global(tip))
		var center:=Vector3(source.winch_x,0,-source.winch_y)
		var d:=tip_local-center;var radius:=.008
		var tangent:=atan2(-d.z,d.x)+acos(radius/Vector2(d.x,d.z).length())
		var points:=PackedVector3Array([draw.to_local(sail.to_global(tip))])
		for j in range(33):
			var u:=j/32.0;var a:=lerpf(tangent,TAU*2.0,u)
			var point:=center+Vector3(radius*cos(a),.180+.009*u+source.winch_lift,-radius*sin(a))
			points.append(draw.to_local(carrier.to_global(point)))
		sheet.points=points
		var material:Material=draw.get_active_material(0) if draw.mesh else sheet.material
		draw.mesh=_tube(points,.0014);draw.set_surface_override_material(0,material)
		rope_error=maxf(rope_error,draw.to_global(points[0]).distance_to(sail.to_global(tip)))
		var end:=center+Vector3(radius,.189+source.winch_lift,0)
		rope_error=maxf(rope_error,draw.to_global(points[33]).distance_to(carrier.to_global(end)))

func _tube(points:PackedVector3Array,radius:float)->ArrayMesh:
	var vertices:=PackedVector3Array();var normals:=PackedVector3Array();var uv:=PackedVector2Array();var indices:=PackedInt32Array()
	const SIDES:=8
	for i in range(points.size()):
		var axis:Vector3=(points[mini(points.size()-1,i+1)]-points[maxi(0,i-1)]).normalized()
		var reference:=Vector3.UP if absf(axis.dot(Vector3.UP))<.9 else Vector3.RIGHT
		var a:=axis.cross(reference).normalized();var b:=axis.cross(a).normalized()
		for j in range(SIDES+1):
			var angle:=j*TAU/SIDES;var normal:=a*cos(angle)+b*sin(angle)
			vertices.append(points[i]+normal*radius);normals.append(normal);uv.append(Vector2(j/float(SIDES),i/float(points.size()-1)))
	for i in range(points.size()-1):
		for j in range(SIDES):
			var a:=i*(SIDES+1)+j;var b:=a+SIDES+1
			indices.append_array(PackedInt32Array([a,b,b+1,a,b+1,a+1]))
	var arrays:Array=[];arrays.resize(Mesh.ARRAY_MAX);arrays[Mesh.ARRAY_VERTEX]=vertices;arrays[Mesh.ARRAY_NORMAL]=normals;arrays[Mesh.ARRAY_TEX_UV]=uv;arrays[Mesh.ARRAY_INDEX]=indices
	var result:=ArrayMesh.new();result.add_surface_from_arrays(Mesh.PRIMITIVE_TRIANGLES,arrays);return result

func neutral()->bool:return absf(trim_angle)<.001 and player.action_energy<.001
func state()->Dictionary:return {"trim_radians":trim_angle,"motion_clock":motion_clock,"cam_phase":cam_phase,"rope_error":rope_error,"cam_contact_error":contact_error,"link_closure_error":link_error,"wave_drive_version":wave_drive_version,"neutral":neutral()}
