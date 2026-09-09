extends RefCounted
## Six persistent indexed leaves, bounded cam transport and geometric optics.
## The motor drives kinematics; the optical gate uses real ray/plane intersections.
var module:Node3D
var leaves:Array=[]
var covers:Array=[]
var folds:Array[float]=[.5,.5,.5,.5,.5,.5]
var actual:Array[float]=[.5,.5,.5,.5,.5,.5]
var records:Array[float]=[0,0,0,0,0,0]
var selected:=0
var selection:Array[float]=[0,0,0,0,0,0]
var writers:Array[float]=[0,0,0,0,0,0]
var pins:=0.0
var alignment:=0.0
var bank_quality:Array[float]=[0,0]
var rays:Array=[]
var stage:="rest"
var writing:=false
var projection:=0.0
var peak_time:=-1.0
var peak_count:=0
var blocked:=false
var time:=0.0
var rig_ready:=false

func setup(owner:Node3D)->void:module=owner

func bind()->void:
	if rig_ready:return
	for item in module.data.g_mechanism.leaves:
		var supports:Array=[]
		for s in item.supports:supports.append({"node":module.named(s.node),"anchor":module.v3(s.anchor),"height":float(s.height)})
		leaves.append({"node":module.named(item.node),"face":module.named(item.face),"writer":module.named(item.writer),"pin":module.named(item.register),"side":float(item.side),"layer":int(item.layer),"supports":supports})
	for item in module.data.g_mechanism.get("covers",[]):
		var supports:Array=[]
		for s in item.supports:supports.append({"node":module.named(s.node),"anchor":module.v3(s.anchor),"height":float(s.height)})
		covers.append({"node":module.named(item.node),"side":float(item.side),"supports":supports})
	rig_ready=true

func changed(key:String,before:Variant,requested:Variant,event:String)->void:
	if key=="leaf":
		selected=clampi(roundi(float(requested)),0,5)
		module.play.values.fold=folds[selected]
	elif key=="fold":
		folds[selected]=clampf(float(requested),0,1)
		if absf(float(requested)-float(before))>.002 and records[selected]>.0:
			# A recorded plate is not erased by a knob click; changing registration
			# invalidates only the projected corridor. Mechanical carriage is kept.
			peak_time=-1
	elif key=="imprint" and event=="begin" and records[selected]>.999:
		records[selected]=0;peak_time=-1
	if event=="cancel":writing=false

func operating()->bool:
	return module.open_target>.5 and not module.stowing and module.explode_target<.001 and module.explosion<.001 and module.power>.01

func tick(delta:float)->void:
	time+=delta
	var live:=operating()
	var ready:bool=live and module.openness>.995
	for i in range(6):
		actual[i]=move_toward(actual[i],folds[i] if live else .5,delta*.65)
		selection[i]=move_toward(selection[i],1.0 if ready and i==selected else 0.0,delta*3)
		writers[i]=move_toward(writers[i],records[i] if live else 0.0,delta*.85)
	pins=move_toward(pins,1.0 if ready and alignment>.93 else 0.0,delta*3.5)
	var holding:bool=module.play.number("imprint")>.5
	blocked=ready and holding and alignment<.93
	writing=ready and holding and alignment>.93 and pins>.98 and records[selected]<1.0
	if writing:
		records[selected]=minf(1,records[selected]+delta/3.8)
		writers[selected]=records[selected]
		if records[selected]>=1:peak_time=0;peak_count+=1
	if peak_time>=0:
		peak_time+=delta
		if not ready or alignment<.85 or peak_time>7.5:peak_time=-1
	var goal:float=(.22+records[selected]*.50+crest()*.28)*alignment if ready and records[selected]>.001 else 0.0
	projection=move_toward(projection,goal,delta*.65)
	if not live:stage="rewind" if not ready_to_fold() else "rest"
	elif not ready:stage="unlatch"
	elif blocked:stage="misregistered"
	elif peak_time>=0:stage="memory_relief"
	elif writing:stage="inscribe"
	elif records[selected]>.001:stage="record_held"
	else:stage="registered" if alignment>.93 else "index"

