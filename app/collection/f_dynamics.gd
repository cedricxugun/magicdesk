extends RefCounted
## Closed four-bar linkage coupled to TWO spherical point-mass hangers.
## Gravity always points down. Prescribed yaw and magnetic bias are external
## drives. Massless rigid links are solved analytically; no variable-length rods.

const STEP:=1.0/240.0
const H:=Vector3(.4,2.64,.055)
const Q:=Vector3(.4,.934,.055)
const REST:=-42.0*PI/180.0
const RELEASE:=-50.0*PI/180.0
const DELTA:=-120.0*PI/180.0
var gravity:=9.81
var length_scale:=1.0
var right_length:=.82
var left_length:=.66
var counter_depth:=.18
var plumb_length:=.45
var prism_length:=.37
var lower_length:=1.01
var coupler_length:=.50
var right_mass:=1.0
var left_mass:=.56
var shaft_inertia:=.12
var spring:=2.2
var shaft_drag:=.65
var air_drag:=.25
var theta:=RELEASE
var omega:=0.0
var direction:=Vector3.DOWN
var direction_rate:=Vector3.ZERO
var right_direction:=Vector3.DOWN
var right_rate:=Vector3.ZERO
var accumulator:=0.0
var sim_time:=0.0
var heat:=0.0
var trim:=0.0
var brake:=0.0
var polarity:=0.0
var parking:=false
var yaw:=0.0
var yaw_rate:=0.0
var yaw_accel:=0.0
var last_yaw:=0.0
var last_yaw_rate:=0.0
var initialized:=false
var free:=false
var last_torque:=0.0
var stop_contacts:=0

func _init()->void:
	left_mass=right_mass*right_kinematics(REST)[1].y/(-left_length*cos(REST+DELTA))

func right_kinematics(q:float)->Array:
	var upper:=H+Vector3(right_length*cos(q),right_length*sin(q),0)
	var delta:=upper-Q;var distance:=delta.length();var along:=delta/distance
	var a:float=(lower_length*lower_length-coupler_length*coupler_length+distance*distance)/(2.0*distance)
	var height:=sqrt(maxf(.000001,lower_length*lower_length-a*a))
	var end:=Q+along*a+Vector3(along.y,-along.x,0)*height
	var top_j:=Vector3(-right_length*sin(q),right_length*cos(q),0)
	var top_j2:=Vector3(-right_length*cos(q),-right_length*sin(q),0)
	var lower:=end-Q;var coupler:=end-upper
	var determinant:=lower.x*coupler.y-lower.y*coupler.x
	var rhs:=coupler.dot(top_j)
	var j:=Vector3(-lower.y*rhs,lower.x*rhs,0)/determinant
	var rhs1:float=-j.length_squared()
	var rhs2:float=coupler.dot(top_j2)-(j-top_j).length_squared()
	var j2:=Vector3(rhs1*coupler.y-lower.y*rhs2,lower.x*rhs2-rhs1*coupler.x,0)/determinant
	return [end,j,j2,upper]

func release(angle:float=RELEASE,heading:float=0.0)->void:
	theta=angle;omega=0;direction=Vector3.DOWN;direction_rate=Vector3.ZERO
	right_direction=Vector3.DOWN;right_rate=Vector3.ZERO
	accumulator=0;last_yaw=heading;yaw=heading;last_yaw_rate=0;initialized=true;free=true

func advance(delta:float,heading:float)->void:
	if not initialized:release(theta,heading)
	var heading_step:=wrapf(heading-last_yaw,-PI,PI)
	yaw_rate=heading_step/maxf(delta,.00001)
	yaw_accel=(yaw_rate-last_yaw_rate)/maxf(delta,.00001)
	# The presentation yaw motor is acceleration-limited. Clamp exceptional
	# discontinuities from a reset command, rather than injecting an impulse.
	if absf(heading_step)>.5:yaw_rate=0;yaw_accel=0;direction_rate=Vector3.ZERO;right_rate=Vector3.ZERO
	yaw=heading;last_yaw=heading;last_yaw_rate=yaw_rate
	accumulator+=minf(delta,.20)
	while accumulator>=STEP:
		_integrate(STEP);accumulator-=STEP;sim_time+=STEP

