extends RefCounted
## One physical record moves between its slot, the gripper and the reader.
## Motion is a bounded queue; interruption never teleports or duplicates media.
var module:Node3D
var spec:Dictionary
var ship_drive:RefCounted
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
var beam_gain:=0.0
var face:Node3D
var face_home:Transform3D
var carrier:Node3D
var projector:Node3D
var shutters:Array=[]
var eyes:Array=[]
var head_drive:Dictionary={}
var iris_node:Node3D
var cam_node:Node3D
var pinion_node:Node3D
var follower_links:Array=[]
var iris_open:=0.0
var face_pose:=Quaternion.IDENTITY
var arrival_age:=10.0
var face_dt:=1.0/60
var face_material:ShaderMaterial
var butterfly_drive:RefCounted
var observatory_enabled:=false
var observatory_profile:Dictionary={}
var observatory_parameter:=.5
var expression:=0
var expression_previous:=0
var expression_blend:=1.0
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
var wrist_virtual:=Vector3(-.66,2.02,-.22)
var wrist_q:=Quaternion.IDENTITY
var tone_lift:=.17
var tone_angle:=0.0
var record_pose:=Transform3D.IDENTITY
var return_spin:=0.0
var cycle_count:=0
var queue_events:Array=[]
var PARK:=Vector3(-.66,2.02,-.22)
var PLACE:=Vector3(0,.94376,.72)
var TAKE:=Vector3(0,1.46,.74)
var LIFT:=Vector3(0,2.02,.74)
var LEVEL:=Vector3(0,2.11,.74)
var ABOVE:=Vector3(0,2.12,.72)

func setup(owner:Node3D)->void:
	module=owner;spec=module.data.record_player;
	observatory_enabled=str(module.data.g_archive.contents[0].get("source_blend","")).contains("G_observatory_r2")
	if observatory_enabled:observatory_profile=JSON.parse_string(FileAccess.get_file_as_string("res://assets/collection/observatory_interaction.json"))
	observatory_parameter=parameters[0]
	PARK=module.v3(spec.park);PLACE=module.v3(spec.place);TAKE=module.v3(spec.take);LIFT=module.v3(spec.lift);LEVEL=module.v3(spec.level);ABOVE=module.v3(spec.above);wrist_virtual=PARK
	module.play.values.fold=parameters[0];module.play.values.spin=1.0
func bind()->void:
	if bound:return
	magazine=module.named(spec.magazine);upper=module.named(spec.upper_arm);fore=module.named(spec.forearm);wrist=module.named(spec.wrist);platter=module.named(spec.platter);tone=module.named(spec.tonearm)
	for i in range(6):media.append(module.named(spec.records[i]));cradles.append(module.named(spec.cradles[i]))
	for f in spec.fingers:fingers.append({"a":module.named(f.proximal),"b":module.named(f.distal),"pad":module.named(f.pad),"angle":float(f.angle)})
	for c in module.data.g_archive.contents:
		var rig:Array=[]
		for r in c.rig:rig.append({"node":module.named(r.name),"home":module.pose(r.home),"data":r,"kind":str(r.kind)})
		content.append({"node":module.named(c.root),"rig":rig,"title":str(c.title),"parameter":str(c.parameter),"action":str(c.action)})
	if module.data.g_archive.contents[1].has("butterfly"):
		butterfly_drive=load("res://collection/butterfly_drive.gd").new();butterfly_drive.setup(module,module.data.g_archive.contents[1].butterfly)
	if module.data.g_archive.contents[2].has("ship"):
		ship_drive=load("res://collection/ship_drive.gd").new();ship_drive.setup(module,module.data.g_archive.contents[2].ship)
	var ai:Dictionary=module.data.optical_curator
	face=module.named(ai.face);carrier=module.named(ai.carrier);projector=module.named(ai.projector)
	face_home=face.transform
	for leaf in ai.leaves:shutters.append({"node":module.named(leaf.name),"home":module.pose(leaf.home)})
	for name in ai.eyes:eyes.append({"node":module.named(name),"home":module.named(name).transform})
	head_drive=ai.get("head_service",{})
	if not head_drive.is_empty():
		iris_node=module.named(ai.iris);cam_node=module.named(head_drive.cam);pinion_node=module.named(head_drive.pinion)
		for item in head_drive.followers:follower_links.append({"node":module.named(item.link),"blade_pin":module.named(item.blade_pin),"cam_pin":module.named(item.cam_pin)})
	if ai.has("screen"):
		face_material=ShaderMaterial.new();face_material.shader=load("res://collection/curator_face.gdshader");face_material.set_shader_parameter("expressions",load("res://assets/collection/art/G_AI/expressions.png"));module.named(ai.screen).material_override=face_material;module.materials.append(face_material)
		var optical:Dictionary=JSON.parse_string(FileAccess.get_file_as_string("res://assets/collection/lighting_profiles.json")).profiles.G.optical
		face_material.set_shader_parameter("face_specular",optical.specular);face_material.set_shader_parameter("face_coat",optical.coat);face_material.set_shader_parameter("face_roughness",optical.roughness)
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
func take_orientation()->Quaternion:return module.pose(spec.slots[maxi(0,working_id)]).basis.get_rotation_quaternion()
func begin_index()->void:
	working_id=selected;TAKE=module.pose(spec.slots[working_id]).origin;LIFT=Vector3(TAKE.x,2.35,TAKE.z);LEVEL=LIFT
	task_add("indexing","index",.42,{"angle":0.0},"indexed");start_next()