func crest()->float:
	if peak_time<0:return 0
	return smoothstep(0.0,1.5,peak_time)*(1-smoothstep(4.8,7.5,peak_time))

func ready_to_fold()->bool:
	if projection>.001 or pins>.001:return false
	for i in range(6):
		if absf(actual[i]-.5)>.001 or writers[i]>.001 or selection[i]>.001:return false
	return true

func apply()->void:
	bind()
	var u:float=smoothstep(.32,1,module.openness)
	for i in range(6):
		var leaf:Dictionary=leaves[i];var side:float=leaf.side
		var angle:float=deg_to_rad(float(module.data.g_mechanism.fold_degrees))*(actual[i]-.5)*2.0*u
		leaf.node.position.x+=side*(actual[i]-.5)*.28*u
		leaf.node.position.z+=selection[i]*.035
		leaf.node.basis=Basis(Vector3.UP,-side*angle)
		leaf.writer.position.y=.50-writers[i]
		leaf.pin.position.z=.025*pins*side
		for rod in leaf.supports:
			var a:Vector3=rod.anchor;var end:Vector3=leaf.node.position+Vector3(side*.06,float(rod.height),0)
			var v:Vector3=end-a
			rod.node.transform=Transform3D(Basis(Quaternion(Vector3.UP,v.normalized()))*Basis.from_scale(Vector3(1,v.length(),1)),(a+end)*.5)
	for cover in covers:
		for rod in cover.supports:
			var a:Vector3=rod.anchor;var end:Vector3=cover.node.position+Vector3(0,float(rod.height),0)
			var v:Vector3=end-a
			rod.node.transform=Transform3D(Basis(Quaternion(Vector3.UP,v.normalized()))*Basis.from_scale(Vector3(1,v.length(),1)),(a+end)*.5)

func update_optics()->void:
	rays.clear()
	for bank in range(2):
		var side:int=-1 if bank==0 else 1
		var source:Node3D=module.named(module.data.sockets["source_"+str(side)])
		var origin:Vector3=source.global_position
		var direction:Vector3=module.global_basis*Vector3.BACK
		var quality:=1.0;var hits:Array=[];var end:=origin+direction*1.06
		# Source is behind the rear leaf: test rear to front, stopping at occlusion.
		for layer in [2,1,0]:
			var leaf:Dictionary=leaves[bank*3+layer];var face:Node3D=leaf.face
			var ro:Vector3=face.to_local(origin);var rd:Vector3=face.global_basis.inverse()*direction
			if absf(rd.z)<.001:quality=0;break
			var t:float=-ro.z/rd.z;var p:=ro+rd*t
			var radius:=Vector2(p.x-.47,p.y+.09).length()
			var angle:=acos(clampf(absf(rd.normalized().z),0,1))
			var transmission:float=(1-smoothstep(.073,.118,radius))*(1-smoothstep(deg_to_rad(1.0),deg_to_rad(3.0),angle))
			quality=minf(quality,transmission)
			var hit:Vector3=face.to_global(p)
			hits.append({"leaf":bank*3+layer,"radius":radius,"angle_degrees":rad_to_deg(angle),"transmission":transmission,"point":hit})
			if transmission<.01:end=hit;break
		bank_quality[bank]=quality
		rays.append({"start":origin,"end":end,"quality":quality,"hits":hits})
	alignment=bank_quality[0 if selected<3 else 1]

func diagnostics()->Dictionary:
	return {"stage":stage,"selected":selected,"folds":folds.duplicate(),"actual":actual.duplicate(),"records":records.duplicate(),"writers":writers.duplicate(),"pins":pins,"alignment":alignment,"bank_quality":bank_quality.duplicate(),"projection":projection,"writing":writing,"blocked":blocked,"peak_time":peak_time,"peak_count":peak_count,"ready_to_fold":ready_to_fold(),"optics":"world ray -> actual leaf plane -> bore radius AND collimator angle"}