func transport(amount:float,heading:float,delta:float=1.0,closing:bool=false)->void:
	free=false;initialized=false;accumulator=0;omega=0;direction_rate=Vector3.ZERO
	var target:=lerpf(-80.0*PI/180.0,REST if closing else RELEASE,smoothstep(0.0,1.0,amount))
	theta=move_toward(theta,target,delta*1.8)
	direction=Vector3.DOWN;right_direction=Vector3.DOWN;right_rate=Vector3.ZERO
	yaw=heading;last_yaw=heading;yaw_rate=0;yaw_accel=0

func _derivative(q:float,w:float,d:Vector3,u:Vector3,e:Vector3,v:Vector3)->Array:
	var rot:=Basis(Vector3.UP,yaw)
	var c:=rot*(H+Vector3(left_length*cos(q+DELTA),left_length*sin(q+DELTA),counter_depth))
	var j:=rot*Vector3(-left_length*sin(q+DELTA),left_length*cos(q+DELTA),0)
	var j2:=rot*Vector3(-left_length*cos(q+DELTA),-left_length*sin(q+DELTA),0)
	var k:=right_kinematics(q)
	var r:Vector3=rot*k[0];var rj:Vector3=rot*k[1];var rj2:Vector3=rot*k[2]
	var spin:=Vector3.UP*yaw_rate;var spin_accel:=Vector3.UP*yaw_accel
	var external_c:=j2*w*w+2.0*spin.cross(j*w)+spin_accel.cross(c)+spin.cross(spin.cross(c))
	var external_r:=rj2*w*w+2.0*spin.cross(rj*w)+spin_accel.cross(r)+spin.cross(spin.cross(r))
	var bob_velocity:=j*w+spin.cross(c)+plumb_length*u
	var prism_velocity:=rj*w+spin.cross(r)+prism_length*v
	var g:=Vector3.DOWN*(gravity/length_scale)
	var effective_g:=g-bob_velocity*((air_drag+7.0 if parking else air_drag)/left_mass)
	var effective_r:=g-prism_velocity*((air_drag+7.0 if parking else air_drag)/right_mass)
	if parking:effective_g+=Vector3(-d.x,0,-d.z)*12.0
	if parking:effective_r+=Vector3(-e.x,0,-e.z)*12.0
	var applied:float=-spring*(q-REST-trim*.55)-shaft_drag*w+.40*polarity
	if parking:applied+=-18.0*(q-REST)-4.5*w
	var projection:=j.dot(d)
	var right_projection:=rj.dot(e)
	var inertia:=shaft_inertia+left_mass*projection*projection+right_mass*right_projection*right_projection
	var constraint_force:=effective_g.dot(d)-external_c.dot(d)+plumb_length*u.length_squared()
	var right_constraint:=effective_r.dot(e)-external_r.dot(e)+prism_length*v.length_squared()
	var net:=applied+left_mass*projection*constraint_force+right_mass*right_projection*right_constraint
	var dry_friction:=brake*8.0
	var locked:bool=absf(w)<.006 and absf(net)<=dry_friction and brake>.01
	var acceleration:=0.0 if locked else (net-dry_friction*signf(w if absf(w)>.000001 else net))/inertia
	var support_accel:=external_c+j*acceleration
	var tension:=effective_g.dot(d)-support_accel.dot(d)+plumb_length*u.length_squared()
	var d_accel:Vector3=(effective_g-support_accel-tension*d)/plumb_length
	var right_support:=external_r+rj*acceleration
	var right_tension:=effective_r.dot(e)-right_support.dot(e)+prism_length*v.length_squared()
	var e_accel:Vector3=(effective_r-right_support-right_tension*e)/prism_length
	last_torque=net
	return [0.0 if locked else w,acceleration,u,d_accel,v,e_accel]