func begin_load()->void:
	var q:=take_orientation()
	move("approaching_record",TAKE+Vector3.UP*.40,q,.48)
	move("lowering_gripper",TAKE,q,.28)
	task_add("locking_optical_field","grip",.32,{"grip":1.0},"grasped")
	move("lifting_record",LIFT,q,.48)
	move("levelling_record",LEVEL,Quaternion.IDENTITY,.40)
	move("carrying_record",ABOVE,Quaternion.IDENTITY,.46)
	move("placing_record",PLACE,Quaternion.IDENTITY,.38,"placed")
	task_add("releasing_field","grip",.24,{"grip":0.0})
	move("clearing_platter",ABOVE,Quaternion.IDENTITY,.38)
	move("parking_gripper",PARK,Quaternion.IDENTITY,.48,"load_clear")
func scan_angle(radius:float)->float:
	var origin:Vector3=module.v3(spec.tone_origin);var d:=Vector2(-origin.x,PLACE.z-origin.z);var length:float=spec.tone_length
	return atan2(-d.y,d.x)+acos(clampf((d.length_squared()+length*length-radius*radius)/(2*d.length()*length),-1,1))
func begin_read()->void:
	task_add("positioning_tonearm","tone",.35,{"angle":scan_angle(.35),"lift":.17})
	task_add("lowering_tonearm","tone",.26,{"angle":scan_angle(.35),"lift":0.0})
	task_add("reading","read",1.15,{},"read_done")
	task_add("lifting_tonearm","tone",.25,{"angle":scan_angle(.105),"lift":.17})
	task_add("parking_tonearm","tone",.32,{"angle":0.0,"lift":.17},"ready_to_print")
func begin_return()->void:
	if ship_drive and loaded_index==2 and print_amount>.999:task_add("settling_ship","wait",1.5)
	if butterfly_drive and loaded_index==1 and print_amount>.999:task_add("folding_butterfly","wait",1.2)
	if print_amount>.001:task_add("erasing","print",maxf(.18,print_amount*(1.9 if butterfly_drive and loaded_index==1 else 2.1 if ship_drive and loaded_index==2 else 1.3)),{"amount":0.0})
	task_add("braking_record","wait",.5,{},"return_ready")
