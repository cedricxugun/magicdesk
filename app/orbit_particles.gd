extends Node3D

const COUNT:=12
var spawn_serial:=0
var host:Node3D
var core:Node3D
var clock:=0.0
var reveal_pending:=false
var burst_time:=-1.0
var burst_next:=0.0
var emitted:=0
var steady_timer:=0.0
var cancelled:=false
var particles:Array=[]
var rng:=RandomNumberGenerator.new()
var trail_mesh:=ImmediateMesh.new()
var trail_node:MeshInstance3D

func setup(owner:Node3D)->void:
	host=owner;core=host.named("P_Solar_Crystal");rng.seed=731905
	var halo_shader:=Shader.new()
	halo_shader.code="""
shader_type spatial;
render_mode unshaded,cull_disabled,depth_draw_never;
uniform float strength=0.0;
void vertex(){MODELVIEW_MATRIX=VIEW_MATRIX*mat4(INV_VIEW_MATRIX[0],INV_VIEW_MATRIX[1],INV_VIEW_MATRIX[2],MODEL_MATRIX[3]);}
void fragment(){float r=length(UV*2.0-1.0);float soft=exp(-r*r*4.8)*(1.0-smoothstep(.5,1.0,r));float hot=exp(-r*r*65.0);ALBEDO=mix(vec3(1.0,.027,.018),vec3(1.0,.88,.82),hot);EMISSION=mix(vec3(2.2,.025,.018),vec3(8.0,5.2,4.5),hot);ALPHA=soft*strength;}
"""
	var halo_mesh:=QuadMesh.new();halo_mesh.size=Vector2(.17,.17)
	var head_shader:=Shader.new();head_shader.code="""
shader_type spatial;
render_mode unshaded,depth_draw_never;
uniform float strength=1.0;
void fragment(){float facing=max(dot(normalize(NORMAL),normalize(VIEW)),0.0);float soft=smoothstep(.04,.82,facing);ALBEDO=vec3(1.0,.91,.88);EMISSION=vec3(8.0,5.0,4.6)*strength;ALPHA=soft*strength;}
"""
	var sphere:=SphereMesh.new();sphere.radius=.025;sphere.height=.050;sphere.radial_segments=10;sphere.rings=6
	for i in range(COUNT):
		var point:=MeshInstance3D.new();point.mesh=sphere;point.cast_shadow=GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
		var mat:=ShaderMaterial.new();mat.shader=head_shader
		point.material_override=mat;add_child(point);point.hide()
		var halo:=MeshInstance3D.new();halo.mesh=halo_mesh
		var halo_mat:=ShaderMaterial.new();halo_mat.shader=halo_shader;halo.material_override=halo_mat
		halo.cast_shadow=GeometryInstance3D.SHADOW_CASTING_SETTING_OFF;add_child(halo);halo.hide()
		particles.append({"node":point,"halo":halo,"halo_mat":halo_mat,"mat":mat,"age":0.0,"life":0.0,"center":Vector3.ZERO,"a":Vector3.RIGHT,"b":Vector3.UP,"r":.7,"turn":2.0,"lift":.3,"scale":1.0,"trail":[],"cancel":-1.0,"phase":0.0})
	trail_node=MeshInstance3D.new();trail_node.mesh=trail_mesh;trail_node.cast_shadow=GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	var shader:=Shader.new();shader.code="""
shader_type spatial;
render_mode unshaded,cull_disabled,depth_draw_never;
void fragment(){
 float across=abs(UV.y*2.0-1.0);
 float soft=pow(max(0.0,1.0-across),1.7);
 float hot=pow(max(0.0,1.0-across),10.0);
 ALBEDO=mix(vec3(1.0,.025,.009),vec3(1.0,.77,.43),hot);
 EMISSION=mix(vec3(1.8,.012,.003),vec3(5.0,2.3,.8),hot);
 ALPHA=COLOR.a*soft;
}
"""
	var mat:=ShaderMaterial.new();mat.shader=shader;trail_node.material_override=mat;add_child(trail_node)
	# Resident nondegenerate topology initializes the trail pipeline inside the core.
	trail_mesh.surface_begin(Mesh.PRIMITIVE_TRIANGLES)
	for p in [Vector3.ZERO,Vector3(.0001,0,0),Vector3(0,.0001,0)]:
		trail_mesh.surface_set_color(Color(1,1,1,0));trail_mesh.surface_set_uv(Vector2.ZERO);trail_mesh.surface_add_vertex(p+core.global_position)
	trail_mesh.surface_end()

func trigger(kind:String)->void:
	match kind:
		"open":reveal_pending=true;cancelled=false;burst_time=-1.0
		"ignition":cancelled=false
		"overload":cancelled=false;burst_time=0.0;burst_next=0.0;emitted=0
		"close","shutdown","explode","cancel","assemble":
			cancelled=true;reveal_pending=false;burst_time=-1.0
			for p in particles:
				if float(p.life)>0:p.cancel=.65