func _integrate(h:float)->void:
	var old_omega:=omega
	var a:=_derivative(theta,omega,direction,direction_rate,right_direction,right_rate)
	var b:=_derivative(theta+a[0]*h*.5,omega+a[1]*h*.5,direction+a[2]*h*.5,direction_rate+a[3]*h*.5,right_direction+a[4]*h*.5,right_rate+a[5]*h*.5)
	var c:=_derivative(theta+b[0]*h*.5,omega+b[1]*h*.5,direction+b[2]*h*.5,direction_rate+b[3]*h*.5,right_direction+b[4]*h*.5,right_rate+b[5]*h*.5)
	var d:=_derivative(theta+c[0]*h,omega+c[1]*h,direction+c[2]*h,direction_rate+c[3]*h,right_direction+c[4]*h,right_rate+c[5]*h)
	theta+=(a[0]+2.0*b[0]+2.0*c[0]+d[0])*h/6.0
	omega+=(a[1]+2.0*b[1]+2.0*c[1]+d[1])*h/6.0
	direction+=(a[2]+2.0*b[2]+2.0*c[2]+d[2])*h/6.0
	direction_rate+=(a[3]+2.0*b[3]+2.0*c[3]+d[3])*h/6.0
	right_direction+=(a[4]+2.0*b[4]+2.0*c[4]+d[4])*h/6.0
	right_rate+=(a[5]+2.0*b[5]+2.0*c[5]+d[5])*h/6.0
	direction=direction.normalized();direction_rate-=direction*direction_rate.dot(direction)
	right_direction=right_direction.normalized();right_rate-=right_direction*right_rate.dot(right_direction)
	if brake>.01 and omega*old_omega<=0.0 and absf(last_torque)<brake*8.0:omega=0
	if brake>.01 and absf(omega)<.006 and absf(last_torque)<brake*8.0:omega=0
	var limit:=clampf(theta,-58.0*PI/180.0,-30.0*PI/180.0)
	if limit!=theta:theta=limit;omega=-omega*.05;stop_contacts+=1
	heat+=brake*8.0*absf((omega+old_omega)*.5)*h

func energy()->float:
	var rotation:=Basis(Vector3.UP,yaw)
	var pivot:=rotation*(H+Vector3(left_length*cos(theta+DELTA),left_length*sin(theta+DELTA),counter_depth))
	var jacobian:=rotation*Vector3(-left_length*sin(theta+DELTA),left_length*cos(theta+DELTA),0)
	var bob_velocity:=jacobian*omega+plumb_length*direction_rate
	var bob:=pivot+plumb_length*direction
	var k:=right_kinematics(theta)
	var prism_velocity:Vector3=(rotation*k[1])*omega+prism_length*right_rate
	var prism:Vector3=rotation*k[0]+prism_length*right_direction
	var kinetic:=.5*shaft_inertia*omega*omega+.5*left_mass*bob_velocity.length_squared()+.5*right_mass*prism_velocity.length_squared()
	var potential:float=(gravity/length_scale)*(right_mass*prism.y+left_mass*bob.y)
	potential+=.5*spring*pow(theta-REST-trim*.55,2)-.40*polarity*theta
	return (kinetic+potential)*length_scale*length_scale

func ready_to_transport()->bool:
	return absf(theta-REST)<.025 and absf(omega)<.055 and direction.dot(Vector3.DOWN)>.997 and direction_rate.length()<.10 and right_direction.dot(Vector3.DOWN)>.997 and right_rate.length()<.10

func diagnostics()->Dictionary:
	return {"solver":"closed four-bar + two spherical hangers, coupled RK4 240 Hz","theta":theta,"omega":omega,"direction":str(direction),"right_direction":str(right_direction),"plumb_speed":direction_rate.length(),"prism_speed":right_rate.length(),"energy":energy(),"brake_heat":heat,"torque":last_torque,"constraint_error":maxf(absf(direction.length()-1.0),absf(right_direction.length()-1.0)),"stops":stop_contacts,"gravity":gravity}