func prepare_return()->void:
	return_spin=wrapf(platter_angle,-PI,PI);var q:=Quaternion(Vector3.UP,return_spin)
	move("return_approach",ABOVE,q,.45)
	move("return_lower_gripper",PLACE,q,.36)
	task_add("return_lock_field","grip",.32,{"grip":1.0},"regrasped")
	move("return_lift",ABOVE,q,.42)
	move("return_unwind",ABOVE,Quaternion.IDENTITY,.42)
	move("return_carry",LEVEL,Quaternion.IDENTITY,.46)
	move("return_tilt",LIFT,take_orientation(),.40)
	move("return_to_slot",TAKE,take_orientation(),.45,"slotted")
	task_add("return_release","grip",.24,{"grip":0.0})
	move("return_clear",TAKE+Vector3.UP*.40,take_orientation(),.28)
	move("return_park",PARK,Quaternion.IDENTITY,.48,"returned")
func abort_held_record()->void:
	tasks.clear();task={}
	var safe:=Vector3(wrist_virtual.x,maxf(LIFT.y,wrist_virtual.y),wrist_virtual.z)
	move("return_safe_lift",safe,wrist_q,.38)
	move("return_carry_home",LIFT,take_orientation(),.58)
	move("return_to_slot",TAKE,take_orientation(),.45,"slotted")
	task_add("return_release","grip",.24,{"grip":0.0})
	move("return_clear",TAKE+Vector3.UP*.40,take_orientation(),.28)
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
			if live() and selected==working_id:task_add("printing","print",3.4 if ship_drive and working_id==2 else 2.7,{"amount":1.0},"printed")
			else:begin_return()
		"printed":stage="playing";cycle_count+=1;arrival_age=0
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
		"read":read_progress=u;tone_angle=scan_angle(lerpf(.35,.105,s));tone_lift=0
		"print":print_amount=lerpf(float(task.start_print),float(v.amount),s)
func tick(delta:float)->void:
	time+=delta;arrival_age+=delta;face_dt=delta
	if observatory_enabled:observatory_parameter=move_toward(observatory_parameter,parameters[0],delta*float(observatory_profile.parameter_rate))
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
	var response:float=5.0 if held else 1.5
	if observatory_enabled and loaded_index==0:response=float(observatory_profile.attack_rate) if playing and held else float(observatory_profile.release_rate)
	if butterfly_drive and loaded_index==1:response=1.25 if playing and held else 1.0/1.4
	if ship_drive and loaded_index==2:response=1.0/1.3 if playing and held else 1.0/1.4
	action_energy=move_toward(action_energy,1.0 if playing and held else 0.0,delta*response);writing=playing and held
	if playing:
		var speed:float=.75+action_energy*3
		if selected==5:speed=(parameters[5]-.5)*2*(1+action_energy*4)
		times[selected]+=delta*speed
	if butterfly_drive:butterfly_drive.tick(delta)
	if ship_drive:ship_drive.tick(delta)
	display_amount=print_amount;alignment=1.0 if playing else 0.0
	beam_gain=grip
	if loaded_index>=0 and owners[loaded_index]=="grip":beam_gain=1.0
func ready_to_fold()->bool:return stage=="sleep" and task.is_empty() and tasks.is_empty() and loaded_index<0 and print_amount<.001 and owners.all(func(o):return o=="slot")
func crest()->float:return action_energy
func bone(node:Node3D,a:Vector3,b:Vector3,x:Vector3=Vector3.RIGHT)->void:
	var y:Vector3=(b-a).normalized();var z:=x.cross(y).normalized();x=y.cross(z).normalized();node.transform=Transform3D(Basis(x,y,z),a)