func _emit()->void:
	for p in particles:
		if float(p.life)>0:continue
		var theta:=TAU*float(spawn_serial%12)/12.0+rng.randf_range(-.13,.13)
		spawn_serial+=1
		var tilt:=deg_to_rad(rng.randf_range(18.0,28.0))
		var skew:=deg_to_rad(rng.randf_range(-9.0,9.0))
		var a:=Vector3(cos(skew),sin(skew),0)
		var b:=Vector3(0,sin(tilt),cos(tilt)).normalized()
		p.a=a;p.b=b;p.center=core.global_position+Vector3(0,rng.randf_range(.28,.43),0)
		p.age=0.0;p.life=rng.randf_range(8.0,11.5)
		p.r=rng.randf_range(2.20,2.48);p["minor"]=rng.randf_range(.94,1.20)
		p.turn=rng.randf_range(.70,.95)*(-1 if spawn_serial%3==0 else 1)
		p.lift=theta;p.scale=rng.randf_range(.84,1.12);p.phase=rng.randf_range(0,TAU)
		p.cancel=-1.0;p.trail.clear();p.node.global_position=core.global_position+a*.27;p.node.show();p.halo.show()
		return

func tick(delta:float)->void:
	clock+=delta
	var allowed:=not cancelled and float(host.openness)>.52 and float(host.power)>.15 and float(host.explosion)<.04
	if reveal_pending and allowed:
		reveal_pending=false;burst_time=0.0;burst_next=0.0;emitted=0
	if burst_time>=0.0:
		burst_time+=delta
		while allowed and burst_time>=burst_next and emitted<10:
			_emit();emitted+=1;burst_next+=.055
		if emitted>=10:burst_time=-1.0
	elif allowed:
		steady_timer+=delta
		if steady_timer>.75:_emit();steady_timer=0.0
	for p in particles:
		if float(p.life)<=0.0:continue
		p.age+=delta
		if float(p.cancel)>=0.0:p.cancel-=delta
		if float(p.age)>=float(p.life) or (float(p.cancel)<0.0 and float(p.cancel)>-delta*1.1):
			p.life=0.0;p.node.hide();p.halo.hide();p.trail.clear();continue
		var u:float=p.age/p.life
		var sweep:float=p.lift+p.turn*float(p.age)
		var entry:=smoothstep(0.0,.85,float(p.age))
		var orbit_position:Vector3=p.center+p.a*cos(sweep)*float(p.r)+p.b*sin(sweep)*float(p.minor)
		var seed_position:Vector3=core.global_position+(orbit_position-core.global_position).normalized()*.27
		var position:Vector3=seed_position.lerp(orbit_position,entry)
		position+=Vector3(0,sin(float(p.age)*1.35+p.phase)*.022,0)
		p.node.global_position=position
		var fade:=smoothstep(0.0,.10,float(p.age))*(1.0-smoothstep(float(p.life)-.8,float(p.life),float(p.age)))
		if float(p.cancel)>=0.0:fade*=smoothstep(0.0,.65,p.cancel)
		p.node.scale=Vector3.ONE*float(p.scale)*maxf(.01,sqrt(fade))
		p.mat.set_shader_parameter("strength",fade)
		p.halo.global_position=position;p.halo.scale=Vector3.ONE*float(p.scale);p.halo_mat.set_shader_parameter("strength",fade*.82)
		p.trail.append({"p":position,"time":clock})
		while p.trail.size()>2 and (clock-float(p.trail[0].time)>1.12 or p.trail.size()>70):p.trail.pop_front()
		p["fade"]=fade
	_render_trails()

func _render_trails()->void:
	trail_mesh.clear_surfaces()
	var started:=false
	var camera:=get_viewport().get_camera_3d()
	if camera==null:return
	for p in particles:
		if float(p.life)<=0.0 or p.trail.size()<2:continue
		if not started:trail_mesh.surface_begin(Mesh.PRIMITIVE_TRIANGLES);started=true
		for i in range(p.trail.size()-1):
			var a:Vector3=p.trail[i].p;var b:Vector3=p.trail[i+1].p
			if a.distance_squared_to(b)<.0000001:continue
			var normal:Vector3=(b-a).normalized().cross((camera.global_position-(a+b)*.5).normalized()).normalized()
			var tail:=float(i+1)/float(p.trail.size());var width:=.0085*float(p.scale)*(.35+.65*tail)
			var alpha:=float(p.fade)*pow(tail,.68)*.92
			var points:Array[Vector3]=[a-normal*width,b-normal*width,b+normal*width,a-normal*width,b+normal*width,a+normal*width]
			var uvs:Array[Vector2]=[Vector2(0,0),Vector2(1,0),Vector2(1,1),Vector2(0,0),Vector2(1,1),Vector2(0,1)]
			for j in range(6):
				trail_mesh.surface_set_color(Color(1,1,1,alpha));trail_mesh.surface_set_uv(uvs[j]);trail_mesh.surface_add_vertex(to_local(points[j]))
	if started:trail_mesh.surface_end()
