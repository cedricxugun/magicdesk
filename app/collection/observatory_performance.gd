extends Node3D
## Authored dial mask and local material/light response on the real component.
var module:Node3D
var player:RefCounted
var surfaces:Array=[]
var dial:Node3D
var pointer:Node3D
var globe:Node3D
var crown:Node3D
var trace:MeshInstance3D
var lamp:OmniLight3D
var activity:=0.
var previous_parameter:=.5
var gain:=0.
var profile:Dictionary
func setup(owner:Node3D,materials:Array)->void:
	module=owner;player=module.play.g_instrument;surfaces=materials
	profile=JSON.parse_string(FileAccess.get_file_as_string("res://assets/collection/observatory_interaction.json"))
	dial=module.named("GO2_TimeDial");pointer=module.named("GO2_Time_minute");globe=module.named("GO2_MainArmillarySpin");crown=module.named("GO2_CrownOrbit")
	var texture:Texture2D=load(profile.calibration_mask.path)
	var center:=Vector2(profile.calibration_mask.center[0],profile.calibration_mask.center[1])
	trace=MeshInstance3D.new();var quad:=QuadMesh.new();var size:float=profile.calibration_mask.dial_radius/profile.calibration_mask.radius;quad.size=Vector2.ONE*size;trace.mesh=quad
	var mat:=ShaderMaterial.new();mat.shader=load("res://collection/observatory_calibration.gdshader");mat.set_shader_parameter("pattern",texture);mat.set_shader_parameter("mask_center",center);trace.material_override=mat
	trace.cast_shadow=GeometryInstance3D.SHADOW_CASTING_SETTING_OFF;dial.add_child(trace);trace.position.z=.008;trace.hide()
	lamp=OmniLight3D.new();lamp.light_color=Color(1.,.53,.17);lamp.omni_range=.26;lamp.light_specular=.12;lamp.light_energy=0;add_child(lamp)
	for m in surfaces:m.set_shader_parameter("interaction_pattern",texture);m.set_shader_parameter("interaction_mask_center",center);m.set_shader_parameter("interaction_mask_radius",profile.calibration_mask.radius)
func tick(delta:float,warm:bool=false)->void:
	var showing:bool=player.loaded_index==0 and player.selected==0 and player.stage in ["playing","paused"] and player.print_amount>.999 and module.power>.01 and module.explosion<.001 and not module.stowing
	var moving:bool=absf(player.observatory_parameter-previous_parameter)>.000001
	previous_parameter=player.observatory_parameter
	activity=move_toward(activity,1.0 if showing and moving else 0.,delta*(9. if moving else 2.4))
	var energy:float=player.action_energy if showing else 0.
	gain=maxf(activity,energy*.8)*module.power if showing else 0.
	if warm:gain=1.;energy=1.
	# The full time circle extends behind the jambs. The lower central arc
	# is physically visible, so use it as the calibration feedback range.
	var angle:float=PI*(.28+.44*player.observatory_parameter)
	trace.visible=gain>.002;trace.material_override.set_shader_parameter("gain",gain);trace.material_override.set_shader_parameter("pointer_angle",angle);trace.material_override.set_shader_parameter("charge",energy)
	var glow:float=energy*energy
	for mat in surfaces:
		mat.set_shader_parameter("interaction_center",globe.global_position);mat.set_shader_parameter("interaction_axis",globe.global_basis.y.normalized());mat.set_shader_parameter("interaction_x",globe.global_basis.x.normalized());mat.set_shader_parameter("interaction_z",globe.global_basis.z.normalized())
		mat.set_shader_parameter("interaction_gain",glow);mat.set_shader_parameter("interaction_crown",crown.global_position);mat.set_shader_parameter("interaction_crown_gain",smoothstep(.35,1.,energy))
	lamp.global_position=globe.global_position+module.named("GA_Observatory").global_basis.z.normalized()*.065;lamp.light_energy=glow*.035
func state()->Dictionary:
	return {"activity":activity,"trace_gain":gain,"light_energy":lamp.light_energy,"parameter":player.observatory_parameter,"requested":player.parameters[0],"charge":player.action_energy}