func apply()->void:
	bind()
	magazine.transform=Transform3D(Basis(Vector3.UP,magazine_angle),module.v3(spec.magazine_origin))
	for i in range(6):
		cradles[i].transform=slot(i)*Transform3D(Basis.from_scale(Vector3.ONE*float(spec.cradle_scale)),Vector3.ZERO)
		if owners[i]=="slot":media[i].transform=slot(i)
		elif owners[i]=="grip":media[i].transform=Transform3D(Basis(wrist_q),wrist_virtual)
		else:media[i].transform=Transform3D(Basis(Vector3.UP,platter_angle),PLACE)
		media[i].basis*=Basis.from_scale(Vector3.ONE*float(spec.record_scale))
	platter.transform=Transform3D(Basis(Vector3.UP,platter_angle),module.v3(spec.platter_origin))
	var origin:Vector3=module.v3(spec.shoulder);var target:Vector3=wrist_virtual+Basis(wrist_q)*Vector3.UP*float(spec.carrier_offset)+Vector3.UP*.35
	var horizontal:=Vector3(target.x-origin.x,0,target.z-origin.z);var distance:float=horizontal.length();var direction:Vector3=horizontal.normalized();var y:float=target.y-origin.y;var a:float=spec.lengths[0];var b:float=spec.lengths[1]
	var q2:float=-acos(clampf((distance*distance+y*y-a*a-b*b)/(2*a*b),-1,1));var q1:float=atan2(y,distance)-atan2(b*sin(q2),a+b*cos(q2))
	var axis:=Vector3(direction.z,0,-direction.x);var elbow:=origin+direction*(a*cos(q1))+Vector3.UP*(a*sin(q1));bone(upper,origin,elbow,axis);bone(fore,elbow,target,axis)
	wrist.transform=Transform3D(Basis.IDENTITY,target)
	projector.transform=Transform3D(Basis(wrist_q),Vector3.DOWN*.35)
	module.named(module.data.optical_curator.wrist_yoke).basis=fore.basis
	module.named(module.data.optical_curator.shoulder_fork).transform=Transform3D(Basis(axis,Vector3.UP,axis.cross(Vector3.UP)),origin)
	animate_character()
	tone.transform=Transform3D(Basis(Vector3.UP,tone_angle),module.v3(spec.tone_origin)+Vector3.UP*tone_lift)
	animate_content()
func animate_character()->void:
	var awake:bool=module.power>.05 and (not module.stowing or not ready_to_fold())
	var idle:bool=stage in ["sleep","playing","paused"] and not owners.has("grip")
	var yaw:=0.0;var pitch:=0.0;var roll:=0.0;var next_expression:=0;var aperture:=.95
	var idle_time:=fposmod(time,15.0)
	if idle:
		if idle_time<3.3:
			var interest:=sin(clampf((idle_time-.6)/2.7,0,1)*PI);yaw=-.20*interest;roll=-.16*interest;pitch=-.035*interest
			next_expression=1 if interest>.3 else 0
		elif idle_time<5.8:
			yaw=sin((idle_time-3.3)/2.5*PI)*.17;pitch=-.06;next_expression=4 if idle_time<4.2 else 0
		elif idle_time<8.5:
			roll=sin((idle_time-5.8)/2.7*PI)*.15;next_expression=7
		elif idle_time<12.5:
			var drowse:=sin((idle_time-8.5)/4.0*PI);pitch=drowse*.19;aperture=1.-drowse*.48;next_expression=5
		else:yaw=sin((idle_time-12.5)/2.5*PI)*-.09;next_expression=2
	else:
		yaw=clampf(wrist_virtual.x*.14,-.16,.16);pitch=-.06;next_expression=3;aperture=.82
		if stage=="printing":pitch=-.1+print_amount*.13
	if arrival_age<1.7:roll=sin(arrival_age/1.7*PI)*.14;next_expression=2 if arrival_age<.6 else 7
	if not awake:pitch=.18;yaw=0;roll=0;next_expression=6;aperture=0
	if module.explosion>.001:
		# Stabilize the servicing axes. Idle head tilts must not move the
		# detached shell sectors and internal cartridges around one another.
		yaw=0;pitch=0;roll=0;next_expression=0;aperture=.58
	var target_q:=Quaternion.from_euler(Vector3(pitch,yaw,roll))
	face_pose=face_pose.slerp(target_q,1.0-exp(-face_dt*6)).normalized();face.basis=Basis(face_pose)
	var pivot:Vector3=module.v3(module.data.optical_curator.get("face_pivot",[0,0,0]))
	face.position=face_home.origin+pivot-face.basis*pivot
	var blink:float=fposmod(time+2.5,7.3)
	var closed:float=smoothstep(0.,.12,blink)*(1.-smoothstep(.18,.38,blink)) if blink<.38 and idle else 0.
	aperture*=1.-closed
	iris_open=move_toward(iris_open,aperture,face_dt*(8.3 if aperture<iris_open else 5.0))
	for item in shutters:item.node.transform=item.home;item.node.rotate_object_local(Vector3.BACK,iris_open*.94)
	if not head_drive.is_empty():
		cam_node.transform=module.pose(head_drive.cam_home);cam_node.rotate_object_local(Vector3.BACK,iris_open*.12)
		pinion_node.transform=module.pose(head_drive.pinion_home);pinion_node.rotate_object_local(Vector3.BACK,-iris_open*.12*8.)
		for item in follower_links:
			var a:Vector3=iris_node.to_local(item.blade_pin.global_position);var b:Vector3=iris_node.to_local(item.cam_pin.global_position);var d:=b-a
			item.node.transform=Transform3D(Basis(Quaternion(Vector3.UP,d.normalized()))*Basis.from_scale(Vector3(1,maxf(.00001,d.length()),1)),a)
	if expression!=next_expression:expression_previous=expression;expression=next_expression;expression_blend=0
	expression_blend=move_toward(expression_blend,1.,face_dt*8.)
	if face_material:
		face_material.set_shader_parameter("expression",float(expression));face_material.set_shader_parameter("previous_expression",float(expression_previous));face_material.set_shader_parameter("transition",expression_blend);face_material.set_shader_parameter("brightness",module.power*(.75 if awake else .05));face_material.set_shader_parameter("gaze",Vector2(yaw*.08,-pitch*.04))

