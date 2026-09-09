extends RefCounted
## One physical record moves between its slot, the gripper and the reader.
## Motion is a bounded queue; interruption never teleports or duplicates media.
var module:Node3D
var spec:Dictionary
var selected:=0
var loaded_index:=-1
var working_id:=-1
var stage:="sleep"
var parameters:Array[float]=[.5,.8,.5,.35,.5,.70]
var times:Array[float]=[0,0,0,0,0,0]
var records:Array[float]=[0,0,0,0,0,0]
var owners:Array[String]=["slot","slot","slot","slot","slot","slot"]
var content:Array=[]
var media:Array=[]
var cradles:Array=[]
var fingers:Array=[]
var magazine:Node3D
var upper:Node3D
var fore:Node3D
var wrist:Node3D
var platter:Node3D
var tone:Node3D
var bound:=false
var tasks:Array=[]
var task:Dictionary={}
var task_time:=0.0
var magazine_angle:=0.0
var platter_angle:=0.0
var spin_velocity:=0.0
var spin_enabled:=true
var playback_paused:=false
var print_amount:=0.0
var display_amount:=0.0
var read_progress:=0.0
var platform_amount:=1.0
var action_energy:=0.0
var action_count:=0
var action_pulse:=0.0
var alignment:=0.0
var writing:=false
var time:=0.0
var grip:=0.0
var wrist_virtual:=Vector3(.44,1.95,-.30)
var wrist_q:=Quaternion.IDENTITY
var tone_lift:=.17
var tone_angle:=0.0
var record_pose:=Transform3D.IDENTITY
var return_spin:=0.0
var cycle_count:=0
var queue_events:Array=[]
const PARK:=Vector3(.44,1.95,-.30)
const PLACE:=Vector3(0,.898,.72)
const TAKE:=Vector3(0,1.18,.08)
const LIFT:=Vector3(0,1.73,.08)
const LEVEL:=Vector3(0,1.76,.24)
const ABOVE:=Vector3(0,1.65,.72)

func setup(owner:Node3D)->void:
	module=owner;spec=module.data.record_player;module.play.values.fold=parameters[0];module.play.values.spin=1.0
func bind()->void:
	if bound:return
	magazine=module.named(spec.magazine);upper=module.named(spec.upper_arm);fore=module.named(spec.forearm);wrist=module.named(spec.wrist);platter=module.named(spec.platter);tone=module.named(spec.tonearm)
	for i in range(6):media.append(module.named(spec.records[i]));cradles.append(module.named(spec.cradles[i]))
	for f in spec.fingers:fingers.append({"a":module.named(f.proximal),"b":module.named(f.distal),"pad":module.named(f.pad),"angle":float(f.angle)})
	for c in module.data.g_archive.contents:
		var rig:Array=[]
		for r in c.rig:rig.append({"node":module.named(r.name),"home":module.pose(r.home),"data":r,"kind":str(r.kind)})
		content.append({"node":module.named(c.root),"rig":rig,"title":str(c.title),"parameter":str(c.parameter),"action":str(c.action)})
	bound=true
func live()->bool:return module.open_target>.5 and not module.stowing and module.explode_target<.001 and module.power>.01
func pause_spin()->void:spin_enabled=false;module.play.values.spin=0.0
func toggle_spin()->void:spin_enabled=not spin_enabled;module.play.values.spin=1.0 if spin_enabled else 0.0
func pulse_action()->void:action_pulse=1.25;action_count+=1;playback_paused=false;pause_spin()
func changed(key:String,_before:Variant,value:Variant,event:String)->void:
	if key=="leaf":
		var next:int=clampi(roundi(float(value)),0,5)
		if next!=selected or loaded_index<0:spin_enabled=true;module.play.values.spin=1.0;playback_paused=false
		selected=next;module.play.values.fold=parameters[selected]
	elif key=="fold":parameters[selected]=clampf(float(value),0,1);pause_spin()
	elif key=="imprint" and event=="begin":action_count+=1;pause_spin();playback_paused=false
	elif key=="spin":spin_enabled=float(value)>.5
