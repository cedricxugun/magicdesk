"""R3 drive closure in the authored Blender X/Z plane; no Blender dependency."""
import math
A=(-.035,.125)
P=(.010,.150)
ECCENTRIC=.009
CAM_RADIUS=.024
ROLLER_RADIUS=.006
INPUT=.040
OUTPUT=.068
ROD_LENGTH=.035
SLIDER_X=.088
GEAR_MODULE=.003
GEAR_TEETH=(36,18)
GEAR_ANGLE=-math.pi/4
PINION=(A[0]+.081*math.cos(GEAR_ANGLE),A[1]+.081*math.sin(GEAR_ANGLE))

def solve(phase):
    center=(A[0]+ECCENTRIC*math.cos(phase),A[1]+ECCENTRIC*math.sin(phase))
    dx,dz=center[0]-P[0],center[1]-P[1]
    distance=math.hypot(dx,dz)
    arg=(distance*distance+INPUT*INPUT-(CAM_RADIUS+ROLLER_RADIUS)**2)/(2*distance*INPUT)
    if abs(arg)>1:raise ValueError('Cam follower cannot close')
    theta=math.atan2(dz,dx)-math.acos(arg)
    roller=(P[0]+INPUT*math.cos(theta),P[1]+INPUT*math.sin(theta))
    output=(P[0]-OUTPUT*math.cos(theta),P[1]-OUTPUT*math.sin(theta))
    dz2=ROD_LENGTH**2-(SLIDER_X-output[0])**2
    if dz2<=0:raise ValueError('Connecting rod cannot reach guide')
    slider=(SLIDER_X,output[1]+math.sqrt(dz2))
    return dict(cam=center,theta=theta,roller=roller,output=output,slider=slider,
                wave_z=slider[1]+.015,rod_angle=math.atan2(slider[1]-output[1],slider[0]-output[0]))

def gear_outline(teeth,backlash=.00010):
    """20 degree involute flanks, relieved roots and real angular tooth spacing."""
    pressure=math.radians(20);rp=GEAR_MODULE*teeth/2;rb=rp*math.cos(pressure)
    ra=rp+GEAR_MODULE;rf=rp-1.25*GEAR_MODULE
    def half(r):
        a=math.acos(min(1,rb/r))
        return math.pi/(2*teeth)+(math.tan(pressure)-pressure)-(math.tan(a)-a)-backlash/(2*rp)
    points=[]
    for tooth in range(teeth):
        a=math.tau*tooth/teeth;start=half(max(rb,rf))
        points.append((rf*math.cos(a-start-.025),rf*math.sin(a-start-.025)))
        for j in range(11):
            r=max(rf,rb)+(ra-max(rf,rb))*j/10
            points.append((r*math.cos(a-half(r)),r*math.sin(a-half(r))))
        for j in range(1,5):
            t=-half(ra)+2*half(ra)*j/4
            points.append((ra*math.cos(a+t),ra*math.sin(a+t)))
        for j in range(9,-1,-1):
            r=max(rf,rb)+(ra-max(rf,rb))*j/10
            points.append((r*math.cos(a+half(r)),r*math.sin(a+half(r))))
        points.append((rf*math.cos(a+start+.025),rf*math.sin(a+start+.025)))
        next_start=a+math.tau/teeth-start-.025
        for j in range(1,4):
            t=(a+start+.025)+(next_start-a-start-.025)*j/4
            points.append((rf*math.cos(t),rf*math.sin(t)))
    return points

def spring_points(theta,channel):
    """One fixed leg on shaft collar, one moving leg pinned to the rocker."""
    rest=solve(channel*math.tau/3)['theta'];start=rest+math.pi-math.tau*3-math.pi/2;end=theta+math.pi
    points=[]
    for j in range(17):
        a=start+math.pi+j*math.tau/16
        points.append((.018*math.cos(start)+.0025*math.cos(a),-.003,.018*math.sin(start)+.0025*math.sin(a)))
    for j in range(73):
        u=j/72;a=start+(end-start)*u
        points.append((.0105*math.cos(a),.006*u,.0105*math.sin(a)))
    for j in range(17):
        a=end+math.pi+j*math.tau/16
        points.append((.018*math.cos(end)+.0025*math.cos(a),.006,.018*math.sin(end)+.0025*math.sin(a)))
    return points
