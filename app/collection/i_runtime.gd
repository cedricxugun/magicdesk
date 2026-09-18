extends Node
## Opt-in driver for the isolated I component, reusable by its eventual module.
const Acoustics=preload("res://collection/i_acoustics.gd")
var simulation:RefCounted=Acoustics.new()
var asset:Node3D
var rig:Dictionary
var panels:Array=[]
var leaves:Array=[]
var cam:Node3D
var cam_home:Transform3D
var front:Node3D
var diaphragm:Node3D
var relief:Node3D
var wall:MeshInstance3D
var travel_meshes:Array[MeshInstance3D]=[]
var opening:=0.
var visuals:Node3D
var service:RefCounted
var held_pressure:=false
func node(label:String)->Node3D:
	return asset if str(asset.name)==label else asset.find_child(label,true,false) as Node3D
func setup(root:Node3D,service_rig_path:String="res://assets/collection/i_service_rig.json",body_rig_path:String="res://assets/collection/i_runtime_rig.json")->void:
	asset=root;rig=JSON.parse_string(FileAccess.get_file_as_string(body_rig_path))
	for item in rig.panels:
		var n:Node3D=node(item.name);assert(n!=null,"Missing I panel")
		panels.append({"node":n,"home":n.transform,"direction":Vector3(item.direction[0],item.direction[1],item.direction[2]),"stroke":item.stroke})
	for name in rig.leaves:
		var n:Node3D=node(name);assert(n!=null,"Missing iris leaf");leaves.append({"node":n,"home":n.transform})
	cam=node(rig.cam);cam_home=cam.transform;front=node(rig.front);diaphragm=node(rig.diaphragm);relief=node(rig.relief)
	wall=node(rig.wall) as MeshInstance3D
	for name in [rig.surround]+rig.springs:
		var mesh:MeshInstance3D=node(name) as MeshInstance3D;assert(mesh!=null and mesh.find_blend_shape_by_name("Travel")>=0);travel_meshes.append(mesh)
	assert(wall!=null and wall.find_blend_shape_by_name("Compression")>=0)
	apply_state(simulation.state(),0.)
	if node("IS4_IrisCartridge")!=null:
		service=load("res://collection/i_service.gd").new();service.setup(asset,service_rig_path)
func request_service()->void:
	held_pressure=false
	if service!=null:service.request_service(simulation)
	else:simulation.quiet()
func request_stow()->void:
	held_pressure=false
	if service!=null:service.request_stow(simulation)
	else:simulation.quiet()
func request_operation()->void:
	if service!=null:service.request_operation(simulation)
	else:simulation.start()
func control(key:String,value:float,phase:String)->void:
	if phase=="cancel":request_stow();return
	if key=="service":
		if phase in ["begin","change"]:
			if value<-.55:request_service()
			elif value>.55:request_stow()
		return
	if key not in ["frequency","throat","bellows"]:return
	if key=="frequency":simulation.set_controls(value,simulation.throat)
	elif key=="throat":simulation.set_controls(simulation.frequency,value)
	elif key=="bellows":held_pressure=value>.5
	if phase=="begin":request_operation()
	if key=="bellows" and (service==null or service.amount==0.):simulation.set_pressed(held_pressure)
func enable_visuals()->void:
	if visuals!=null:return
	visuals=load("res://collection/i_visuals.gd").new();asset.add_child(visuals);visuals.setup(asset,rig)
func tick(delta:float)->Array:
	simulation.tick(delta)
	if service!=null:service.tick(delta,simulation,opening)
	var target:float=1. if simulation.listening else 0. if simulation.ready_to_close() else opening
	opening=move_toward(opening,target,delta*2.)
	apply_state(simulation.state(),opening)
	if service!=null:
		service.apply()
		if service.amount==0. and service.requested=="operate" and simulation.pressed!=held_pressure:simulation.set_pressed(held_pressure)
	var events:Array=simulation.drain_events()
	if visuals!=null:visuals.update(simulation.clock,simulation.state(),events,simulation.return_schedule())
	return events
func apply_state(state:Dictionary,body_open:float)->void:
	opening=clampf(body_open,0.,1.)
	for item in panels:item.node.transform=item.home;item.node.position=item.home.origin+item.direction*item.stroke*opening
	for item in leaves:item.node.transform=item.home;item.node.basis=item.home.basis*Basis(Vector3.UP,-1.05*float(state.iris))
	cam.transform=cam_home;cam.basis=cam_home.basis*Basis(Vector3.UP,-.30*float(state.iris))
	front.position.y=-.23+float(rig.stroke)*float(state.compression)
	var displacement:float=clampf(float(state.diaphragm)*float(rig.visual_amplification),-float(rig.visual_limit),float(rig.visual_limit))
	diaphragm.position.y=.235-displacement
	relief.position.y=.293+.012*(1. if state.stage in ["rest","recover"] else clampf((1.-float(state.pressure))*12.,0.,1.))
	wall.set_blend_shape_value(wall.find_blend_shape_by_name("Compression"),float(state.compression))
	for mesh in travel_meshes:mesh.set_blend_shape_value(mesh.find_blend_shape_by_name("Travel"),displacement/float(rig.visual_limit))