func slot(i:int)->Transform3D:
	var origin:Vector3=module.v3(spec.magazine_origin);var home:Transform3D=module.pose(spec.slots[i]);var rot:=Basis(Vector3.UP,magazine_angle)
	return Transform3D(rot*home.basis,origin+rot*(home.origin-origin))
func task_add(name:String,kind:String,duration:float,values:Dictionary={},event:String="")->void:
	tasks.append({"name":name,"kind":kind,"duration":duration,"values":values,"event":event})
func move(name:String,p:Vector3,q:Quaternion,duration:float,event:String="")->void:task_add(name,"move",duration,{"p":p,"q":q},event)
func start_next()->void:
	if tasks.is_empty():task={};return
	task=tasks.pop_front();task_time=0;stage=task.name
	task["start_p"]=wrist_virtual;task["start_q"]=wrist_q;task["start_grip"]=grip;task["start_mag"]=magazine_angle;task["start_lift"]=tone_lift;task["start_tone"]=tone_angle;task["start_print"]=print_amount
	queue_events.append({"time":time,"stage":stage,"record":working_id})
	if queue_events.size()>200:queue_events.pop_front()
func begin_index()->void:
	working_id=selected;var target:=magazine_angle+wrapf(-selected*TAU/6-magazine_angle,-PI,PI)
	task_add("indexing","index",.45+absf(target-magazine_angle)*.12,{"angle":target},"indexed");start_next()
func begin_load()->void:
	var q:=Quaternion(Vector3.RIGHT,PI/3)
	move("approaching_record",TAKE+Basis(q)*Vector3.UP*.14,q,.48)
	move("lowering_gripper",TAKE,q,.28)
	task_add("clamping_record","grip",.20,{"grip":1.0},"grasped")
	move("lifting_record",LIFT,q,.48)
	move("levelling_record",LEVEL,Quaternion.IDENTITY,.40)
	move("carrying_record",ABOVE,Quaternion.IDENTITY,.46)
	move("placing_record",PLACE,Quaternion.IDENTITY,.38,"placed")
	task_add("releasing_record","grip",.18,{"grip":0.0})
	move("clearing_platter",ABOVE,Quaternion.IDENTITY,.38)
	move("parking_gripper",PARK,Quaternion.IDENTITY,.48,"load_clear")
func scan_angle(radius:float)->float:
	var origin:Vector3=module.v3(spec.tone_origin);var d:=Vector2(-origin.x,.72-origin.z);var length:float=spec.tone_length
	return atan2(-d.y,d.x)+acos(clampf((d.length_squared()+length*length-radius*radius)/(2*d.length()*length),-1,1))
func begin_read()->void:
	task_add("positioning_tonearm","tone",.35,{"angle":scan_angle(.217),"lift":.17})
	task_add("lowering_tonearm","tone",.26,{"angle":scan_angle(.217),"lift":0.0})
	task_add("reading","read",1.15,{},"read_done")
	task_add("lifting_tonearm","tone",.25,{"angle":scan_angle(.084),"lift":.17})
	task_add("parking_tonearm","tone",.32,{"angle":0.0,"lift":.17},"ready_to_print")
func begin_return()->void:
	if print_amount>.001:task_add("erasing","print",maxf(.18,print_amount*1.3),{"amount":0.0})
	task_add("braking_record","wait",.5,{},"return_ready")
func prepare_return()->void:
	return_spin=wrapf(platter_angle,-PI,PI);var q:=Quaternion(Vector3.UP,return_spin)
	move("return_approach",ABOVE,q,.45)
	move("return_lower_gripper",PLACE,q,.36)
	task_add("return_clamp","grip",.20,{"grip":1.0},"regrasped")
	move("return_lift",ABOVE,q,.42)
	move("return_unwind",ABOVE,Quaternion.IDENTITY,.42)
	move("return_carry",LEVEL,Quaternion.IDENTITY,.46)
	move("return_tilt",LIFT,Quaternion(Vector3.RIGHT,PI/3),.40)
	move("return_to_slot",TAKE,Quaternion(Vector3.RIGHT,PI/3),.45,"slotted")
	task_add("return_release","grip",.18,{"grip":0.0})
	move("return_clear",TAKE+Basis(Quaternion(Vector3.RIGHT,PI/3))*Vector3.UP*.14,Quaternion(Vector3.RIGHT,PI/3),.28)
	move("return_park",PARK,Quaternion.IDENTITY,.48,"returned")
