"""Independent observatory geometry. Blender Z-up, front is negative Y.

This component does not load or overwrite the animated optical-curator source.
Ordered fabrication contours are authored alongside the geometry they describe.
"""
import math,bpy,bmesh
from mathutils import Vector,Matrix
from geometry import pose,C
TAU=math.tau

class Observatory:
    def __init__(self,b):
        self.b=b;self.root=b.empty('GA_Observatory',b.upper);self.rig=[];self.guides=[];self.gears=[]
        self.groups={name:b.empty('GO2_'+name,self.root) for name in ['Foundation','Core','Arcade','Dome','Crown']}
        b.material('PlayerPorcelain',(.81,.77,.68),0,.23,coat=.52)
        b.material('PlayerGold',(.72,.47,.18),.96,.245,rough='metal_roughness.png',normal='metal_normal.png')
        b.material('PlayerNickel',(.45,.49,.50),.95,.27,rough='metal_roughness.png',normal='metal_normal.png')
        b.material('ObservatoryCopper',(.35,.14,.048),.94,.29)
        b.material('PlayerRuby',(.27,.008,.012),.20,.14,coat=.68)
        b.material('ObservatoryInk',(.010,.016,.018),.22,.34)
    def dynamic(self,name,parent,loc,kind,phase=0,**data):
        n=self.b.empty('GO2_'+name,parent,loc);n.rotation_euler.y=-phase
        self.rig.append({'name':n.name,'home':pose(n.matrix_basis),'kind':kind,**data});return n
    def sphere(self,name,r,key,parent,loc=(0,0,0),scale=None):
        n,rows=(24,12) if r<=.01 else (40,20) if r<=.027 else (64,32)
        scale=scale or (1,1,1);vs=[];uv=[];fs=[]
        for j in range(rows+1):
            theta=j*math.pi/rows
            for k in range(n+1):
                a=k*TAU/n;vs.append((r*math.sin(theta)*math.cos(a)*scale[0],r*math.sin(theta)*math.sin(a)*scale[1],r*math.cos(theta)*scale[2]));uv.append((k/n,j/rows))
        for j in range(rows):
            for k in range(n):
                q=j*(n+1)+k;fs.append((q,q+1,q+n+2,q+n+1))
        obj=self.mesh(name,vs,fs,key,parent,True,uv=uv);obj.location=loc;return obj
    def screw(self,parent,p,r=.0032,axis=(0,0,1)):
        b=self.b;axis=Vector(axis);q=axis.to_track_quat('Z','Y');depth=r*.65
        b.cyl('MicroFastener',r,depth,'PlayerNickel',parent,p,q,24)
        b.cube('MicroFastenerSlot',(r*1.2,r*.18,depth*.18),'ObservatoryInk',parent,Vector(p)+axis*(depth*.51),depth*.04,q)
    def trim(self,name,points,r=.003,key='PlayerGold',parent=None,guide=True):
        obj=self.b.tube(name,points,r,key,parent or self.root,2)
        if guide:self.guides.append((obj,points))
        return obj
    def ring(self,name,r,thick,key,parent,loc=(0,0,0),rot=None,guide=True):
        obj=self.b.torus(name,r,thick,key,parent,loc,rot)
        if guide:self.guides.append((obj,[(r*math.cos(a),r*math.sin(a),0) for a in [j*TAU/96 for j in range(97)]]))
        return obj
    def mesh(self,name,vertices,faces,key,parent,smooth=False,bevel=0,uv=None):
        obj=self.b.fast['fast_instance'](self.b.name(name),vertices,faces,key,parent,(0,0,0),smooth_faces=smooth,uv=uv)
        bm=bmesh.new();bm.from_mesh(obj.data);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(obj.data);bm.free()
        if bevel:
            m=obj.modifiers.new('Machined edge radius','BEVEL');m.width=bevel;m.segments=3
            m=obj.modifiers.new('Weighted face normals','WEIGHTED_NORMAL');m.keep_sharp=True
        return obj
    def turned(self,name,profile,key,parent,n=64,flutes=0):
        vs=[];uv=[];fs=[]
        for j,(z,r) in enumerate(profile):
            for k in range(n):
                a=k*TAU/n;rr=r*(1-.045*(.5+.5*math.cos(a*flutes))) if flutes else r
                vs.append((rr*math.cos(a),rr*math.sin(a),z));uv.append((k/n,j/(len(profile)-1)))
        for j in range(len(profile)-1):
            for k in range(n):fs.append((j*n+k,j*n+(k+1)%n,(j+1)*n+(k+1)%n,(j+1)*n+k))
        fs.extend([tuple(range(n-1,-1,-1)),tuple((len(profile)-1)*n+k for k in range(n))])
        return self.mesh(name,vs,fs,key,parent,True,uv=uv)
    def wall(self,name,mid,span,r0,r1,bottom,top,parent):
        vs=[];uv=[];fs=[];n=64
        for band in range(4):
            r=r0 if band<2 else r1
            for j in range(n+1):
                u=2*j/n-1;a=mid+span*u/2;z=bottom(u) if band in [0,3] else top(u)
                vs.append((r*math.cos(a),r*math.sin(a),z));uv.append((j/n,z))
        stride=n+1
        for band in range(4):
            for j in range(n):fs.append((band*stride+j,band*stride+j+1,((band+1)%4)*stride+j+1,((band+1)%4)*stride+j))
        fs.extend([(0,stride,2*stride,3*stride),(n,4*stride-1,3*stride-1,2*stride-1)])
        return self.mesh(name,vs,fs,'PlayerPorcelain',parent,True,.0015,uv)
    def foundation(self):
        b=self.b;p=self.groups['Foundation']
        foundation=self.turned('LayeredFoundation',[(0,.288),(.004,.313),(.018,.315),(.032,.305),(.041,.294),(.054,.280),(.060,.274)],'PlayerGold',p,128)
        # The original disc keeps its raised label and spindle. A real
        # underside pocket clears both rather than burying them in a slab.
        cutter=b.cyl('TemporarySpindlePocket',.100,.055,'Black',p,(0,0,-.0015),n=96)
        bpy.context.view_layer.update();bpy.context.view_layer.objects.active=foundation
        modifier=foundation.modifiers.new('Media spindle clearance pocket','BOOLEAN');modifier.operation='DIFFERENCE';modifier.solver='EXACT';modifier.object=cutter;bpy.ops.object.modifier_apply(modifier=modifier.name);bpy.data.objects.remove(cutter,do_unlink=True)
        self.ring('FoundationNickelLip',.310,.0025,'PlayerNickel',p,(0,0,.021))
        self.ring('FoundationInkInlay',.299,.002,'ObservatoryInk',p,(0,0,.039))
        b.sleeve('PierMountingRing',.275,.232,.018,'PlayerPorcelain',p,(0,0,.064),128)
        self.ring('LowerMachinedCornice',.274,.003,'PlayerGold',p,(0,0,.074))
        for i in range(18):
            a=i*TAU/18;self.screw(p,(.302*math.cos(a),.302*math.sin(a),.033),.0032)
        self.staircase(p)
    def staircase(self,parent):
        b=self.b;n=34;start=-math.pi/2;sweep=TAU*.68;step=sweep/(n-1);r0=.270;r1=.337
        for i in range(n):
            a=start+i*step;z=.082+.518*i/(n-1);vs=[];fs=[];segments=6
            for height,r in [(z-.008,r0),(z-.008,r1),(z,r1),(z,r0)]:
                for j in range(segments+1):
                    t=a+(j/segments-.5)*step;vs.append((r*math.cos(t),r*math.sin(t),height))
            stride=segments+1
            for band in range(4):
                for j in range(segments):fs.append((band*stride+j,band*stride+j+1,((band+1)%4)*stride+j+1,((band+1)%4)*stride+j))
            fs.extend([(0,stride,2*stride,3*stride),(segments,4*stride-1,3*stride-1,2*stride-1)])
            self.mesh('ConnectedStairTread',vs,fs,'PlayerPorcelain',parent,False,.001)
            lead=a-step*.5
            self.trim('GildedTreadNosing',[(r*math.cos(lead),r*math.sin(lead),z+.0007) for r in [r0,r1]],.0013,parent=parent,guide=False)
            if i<n-1:
                angle=a+step*.5;rise=.518/(n-1)
                obj=b.cube('StairRiser',(r1-r0,.003,rise+.002),'PlayerPorcelain',parent,((r0+r1)*.5*math.cos(angle),(r0+r1)*.5*math.sin(angle),z+rise*.5-.008),.0007,(0,0,angle))
            if i%2==0 or i==n-1:
                for r in [.273,.333]:
                    x=r*math.cos(a);y=r*math.sin(a)
                    b.cyl('BalusterFoot',.005,.006,'PlayerGold',parent,(x,y,z+.003),n=20)
                    b.beam('StairBaluster',(x,y,z+.004),(x,y,z+.073),.0018,'PlayerGold',parent)
                    self.sphere('BalusterFinial',.0028,'PlayerGold',parent,(x,y,z+.073))
        for r in [.274,.329]:
            self.trim('ContinuousStairStringer',[(r*math.cos(start+sweep*t),r*math.sin(start+sweep*t),.070+.518*t) for t in [j/180 for j in range(181)]],.005,'ObservatoryCopper',parent)
        for r in [.273,.333]:
            self.trim('ContinuousStairHandrail',[(r*math.cos(start+sweep*t),r*math.sin(start+sweep*t),.155+.518*t) for t in [j/180 for j in range(181)]],.0026,'PlayerGold',parent)
        for i in [0,8,16,24,33]:
            a=start+sweep*i/(n-1);z=.07+.518*i/(n-1)
            b.beam('StairRadialSupport',(.237*math.cos(a),.237*math.sin(a),z-.018),(.333*math.cos(a),.333*math.sin(a),z+.004),.004,'PlayerNickel',parent)
    def structure(self):
        b=self.b;p=self.groups['Core']
        for i in range(6):
            a=-2*math.pi/3+i*TAU/6;pole=b.empty('GO2_Pier_'+str(i),p,(.245*math.cos(a),.245*math.sin(a),0));pole.rotation_euler.z=a
            self.turned('SculptedFlutedPier',[(.066,.025),(.080,.028),(.099,.025),(.114,.020),(.145,.018),(.310,.017),(.430,.019),(.490,.022),(.527,.021),(.552,.018),(.595,.019),(.627,.028),(.65,.025),(.673,.024)],'PlayerPorcelain',pole,96,12)
            for z,r,d in [(.087,.028,.012),(.115,.021,.008),(.432,.023,.012),(.490,.024,.010),(.636,.029,.012),(.677,.025,.008)]:
                b.cyl('PierMachinedCollar',r,d,'PlayerGold',pole,(0,0,z),n=64)
            self.trim('PierContourA',[(.020,0,.12),(.018,0,.32),(.022,0,.48),(.019,0,.59),(.024,0,.67)],.0008,'PlayerGold',pole)
            if i in [2,5]:
                self.sphere('PierOvalHousing',.043,'PlayerPorcelain',pole,(.026,0,.338),(1,.70,1.65))
                self.trim('HousingSeam',[(.065,.029*math.cos(t),.338+.065*math.sin(t)) for t in [j*TAU/80 for j in range(81)]],.0023,parent=pole)
                b.cyl('HousingRubySeat',.021,.010,'PlayerGold',pole,(.067,0,.338),(0,math.pi/2,0),48)
                self.sphere('HousingRuby',.016,'PlayerRuby',pole,(.073,0,.338),(.35,1,1))
                for z in [.271,.405]:b.cyl('HousingUnion',.017,.018,'PlayerGold',pole,(.026,0,z),n=40)
            for j in range(4):
                theta=j*TAU/4;self.screw(pole,(.021*math.cos(theta),.021*math.sin(theta),.082),.0028)
        for side in [-1,1]:
            b.beam('ArmillarySupportedShaft',(side*.105,0,.455),(side*.244,0,.455),.007,'PlayerNickel',p)
            b.cyl('ArmillaryOuterBearing',.017,.027,'PlayerGold',p,(side*.145,0,.455),(0,math.pi/2,0),48)
        outer=self.dynamic('MainArmillaryTilt',p,(0,0,.455),'orbit_tilt')
        self.ring('MainOuterGimbal',.112,.0045,'PlayerGold',outer,rot=(math.pi/2,0,0))
        for z in [-.104,.104]:b.cyl('InnerGimbalPolarPin',.007,.018,'PlayerNickel',outer,(0,0,z),n=32)
        inner=self.dynamic('MainArmillarySpin',outer,(0,0,0),'orbit',ratio=.32)
        self.ring('InnerMeridian',.096,.0035,'PlayerNickel',inner,rot=(math.pi/2,0,0))
        self.ring('EclipticBand',.086,.0025,'PlayerGold',inner,rot=(math.pi*.34,0,0))
        self.sphere('GoldenCelestialGlobe',.046,'PlayerGold',inner)
        b.cyl('GlobePolarAxle',.004,.192,'PlayerNickel',inner,n=32)
        for latitude in [-.60,0,.60]:
            self.ring('EngravedLatitude',.0465*math.cos(latitude),.00065,'ObservatoryCopper',inner,(0,0,.0465*math.sin(latitude)),guide=False)
        for i in range(6):
            a=i*math.pi/6;pts=[(.0465*math.sin(t)*math.cos(a),.0465*math.sin(t)*math.sin(a),.0465*math.cos(t)) for t in [j*TAU/96 for j in range(97)]]
            self.trim('EngravedLongitude',pts,.00065,'ObservatoryCopper',inner,False)
        self.clockwork(p)
    def gear(self,name,teeth,loc,ratio,phase,parent):
        b=self.b;m=.004;pitch=m*teeth/2;base=pitch*math.cos(math.radians(20));tip=pitch+m;root=pitch-1.25*m;inside=root*.68
        inv=lambda alpha:math.tan(alpha)-alpha
        half=lambda r:math.pi/(2*teeth)*.94+inv(math.radians(20))-inv(math.acos(min(1,base/r)))
        points=[];angular=TAU/teeth;hb=half(base)
        for tooth in range(teeth):
            center=tooth*angular
            points.append((root,center-angular*.5))
            points.append((root,center-hb))
            for i in range(9):
                r=max(root,base)+(tip-max(root,base))*i/8;points.append((r,center-half(r)))
            ha=half(tip)
            for i in range(1,5):points.append((tip,center-ha+2*ha*i/4))
            for i in range(1,9):
                r=tip-(tip-max(root,base))*i/8;points.append((r,center+half(r)))
            points.append((root,center+hb))
        vs=[];fs=[];uv=[];n=len(points)
        for outer,y in [(True,-.006),(True,.006),(False,.006),(False,-.006)]:
            for radius,a in points:
                r=radius if outer else inside;vs.append((r*math.cos(a),y,r*math.sin(a)));uv.append((a/TAU,y/.012+.5))
        for band in range(4):
            for j in range(n):fs.append((band*n+j,band*n+(j+1)%n,((band+1)%4)*n+(j+1)%n,((band+1)%4)*n+j))
        node=self.dynamic(name,parent,loc,'gear',phase,ratio=ratio)
        wheel=self.mesh('InvoluteGear_'+str(teeth),vs,fs,'PlayerGold',node,False,.00035,uv)
        for i in range(6):
            a=i*TAU/6;b.beam('GearSpoke',(.008*math.cos(a),0,.008*math.sin(a)),(inside*math.cos(a),0,inside*math.sin(a)),.003,'ObservatoryCopper',node)
        b.cyl('GearHub',.010,.021,'PlayerGold',node,rot=(math.pi/2,0,0),n=32)
        b.cyl('GearSpindle',.005,.095,'PlayerNickel',parent,(loc[0],loc[1]+.013,loc[2]),(math.pi/2,0,0),32)
        b.cyl('GearRubyBearing',.010,.007,'PlayerRuby',parent,(loc[0],loc[1]-.021,loc[2]),(math.pi/2,0,0),40)
        self.gears.append({'node':node.name,'wheel':wheel.name,'teeth':teeth,'pitch_radius':pitch,'center':loc,'ratio':ratio,'phase':phase})
        self.guides.append((node,[(pitch*math.cos(a),-.006,pitch*math.sin(a)) for a in [j*TAU/96 for j in range(97)]]))
        return node
    def clockwork(self,parent):
        b=self.b
        for x in [-.082,.062]:
            b.beam('ClockBridgePillar',(x,.096,.055),(x,.096,.355),.008,'PlayerNickel',parent)
            b.cyl('ClockFrameFoot',.016,.016,'PlayerGold',parent,(x,.096,.063),n=32)
        for z in [.210,.298]:
            b.beam('ClockBearingBridge',(-.090,.075,z),(.073,.075,z),.007,'ObservatoryCopper',parent)
        self.gear('ClockMaster',32,(-.066,.04,.210),1.,0,parent)
        self.gear('ClockIntermediate',24,(.046,.04,.210),-32/24,-math.pi/24,parent)
        self.gear('ClockUpper',20,(.046,.04,.298),32/20,0,parent)
        pend=self.dynamic('Pendulum',parent,(-.09,.135,.342),'pendulum',swing_gain=.12)
        b.beam('PendulumStem',(0,0,0),(0,0,-.222),.0025,'PlayerGold',pend)
        self.sphere('PendulumBob',.026,'PlayerGold',pend,(0,0,-.222),(1,.32,1))
        # Readable time setting around the central armillary, with open space.
        dial=b.empty('GO2_TimeDial',parent,(0,-.166,.455))
        self.ring('ArmillaryTimeScale',.137,.0038,'PlayerGold',dial,rot=(math.pi/2,0,0))
        for i in range(60):
            a=i*TAU/60;r=.137
            b.cube('TimeScaleIndex',(.0014,.002,.009 if i%5==0 else .004),'PlayerNickel',dial,(r*math.sin(a),-.002,r*math.cos(a)),.0004,(0,a,0))
        for name,length,radius,dy in [('hour',.040,.109,-.008),('minute',.054,.108,-.012)]:
            node=self.dynamic('Time_'+name,dial,(0,dy,0),name)
            # Outer pointer only; the celestial sphere stays unobscured.
            b.beam('TimePointer',(0,0,radius),(0,0,radius+length*.45),.0017,'PlayerGold',node)
    def arcade(self):
        b=self.b;p=self.groups['Arcade']
        for i in range(6):
            mid=-math.pi/2+i*TAU/6;span=TAU/6*.84
            arch=lambda u:.430+.205*max(0,1-abs(u))**.62
            crest=lambda u:.640+.056*max(0,1-abs(u))**.8
            self.wall('FormedArchSpandrel',mid,span,.263,.245,arch,crest,p)
            pts=[];top=[]
            for j in range(65):
                u=j/32-1;a=mid+span*u/2;pts.append((.265*math.cos(a),.265*math.sin(a),arch(u)));top.append((.264*math.cos(a),.264*math.sin(a),crest(u)))
            self.trim('WindowMachinedReveal',pts,.0035,parent=p)
            self.trim('CurvedUpperCornice',top,.003,parent=p)
            # Tall jambs join the curved arch and the lower apron.
            for side in [-1,1]:
                a=mid+side*span*.5
                self.trim('PorcelainWindowJamb',[(.260*math.cos(a),.260*math.sin(a),z) for z in [.124,.17,.30,.43]],.012,'PlayerPorcelain',p)
                self.trim('WindowJambGoldInlay',[(.272*math.cos(a),.272*math.sin(a),z) for z in [.132,.17,.30,.43]],.0018,'PlayerGold',p,False)
                self.wall('PiercedLowerApron',mid+side*span*.335,span*.32,.262,.246,lambda u:.071,lambda u:.164+.032*(1-abs(u)),p)
            normal=Vector((math.cos(mid),math.sin(mid),0));pos=normal*.273+Vector((0,0,.675))
            b.cyl('ArchKeystoneBezel',.024,.012,'PlayerGold',p,pos,normal.to_track_quat('Z','Y'),48)
            jewel=self.sphere('ArchKeystoneRuby',.017,'PlayerRuby',p,pos+normal*.007);jewel.scale=(1,1,1.05)
            self.portal(p,mid)
    def portal(self,parent,mid):
        b=self.b;half=.163;r=.276;pts=[]
        for z in [.072,.183]:pts.append((r*math.cos(mid-half),r*math.sin(mid-half),z))
        for j in range(41):
            u=j/20-1;a=mid+u*half;z=.183+.075*max(0,1-abs(u))**.65;pts.append((r*math.cos(a),r*math.sin(a),z))
        pts.append((r*math.cos(mid+half),r*math.sin(mid+half),.072))
        self.trim('LowerPointedPortal',pts,.0075,'PlayerPorcelain',parent)
        self.trim('PortalGoldReveal',[(x*1.018,y*1.018,z) for x,y,z in pts],.0020,'PlayerGold',parent)
        self.trim('PortalThreshold',[(.278*math.cos(mid+half*u),.278*math.sin(mid+half*u),.103) for u in [j/16-1 for j in range(33)]],.0020,'PlayerGold',parent)
        for u in [-.60,0,.60]:
            a=mid+u*half;z=.183+.075*(1-abs(u))**.65
            b.beam('PortalGrille',(.278*math.cos(a),.278*math.sin(a),.102),(.278*math.cos(a),.278*math.sin(a),z-.007),.0016,'PlayerGold',parent)
        normal=Vector((math.cos(mid),math.sin(mid),0));self.sphere('PortalRuby',.010,'PlayerRuby',parent,normal*.284+Vector((0,0,.257)))
    def dome(self):
        b=self.b;p=self.groups['Dome']
        radius=lambda t:.074+.181*max(0,math.cos(t*math.pi/2))**.90
        for i in range(12):
            a=-2*math.pi/3+i*TAU/12;pts=[(radius(t)*math.cos(a),radius(t)*math.sin(a),.690+.280*t) for t in [j/64 for j in range(65)]]
            if i%2==0:
                vs=[];fs=[];tangent=Vector((-math.sin(a),math.cos(a),0));radial=Vector((math.cos(a),math.sin(a),0))
                for j,point in enumerate(pts):
                    half=.006+.003*math.sin(j/64*math.pi);point=Vector(point)
                    for side,depth in [(-1,-1),(1,-1),(1,1),(-1,1)]:vs.append(point+tangent*half*side+radial*.004*depth)
                for j in range(64):
                    for k in range(4):fs.append((j*4+k,j*4+(k+1)%4,(j+1)*4+(k+1)%4,(j+1)*4+k))
                fs.extend([(3,2,1,0),(256,257,258,259)]);self.mesh('CurvedPorcelainDomeWeb',vs,fs,'PlayerPorcelain',p,True,.001)
                for side in [-1,1]:self.trim('DomeWebGildedEdge',[tuple(Vector(v)+tangent*.008*side) for v in pts],.0015,'PlayerGold',p)
            else:self.trim('DomeNickelMeridian',pts,.003,'PlayerNickel',p)
        for i in range(6):
            mid=-math.pi/2+i*TAU/6;pts=[]
            for j in range(49):
                u=j/24-1;a=mid+u*math.pi/6;z=.718+.107*max(0,1-u*u)**.70;r=radius((z-.690)/.280)+.002
                pts.append((r*math.cos(a),r*math.sin(a),z))
            self.trim('DomeSecondaryArch',pts,.006,'PlayerPorcelain',p)
            self.trim('DomeSecondaryGoldEdge',[(x*1.012,y*1.012,z) for x,y,z in pts],.002,'PlayerGold',p)
            vs=[];fs=[];uv=[];width=49;rows=5
            for inside in [False,True]:
                for row in range(rows):
                    for j in range(width):
                        u=j/24-1;a=mid+u*math.pi/6;low=.718+.107*max(0,1-u*u)**.70;z=low+(row/(rows-1))*(.013+.023*(1-abs(u)));r=radius((z-.690)/.280)+(-.003 if inside else .004)
                        vs.append((r*math.cos(a),r*math.sin(a),z));uv.append((j/48,row/(rows-1)))
            layer=width*rows
            for side in [0,1]:
                for row in range(rows-1):
                    for j in range(width-1):
                        q=side*layer+row*width+j;face=(q,q+1,q+width+1,q+width);fs.append(face if side==0 else tuple(reversed(face)))
            for j in range(width-1):
                fs.append((j,j+layer,j+layer+1,j+1));q=(rows-1)*width+j;fs.append((q,q+1,q+layer+1,q+layer))
            for j in [0,width-1]:
                for row in range(rows-1):q=row*width+j;fs.append((q,q+width,q+width+layer,q+layer))
            self.mesh('PiercedDomeWindowSpandrel',vs,fs,'PlayerPorcelain',p,True,.0008,uv)
        self.ring('DomeBaseSeat',.255,.004,'PlayerGold',p,(0,0,.690))
        b.sleeve('CrownMount',.082,.064,.026,'PlayerGold',p,(0,0,.974),80)
        self.ring('CrownSeatNickel',.081,.002,'PlayerNickel',p,(0,0,.984))
        # Six finials sit on the structural pier capitals, not in free space.
        for i in range(6):
            a=-2*math.pi/3+i*TAU/6;n=b.empty('GO2_Finial_'+str(i),p,(.245*math.cos(a),.245*math.sin(a),0))
            self.turned('TurnedFinial',[(.682,.014),(.696,.018),(.71,.010),(.835,.005),(.852,.012),(.869,.006),(.895,.003),(.912,0)],'PlayerGold',n,48)
            self.sphere('FinialRuby',.008,'PlayerRuby',n,(0,0,.849))
    def crown(self):
        b=self.b;p=self.groups['Crown'];center=(0,0,1.063)
        orbit=self.dynamic('CrownOrbit',p,center,'orbit',ratio=.23)
        for rot in [(0,0,0),(math.pi/2,0,0),(0,math.pi/2,0)]:self.ring('RubyArmillaryRing',.078,.003,'PlayerGold',orbit,rot=rot)
        self.sphere('CrownRubyGlobe',.032,'PlayerRuby',orbit)
        b.cyl('CrownVerticalSpindle',.003,.153,'PlayerNickel',p,(0,0,1.063),n=24)
        for z in [.985,1.143]:b.cyl('CrownPolarBearing',.009,.012,'PlayerGold',p,(0,0,z),n=32)
        self.turned('CalibratedSpire',[(1.146,.007),(1.156,.009),(1.164,.0035),(1.197,.002),(1.215,0)],'PlayerGold',p,48)
    def build(self):
        self.foundation();self.structure();self.arcade();self.dome();self.crown();bpy.context.view_layer.update()
        edges=[];paths=[];inverse=self.root.matrix_world.inverted()
        for node,points in self.guides:
            matrix=C@inverse@node.matrix_world
            converted=[list((matrix@Vector(p).to_4d()).xyz) for p in points]
            paths.append({'source':node.name,'points':converted})
            edges.extend([[a,b] for a,b in zip(converted,converted[1:]) if (Vector(a)-Vector(b)).length>.00001])
        return {'root':self.root.name,'title':'穹顶观测塔','parameter':'时间偏置','action':'发条共鸣','rig':self.rig,'structure_edges':edges,'build_guides':paths,'base_diameter':.630,'height':1.215,'max_footprint':.70,'gear_train':self.gears,'source_blend':'blender/collection/G_observatory_r2.blend','reference':'production/G_optical_curator/observatory_r2/modeling_reference.png'}
