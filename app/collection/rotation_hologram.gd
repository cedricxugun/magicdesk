extends Node3D
## Shared base-mounted optical rotation control. It never drives the record spindle.
const ART:="res://assets/collection/art/shared_rotation/"
const FACE_ART:="contrast_r3/"
const ICON_POS:=Vector3(1.91,.28,.27)
const PORT_POS:=Vector3(1.34269,.145,.27218)
const ICON_SIZE:=.28
const IDLE_AMOUNT:=.28 # Retain a discoverable contour on light desktops.
var service:Node3D
var host:Node3D
var optics:Node3D
var orbit:MeshInstance3D
var icon:MeshInstance3D
var echo:MeshInstance3D
var projection:MeshInstance3D
var port_light:OmniLight3D
var amount:=0.0
var linger:=0.0
var clock:=0.0
var press_age:=-1.0
var held:=false
var hover:=false
var spin_angle:=0.0
var showing_rotation:=false
var review_pointer:=Vector2(INF,INF)
var display_root:Node3D

func setup(owner:Node3D)->void:
	service=owner;host=service.host
	var port:Node3D=load("res://assets/collection/components/shared_rotation_emitter.glb").instantiate();add_child(port)
	display_root=Node3D.new();add_child(display_root);display_root.position=ICON_POS
	optics=Node3D.new();display_root.add_child(optics)
	orbit=_layer("Orbit",FACE_ART+"orbit.svg",Vector2.ONE*ICON_SIZE,optics)
	icon=_layer("Action",FACE_ART+"rotate.svg",Vector2.ONE*ICON_SIZE,optics);icon.position.z=.0005
	echo=_layer("Echo","echo.svg",Vector2.ONE*ICON_SIZE,optics);echo.position.z=.001
	projection=_layer("Projection","projection.svg",Vector2(.5,.18),self)
	port_light=OmniLight3D.new();add_child(port_light);port_light.position=PORT_POS+Vector3(.039,0,.008);port_light.light_color=Color(.16,.68,1.0);port_light.omni_range=.24;port_light.light_energy=0.0;port_light.shadow_enabled=false
	linger=2.0
	host.get_window().focus_exited.connect(cancel)
	tick(0.)

func _layer(label:String,path:String,size:Vector2,parent:Node3D)->MeshInstance3D:
	var result:=MeshInstance3D.new();result.name=label
	var shape:=QuadMesh.new();shape.size=size;result.mesh=shape
	var material:=ShaderMaterial.new();material.shader=load("res://collection/rotation_hologram.gdshader");material.set_shader_parameter("artwork",load(ART+path))
	material.set_shader_parameter("artwork_color",label in ["Orbit","Action"])
	result.material_override=material;result.cast_shadow=GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	parent.add_child(result);return result

func available()->bool:
	return service.state=="idle" and service.selector_amount<.01 and service.selector_target<.01 and not service.selector_wait and host.shutdown_time<0.0 and host.closing_time<0.0

func screen_center()->Vector2:return host.camera.unproject_position(display_root.global_position)
func radius_pixels()->float:
	# Forty logical points at default desktop scale; linked to base, not canvas pixels.
	var unit:float=screen_center().distance_to(host.camera.unproject_position(display_root.global_position+host.camera.global_basis.x*.20))
	return maxf(17.*DisplayServer.screen_get_scale(),unit)
func contains(point:Vector2)->bool:
	return available() and point.distance_to(screen_center())<=radius_pixels()
func input_region()->Rect2i:
	var radius:=radius_pixels();return Rect2i(Rect2(screen_center()-Vector2.ONE*radius,Vector2.ONE*radius*2.))
func cancel()->void:
	held=false;press_age=-1.;linger=0.
func consume(event:InputEvent)->bool:
	if event is InputEventMouseButton and event.button_index==MOUSE_BUTTON_LEFT:
		if event.pressed and contains(event.position):held=true;linger=2.;return true
		if not event.pressed and held:
			held=false
			if contains(event.position):service.toggle_display_rotation();press_age=0.;linger=2.;host.sound("click",.75)
			return true
	if event is InputEventMouseMotion and held:return true
	return false

func tick(delta:float)->void:
	clock+=delta
	var pointer:Vector2=review_pointer if review_pointer.is_finite() else service.pointer_position()
	hover=contains(pointer)
	var port_point:Vector2=host.camera.unproject_position(PORT_POS)
	# Port discovery stays a small region, clear of the neighboring shutdown cap.
	var at_port:bool=available() and pointer.distance_to(port_point)<5.*DisplayServer.screen_get_scale()
	if hover or at_port or held:linger=1.1
	else:linger=maxf(0.,linger-delta)
	amount=move_toward(amount,1.0 if available() and (linger>0. or held) else IDLE_AMOUNT if available() else 0.,delta*3.8)
	if not available():held=false
	if press_age>=0.:press_age+=delta
	if press_age>.65:press_age=-1.
	var compression:=.0
	if held:compression=.13
	elif press_age>=0.:compression=.15*exp(-press_age*10.)*cos(press_age*18.)
	optics.scale=Vector3.ONE*(1.-compression)
	display_root.global_basis=host.camera.global_basis
	if host.rotation_enabled:spin_angle+=delta*.48
	orbit.rotation.z=-spin_angle
	if showing_rotation!=host.rotation_enabled:
		showing_rotation=host.rotation_enabled
		icon.material_override.set_shader_parameter("artwork",load(ART+FACE_ART+("pause.svg" if showing_rotation else "rotate.svg")))
	var presence:=smoothstep(0.,IDLE_AMOUNT,amount)
	var face_gain:float=presence*lerpf(.68,.94,smoothstep(IDLE_AMOUNT,1.,amount))
	for layer in [orbit,icon]:
		layer.material_override.set_shader_parameter("gain",face_gain)
		layer.material_override.set_shader_parameter("reveal",presence);layer.material_override.set_shader_parameter("clock",clock)
	var echo_amount:float=(1.-press_age/.65)*.50*presence if press_age>=0. and available() else 0.
	echo.scale=Vector3.ONE*(1.+maxf(0.,press_age)*.75);echo.material_override.set_shader_parameter("gain",echo_amount)
	# Project authored optical strands between the real slit and the floating face.
	var center:=display_root.global_position;var camera_z:Vector3=host.camera.global_basis.z
	var axis:Vector3=center-PORT_POS;var plane_x:=axis.normalized();var plane_y:Vector3=camera_z.cross(plane_x).normalized()
	projection.global_transform=Transform3D(Basis(plane_x,plane_y,plane_x.cross(plane_y)),(center+PORT_POS)*.5)
	projection.scale=Vector3(axis.length()/.5,1.,1.)
	port_light.light_energy=smoothstep(.12,.9,amount)*.32
	projection.material_override.set_shader_parameter("gain",amount*.42);projection.material_override.set_shader_parameter("reveal",amount)

func state()->Dictionary:
	return {"visible_amount":amount,"hover":hover,"held":held,"rotation":host.rotation_enabled,"screen_center":[screen_center().x,screen_center().y],"hit_radius":radius_pixels(),"port_world":[PORT_POS.x,PORT_POS.y,PORT_POS.z],"face_gain":icon.material_override.get_shader_parameter("gain"),"face_reveal":icon.material_override.get_shader_parameter("reveal"),"action_art":icon.material_override.get_shader_parameter("artwork").resource_path}