func abort_held_record()->void:
	tasks.clear();task={}
	var safe:=Vector3(0,maxf(1.76,wrist_virtual.y),wrist_virtual.z)
	move("return_safe_lift",safe,wrist_q,.38)
	move("return_carry_home",LIFT,Quaternion(Vector3.RIGHT,PI/3),.58)
	move("return_to_slot",TAKE,Quaternion(Vector3.RIGHT,PI/3),.45,"slotted")
	task_add("return_release","grip",.18,{"grip":0.0})
	move("return_clear",TAKE+Basis(Quaternion(Vector3.RIGHT,PI/3))*Vector3.UP*.14,Quaternion(Vector3.RIGHT,PI/3),.28)
	move("return_park",PARK,Quaternion.IDENTITY,.48,"returned");start_next()
func event(name:String)->void:
	match name:
		"indexed":
			if not live():task_add("parking_magazine","index",.45,{"angle":magazine_angle+wrapf(-magazine_angle,-PI,PI)},"sleep")
			elif selected!=working_id:begin_index()
			else:begin_load()
		"grasped":owners[working_id]="grip";loaded_index=working_id
		"placed":owners[working_id]="platter";platter_angle=0;spin_velocity=0
		"load_clear":
			if live() and selected==working_id:begin_read()
			else:begin_return()
		"read_done":read_progress=1;records[working_id]=1
		"ready_to_print":
			if live() and selected==working_id:task_add("printing","print",2.0,{"amount":1.0},"printed")
			else:begin_return()
		"printed":stage="playing";cycle_count+=1
		"return_ready":prepare_return()
		"regrasped":owners[working_id]="grip"
		"slotted":owners[working_id]="slot";loaded_index=-1
		"returned":
			read_progress=0;working_id=-1
			if live():stage="sleep"
			else:
				var target:=magazine_angle+wrapf(-magazine_angle,-PI,PI);task_add("parking_magazine","index",.5,{"angle":target},"sleep")
		"sleep":stage="sleep"
func step(dt:float)->void:
	task_time=minf(float(task.duration),task_time+dt);var u:float=task_time/float(task.duration);var s:float=smoothstep(0,1,u);var v:Dictionary=task["values"]
	match str(task.kind):
		"index":magazine_angle=lerpf(float(task.start_mag),float(v.angle),s)
		"move":wrist_virtual=(task.start_p as Vector3).lerp(v.p,s);wrist_q=(task.start_q as Quaternion).slerp(v.q,s).normalized()
		"grip":grip=lerpf(float(task.start_grip),float(v.grip),s)
		"tone":tone_lift=lerpf(float(task.start_lift),float(v.lift),s);tone_angle=lerpf(float(task.start_tone),float(v.angle),s)
		"read":read_progress=u;tone_angle=scan_angle(lerpf(.217,.084,s));tone_lift=0
		"print":print_amount=lerpf(float(task.start_print),float(v.amount),s)