func animate_content()->void:
	for i in range(content.size()):
		var item:Dictionary=content[i];item.node.visible=i==loaded_index and owners[i]=="platter" and print_amount>.0001
		item.node.scale=Vector3.ONE
		if i==1 and butterfly_drive:butterfly_drive.apply();continue
		if i==2 and ship_drive:ship_drive.apply();continue
		var p:float=observatory_parameter if i==0 and observatory_enabled else parameters[i];var phase:float=times[i];var energy:float=action_energy if i==loaded_index else 0
		var bias_angle:float=(p-.5)*TAU*float(observatory_profile.get("time_bias_minutes",30))/30.
		for r in item.rig:
			var t:Transform3D=r.home
			match str(r.kind):
				"hour":t.basis*=Basis(Vector3.BACK,-bias_angle/12.-phase*.11 if i==0 and observatory_enabled else -p*TAU-phase*.11)
				"minute":t.basis*=Basis(Vector3.BACK,-bias_angle-phase*1.32 if i==0 and observatory_enabled else -p*TAU*12-phase*1.32)
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
func physical_print_progress()->float:
	if ship_drive and loaded_index==2:return print_amount
	if butterfly_drive and loaded_index==1:return print_amount
	# Seal the substantial arcade at the energy peak, then finish the light
	# cupola/spire. A uniform height sweep spent its peak above the building.
	return .66*smoothstep(.20,.83,print_amount)+.34*smoothstep(.83,.99,print_amount)
func diagnostics()->Dictionary:
	return {"ship":ship_drive.state() if ship_drive else {},"stage":stage,"selected":selected,"loaded_index":loaded_index,"working_id":working_id,"owners":owners.duplicate(),"parameters":parameters.duplicate(),"observatory_parameter":observatory_parameter,"butterfly":butterfly_drive.state() if butterfly_drive else {},"times":times.duplicate(),"print_amount":print_amount,"physical_print_progress":physical_print_progress(),"display_amount":print_amount,"read_progress":read_progress,"action_energy":action_energy,"action_count":action_count,"spin_enabled":spin_enabled,"spin_velocity":spin_velocity,"platter_angle":platter_angle,"magazine_angle":magazine_angle,"playback_paused":playback_paused,"grip":grip,"beam_gain":beam_gain,"iris_open":iris_open,"expression":expression,"expression_previous":expression_previous,"expression_blend":expression_blend,"face_pose":[face_pose.x,face_pose.y,face_pose.z,face_pose.w],"record_radius":spec.record_radius,"tone_lift":tone_lift,"tone_angle":tone_angle,"ready_to_fold":ready_to_fold(),"cycle_count":cycle_count,"queue":queue_events.duplicate(true)}
