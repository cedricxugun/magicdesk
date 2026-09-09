extends "res://collection/g_instrument.gd"
## The six leaves are indexed media. Reading is automatic; the reward is a
## different directly controllable miniature, not a repeated alignment puzzle.
var archive_bound:=false
var content:Array=[]
var lift:Node3D
var slide:Node3D
var locks:Array=[]
var parameters:Array[float]=[.5,.75,.5,.35,.5,.70]
var times:Array[float]=[0,0,0,0,0,0]
var loaded_index:=-1
var read_progress:=0.0
var display_amount:=0.0
var platform_amount:=0.0
var action_energy:=0.0
var playback_paused:=false
var action_count:=0
var action_pulse:=0.0
var presentation:Array[float]=[0,0,0,0,0,0]

func pulse_action()->void:action_pulse=1.25;action_count+=1;playback_paused=false

func page_goal(i:int)->float:
	if not module.data.g_archive.get("indexed_presentation",false):return 0.0
	return 1.0 if ((i<3)==(selected<3)) and i%3<selected%3 else 0.0

func pages_settled()->bool:
	for i in range(6):
		if absf(presentation[i]-page_goal(i))>.001:return false
	return true

func setup(owner:Node3D)->void:
	super.setup(owner);module.play.values.fold=parameters[0]

func bind_archive()->void:
	if archive_bound:return
	lift=module.named(module.data.g_archive.lift);slide=module.named(module.data.g_archive.slide)
	for item in module.data.g_archive.contents:
		var rig:Array=[]
		for r in item.rig:rig.append({"node":module.named(r.name),"kind":str(r.kind),"home":module.pose(r.home),"data":r})
		content.append({"node":module.named(item.root),"rig":rig,"title":str(item.title),"parameter":str(item.parameter),"action":str(item.action)})
	for l in module.data.g_archive.locks:locks.append({"node":module.named(l.name),"home":module.pose(l.home),"side":float(l.side)})
	archive_bound=true

func changed(key:String,_before:Variant,requested:Variant,event:String)->void:
	if key=="leaf":
		selected=clampi(roundi(float(requested)),0,5);module.play.values.fold=parameters[selected]
	elif key=="fold":parameters[selected]=clampf(float(requested),0,1)
	elif key=="imprint" and event=="begin":action_count+=1;playback_paused=false
	if event=="cancel":writing=false

func tick(delta:float)->void:
	time+=delta
	var live:=operating();var ready:bool=live and module.openness>.995
	for i in range(6):
		actual[i]=.5
		selection[i]=move_toward(selection[i],1.0 if ready and i==selected else 0.0,delta*3)
	var changing:bool=loaded_index!=selected
	if not live or changing:
		display_amount=move_toward(display_amount,0,delta*2.8)
		if display_amount<.001:
			for i in range(6):writers[i]=move_toward(writers[i],0,delta*2)
			pins=move_toward(pins,0,delta*4)
	var heads_clear:bool=writers.all(func(v):return v<.001) and pins<.001
	if ready and (not changing or (display_amount<.001 and heads_clear)):
		for i in range(6):presentation[i]=move_toward(presentation[i],page_goal(i),delta*1.15)
	elif not live and display_amount<.001 and heads_clear:
		for i in range(6):presentation[i]=move_toward(presentation[i],0,delta*1.15)
	if changing and ready and display_amount<.001 and heads_clear and pages_settled():loaded_index=selected;read_progress=0
	if ready and loaded_index==selected and platform_amount>.99 and pages_settled():
		read_progress=minf(1,read_progress+delta/1.15)
		records[selected]=read_progress;writers[selected]=read_progress
		pins=move_toward(pins,1,delta*4)
		if read_progress>=1:display_amount=move_toward(display_amount,1,delta*2)
	if live:
		if ready and loaded_index==selected and pages_settled():platform_amount=move_toward(platform_amount,1,delta*1.4)
	elif display_amount<.001 and writers.all(func(v):return v<.001):platform_amount=move_toward(platform_amount,0,delta*1.6)
	var playing:bool=ready and loaded_index==selected and display_amount>.99
	var hold:bool=module.play.number("imprint")>.5 or action_pulse>0.0
	if playing:action_pulse=maxf(0,action_pulse-delta)
	action_energy=move_toward(action_energy,1.0 if playing and hold else 0.0,delta*(5.0 if hold else 1.5))
	writing=playing and hold
	if playing and not playback_paused:
		var speed:float=.75+action_energy*3.0
		if selected==5:speed=(parameters[5]-.5)*2.0*(1.0+action_energy*4)
		times[selected]+=delta*speed
	projection=display_amount;alignment=1.0 if playing else 0.0;bank_quality=[0.0,0.0];bank_quality[0 if selected<3 else 1]=display_amount
	blocked=false
	if not live:stage="stowing" if not ready_to_fold() or module.openness>.001 or module.explosion>.001 else "sleep"
	elif not ready:stage="opening"
	elif changing and (display_amount>.001 or not heads_clear):stage="changing_media"
	elif not pages_settled():stage="positioning_page"
	elif platform_amount<.99:stage="extending_platen"
	elif read_progress<1:stage="reading"
	elif display_amount<.99:stage="reconstructing"
	elif playback_paused:stage="paused"
	else:stage="playing"
	if not live and ready_to_fold():loaded_index=-1;read_progress=0