func tick(delta:float)->void:
	time+=delta
	var cancel:bool=not live() or selected!=working_id
	if cancel and working_id>=0 and owners[working_id]=="grip" and not stage.begins_with("return_"):abort_held_record()
	if stage=="printing" and (not live() or selected!=working_id):tasks.clear();task={};begin_return();start_next()
	if task.is_empty():
		if stage in ["playing","paused"]:
			if not live() or selected!=working_id:begin_return();start_next()
			else:stage="paused" if playback_paused else "playing"
		elif stage=="sleep" and live():begin_index()
	var remaining:=minf(delta,.10);var steps:=0
	while not task.is_empty() and remaining>.000001 and steps<8:
		var dt:=minf(remaining,float(task.duration)-task_time);step(dt);remaining-=dt
		if task_time>=float(task.duration)-.000001:
			var end_event:String=task.event;task={};event(end_event)
			if task.is_empty() and not tasks.is_empty():start_next()
		steps+=1
	var turning:bool=spin_enabled and stage in ["reading","printing","playing","paused"] and owners.has("platter") and not playback_paused
	spin_velocity=move_toward(spin_velocity,TAU/60 if turning else 0.0,delta*.25)
	platter_angle+=spin_velocity*delta
	var playing:bool=stage=="playing" and loaded_index==selected and print_amount>.999
	var held:bool=module.play.number("imprint")>.5 or action_pulse>0
	if playing:action_pulse=maxf(0,action_pulse-delta)
	action_energy=move_toward(action_energy,1.0 if playing and held else 0.0,delta*(5 if held else 1.5));writing=playing and held
	if playing:
		var speed:float=.75+action_energy*3
		if selected==5:speed=(parameters[5]-.5)*2*(1+action_energy*4)
		times[selected]+=delta*speed
	display_amount=print_amount;alignment=1.0 if playing else 0.0
func ready_to_fold()->bool:return stage=="sleep" and task.is_empty() and tasks.is_empty() and loaded_index<0 and print_amount<.001 and owners.all(func(o):return o=="slot")
func crest()->float:return action_energy
func bone(node:Node3D,a:Vector3,b:Vector3,x:Vector3=Vector3.RIGHT)->void:
	var y:Vector3=(b-a).normalized();var z:=x.cross(y).normalized();x=y.cross(z).normalized();node.transform=Transform3D(Basis(x,y,z),a)
func apply()->void:
	bind()
	magazine.transform=Transform3D(Basis(Vector3.UP,magazine_angle),module.v3(spec.magazine_origin))
	for i in range(6):
		cradles[i].transform=slot(i)
		if owners[i]=="slot":media[i].transform=slot(i)
		elif owners[i]=="grip":media[i].transform=Transform3D(Basis(wrist_q),wrist_virtual)
		else:media[i].transform=Transform3D(Basis(Vector3.UP,platter_angle),PLACE)
	platter.transform=Transform3D(Basis(Vector3.UP,platter_angle),module.v3(spec.platter_origin))
	var origin:Vector3=module.v3(spec.shoulder);var target:Vector3=wrist_virtual+Basis(wrist_q)*Vector3.UP*.27
	var horizontal:=Vector3(target.x-origin.x,0,target.z-origin.z);var distance:float=horizontal.length();var direction:Vector3=horizontal.normalized();var y:float=target.y-origin.y;var a:float=spec.lengths[0];var b:float=spec.lengths[1]
	var q2:float=-acos(clampf((distance*distance+y*y-a*a-b*b)/(2*a*b),-1,1));var q1:float=atan2(y,distance)-atan2(b*sin(q2),a+b*cos(q2))
	var axis:=Vector3(direction.z,0,-direction.x);var elbow:=origin+direction*(a*cos(q1))+Vector3.UP*(a*sin(q1));bone(upper,origin,elbow,axis);bone(fore,elbow,target,axis)
	wrist.transform=Transform3D(Basis(wrist_q),wrist_virtual+Basis(wrist_q)*Vector3.UP*.15)
	for f in fingers:
		var radial:=Vector3(cos(float(f.angle)),0,-sin(float(f.angle)));var tangent:=Vector3(sin(float(f.angle)),0,cos(float(f.angle)))
		var radius:float=lerpf(.310,.270,grip);var height:float=lerpf(-.170,-.150,grip);var d:float=radius-.04
		var c2:float=-acos(clampf((d*d+height*height-.185*.185-.145*.145)/(2*.185*.145),-1,1));var c1:float=atan2(height,d)-atan2(.145*sin(c2),.185+.145*cos(c2))
		var start:=radial*.04;var middle:=start+radial*(.185*cos(c1))+Vector3.UP*(.185*sin(c1));var end:=radial*radius+Vector3.UP*height
		bone(f.a,start,middle,tangent);bone(f.b,middle,end,tangent);f.pad.position=end
	tone.transform=Transform3D(Basis(Vector3.UP,tone_angle),module.v3(spec.tone_origin)+Vector3.UP*tone_lift)
	animate_content()
