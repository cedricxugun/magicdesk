"""F gear tooth geometry. Fixed existing axes, independent of G2's dimensions."""
import math
CENTERS=((-0.12999999523162842,2.609999895095825),(-0.3109999895095825,2.4800000190734863))
TEETH=(36,22)
DISTANCE=math.dist(*CENTERS)
MODULE=2*DISTANCE/sum(TEETH)
ANGLE=math.atan2(CENTERS[1][1]-CENTERS[0][1],CENTERS[1][0]-CENTERS[0][0])
PHASE=(ANGLE,ANGLE+math.pi+math.pi/22)
BACKLASH=.00024
DISASSEMBLY_ROUTE=[{'at': 0, 'offset': [-0.0, 0.0, 0.0]}, {'at': 0.105, 'offset': [-0.0, 0.0, 0.0]}, {'at': 0.25, 'offset': [-0.015452369863364398, 0.02458331540627197, 0.0559047397267288]}, {'at': 0.55, 'offset': [-0.10907822128911968, 0.17353353185410508, 0.22615644257823936]}, {'at': 1, 'offset': [-0.2199999988079071, 0.3499999940395355, 0.4399999976158142]}]
def disassembly_offset(amount):
    for first,last in zip(DISASSEMBLY_ROUTE,DISASSEMBLY_ROUTE[1:]):
        if amount<=last['at']:
            t=max(0.,min(1.,(amount-first['at'])/(last['at']-first['at'])));t=t*t*(3.-2.*t)
            return [a+(b-a)*t for a,b in zip(first['offset'],last['offset'])]
    return DISASSEMBLY_ROUTE[-1]['offset']

def outline(teeth,phase=0.):
    pressure=math.radians(20);rp=MODULE*teeth/2;rb=rp*math.cos(pressure)
    ra=rp+MODULE;rf=rp-1.25*MODULE
    def half(r):
        a=math.acos(min(1.,rb/r))
        return math.pi/(2*teeth)+math.tan(pressure)-pressure-(math.tan(a)-a)-BACKLASH/(2*rp)
    points=[]
    def append(r,a):points.append((r*math.cos(a+phase),r*math.sin(a+phase)))
    for tooth in range(teeth):
        a=math.tau*tooth/teeth;start=half(max(rb,rf))
        append(rf,a-start-.025)
        for j in range(13):
            r=max(rf,rb)+(ra-max(rf,rb))*j/12;append(r,a-half(r))
        for j in range(1,5):append(ra,a-half(ra)+2*half(ra)*j/4)
        for j in range(11,-1,-1):
            r=max(rf,rb)+(ra-max(rf,rb))*j/12;append(r,a+half(r))
        append(rf,a+start+.025)
        for j in range(1,4):append(rf,a+start+.025+(math.tau/teeth-2*(start+.025))*j/4)
    return points