func ready_to_fold()->bool:
	return display_amount<.001 and platform_amount<.001 and pins<.001 and writers.all(func(v):return v<.001) and selection.all(func(v):return v<.001) and presentation.all(func(v):return v<.001)

func crest()->float:return action_energy

func apply()->void:
	super.apply();bind_archive()
	for i in range(6):
		var leaf:Dictionary=leaves[i];var p:float=smoothstep(0,1,presentation[i]);var side:float=leaf.side
		leaf.node.position.x+=side*(.41+float(i%3)*.18)*p
		leaf.node.basis=Basis(Vector3.UP,-side*PI*.5*p)
		for rod in leaf.supports:
			var a:Vector3=rod.anchor;var end:Vector3=leaf.node.transform*Vector3(side*.06,float(rod.height),0);var v:Vector3=end-a
			rod.node.transform=Transform3D(Basis(Quaternion(Vector3.UP,v.normalized()))*Basis.from_scale(Vector3(1,v.length(),1)),(a+end)*.5)
	lift.position.y=.11*platform_amount
	slide.position.z=.61*smoothstep(.18,1,platform_amount)
	for l in locks:
		var t:Transform3D=l.home;t.basis*=Basis(Vector3.BACK,float(l.side)*smoothstep(0,.065,module.openness)*1.15);l.node.transform=t
	for i in range(content.size()):
		var item:Dictionary=content[i];item.node.visible=i==loaded_index and display_amount>.001
		# Scan reconstruction scales from its platen; it never pops in at full size.
		item.node.scale=Vector3.ONE*maxf(.001,smoothstep(0,1,display_amount))*float(module.data.g_archive.get("specimen_scale",1.0))
		var p:float=parameters[i];var phase:float=times[i];var energy:float=action_energy if i==loaded_index else 0.0
		var unfold:float=smoothstep(.20,.90,display_amount)
		for r in item.rig:
			var t:Transform3D=r.home
			match str(r.kind):
				"hour":t.basis*=Basis(Vector3.BACK,(-p*TAU-phase*.11)*unfold)
				"minute":t.basis*=Basis(Vector3.BACK,(-p*TAU*12-phase*1.32)*unfold)
				"gear":t.basis*=Basis(Vector3.BACK,phase*float(r.data.ratio))
				"pendulum":t.basis*=Basis(Vector3.BACK,sin(phase*5.5)*(.12+energy*float(r.data.get("swing_gain",.56)))*unfold)
				"wing":t.basis*=Basis(Vector3.UP,float(r.data.side)*lerpf(1.45,(1-p)*1.3+sin(phase*9.0-float(r.data.get("phase",0)))*(.06+energy*.38)*(1.0 if r.data.get("upper",true) else .72),unfold))
				"ship":t.origin.y+=sin(phase*2)*(.008+energy*.028);t.basis*=Basis(Vector3.BACK,sin(phase*2.4)*(.03+energy*.10))
				"sail":t.basis*=Basis(Vector3.UP,lerpf(1.35*float(r.data.get("side",1)),(p-.5)*1.8+sin(phase*.8)*energy*.12,unfold))
				"wave":t.origin.y+=sin(phase*2.4+float(r.data.phase))*(.005+energy*.012)
				"petal":
					var bloom:float=clampf((p+energy*.65-float(r.data.flower)*.08)*unfold,0,1)
					t.basis*=Basis(Vector3.BACK,(1-bloom)*1.1+sin(phase+float(r.data.petal))*.025)
				"orbit_tilt":t.basis=Basis(Quaternion.IDENTITY.slerp(t.basis.get_rotation_quaternion(),unfold))*Basis(Vector3.RIGHT,(p-.5)*unfold)
				"orbit":t.basis*=Basis(Vector3.UP,phase*float(r.data.ratio))
				"traveller":
					var progress:float=fposmod(phase*.055,1);var a:float=progress*TAU*1.35
					t.origin=Vector3(.22*cos(a),.098+progress*17*.036+.010*sin(fposmod(progress*18,1)*PI),-.22*sin(a))
				"traveller_return":
					var progress:float=fposmod(phase*.055,1);var height:float=r.data.height;var turns:float=r.data.turns
					var top:=Vector3(.22*cos(TAU*turns),.113+height,-.22*sin(TAU*turns))
					if progress<.70:
						var u:=smoothstep(0,.70,progress);t.origin=Vector3(.22*cos(u*TAU*turns),.113+u*height,-.22*sin(u*TAU*turns))
					elif progress<.78:t.origin=top.lerp(Vector3(0,.113+height,0),smoothstep(.70,.78,progress))
					elif progress<.94:t.origin=Vector3(0,.113+height*(1-smoothstep(.78,.94,progress)),0)
					else:t.origin=Vector3(.22*smoothstep(.94,1,progress),.113,0)
			if r.node.transform!=t:r.node.transform=t

func diagnostics()->Dictionary:
	return {"stage":stage,"selected":selected,"title":str(module.data.g_archive.contents[selected].title),"loaded_index":loaded_index,"parameters":parameters.duplicate(),"presentation":presentation.duplicate(),"read_progress":read_progress,"display_amount":display_amount,"platform_amount":platform_amount,"action_energy":action_energy,"action_count":action_count,"playback_paused":playback_paused,"times":times.duplicate(),"ready_to_fold":ready_to_fold(),"workflow":"open book -> physically present selected media -> extend platen -> read -> reconstruct -> play"}