func animate_content()->void:
	for i in range(content.size()):
		var item:Dictionary=content[i];item.node.visible=i==loaded_index and owners[i]=="platter" and print_amount>.0001
		item.node.scale=Vector3.ONE
		var p:float=parameters[i];var phase:float=times[i];var energy:float=action_energy if i==loaded_index else 0
		for r in item.rig:
			var t:Transform3D=r.home
			match str(r.kind):
				"hour":t.basis*=Basis(Vector3.BACK,-p*TAU-phase*.11)
				"minute":t.basis*=Basis(Vector3.BACK,-p*TAU*12-phase*1.32)
				"gear":t.basis*=Basis(Vector3.BACK,phase*float(r.data.ratio))
				"pendulum":t.basis*=Basis(Vector3.BACK,sin(phase*5.5)*(.12+energy*float(r.data.get("swing_gain",.24))))
				"wing":t.basis*=Basis(Vector3.UP,float(r.data.side)*((1-p)*1.3+sin(phase*9-float(r.data.get("phase",0)))*(.06+energy*.38)*(1.0 if r.data.get("upper",true) else .72)))
				"ship":t.origin.y+=sin(phase*2)*(.008+energy*.028);t.basis*=Basis(Vector3.BACK,sin(phase*2.4)*(.03+energy*.10))
				"sail":t.basis*=Basis(Vector3.UP,(p-.5)*1.8+sin(phase*.8)*energy*.12)
				"wave":t.origin.y+=sin(phase*2.4+float(r.data.phase))*(.005+energy*.012)
				"petal":t.basis*=Basis(Vector3.BACK,(1-clampf(p+energy*.65-float(r.data.flower)*.08,0,1))*1.1+sin(phase+float(r.data.petal))*.025)
				"orbit_tilt":t.basis*=Basis(Vector3.RIGHT,p-.5)
				"orbit":t.basis*=Basis(Vector3.UP,phase*float(r.data.ratio))
				"traveller_return":
					var u:float=fposmod(phase*.055,1);var h:float=r.data.height;var turns:float=r.data.turns;var top:=Vector3(.22*cos(TAU*turns),.113+h,-.22*sin(TAU*turns))
					if u<.70:
						var v:=smoothstep(0,.70,u);t.origin=Vector3(.22*cos(v*TAU*turns),.113+v*h,-.22*sin(v*TAU*turns))
					elif u<.78:t.origin=top.lerp(Vector3(0,.113+h,0),smoothstep(.70,.78,u))
					elif u<.94:t.origin=Vector3(0,.113+h*(1-smoothstep(.78,.94,u)),0)
					else:t.origin=Vector3(.22*smoothstep(.94,1,u),.113,0)
			if r.node.transform!=t:r.node.transform=t
func diagnostics()->Dictionary:
	return {"stage":stage,"selected":selected,"loaded_index":loaded_index,"working_id":working_id,"owners":owners.duplicate(),"parameters":parameters.duplicate(),"times":times.duplicate(),"print_amount":print_amount,"display_amount":print_amount,"read_progress":read_progress,"action_energy":action_energy,"action_count":action_count,"spin_enabled":spin_enabled,"spin_velocity":spin_velocity,"platter_angle":platter_angle,"magazine_angle":magazine_angle,"playback_paused":playback_paused,"grip":grip,"tone_lift":tone_lift,"tone_angle":tone_angle,"ready_to_fold":ready_to_fold(),"cycle_count":cycle_count,"queue":queue_events.duplicate(true)}
