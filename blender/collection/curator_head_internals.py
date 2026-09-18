"""Serviceable head cartridges based on the authored cutaway design.

The original iris and face screen remain functional. Added parts occupy real
seats inside the .60 housing; the controller, shell and optics separate at
their connectors during service rather than stretching a cable through air.
"""
import bpy,math
from mathutils import Vector
from geometry import pose

def build(b,face,body,optics,iris,screen_root,profile):
    front=(math.pi/2,0,0)
    b.material('CircuitBoard',(.010,.047,.038),.15,.43)
    b.material('ChipCeramic',(.019,.024,.022),.12,.38)
    b.material('HeatCopper',(.47,.205,.065),.95,.27)
    chassis=b.part('HeadChassis',(0,0,0),.6,face)
    controller=b.part('HeadController',(0,0,0),.65,face)
    heat_module=b.part('HeadHeatSink',(0,0,0),.65,face)
    cartridge=b.part('IrisCartridge',(0,0,0),.4,face)
    display=b.part('DisplayCartridge',(0,0,0),.5,face)
    iris.parent=cartridge;screen_root.parent=display
    for obj in list(optics.children):
        if 'PixelGlass' in obj.name:obj.parent=display
    # Replace the uninterrupted hollow skin with three removable curved
    # sectors; assembled radii and front opening are exactly the same.
    for obj in list(body.children):
        if 'CuratorFormedShell' in obj.name or 'CrownSeam' in obj.name or 'CeramicPanelJoint' in obj.name:
            bpy.data.objects.remove(obj,do_unlink=True)
    sectors=[b.part('HeadShell'+str(i),(0,0,0),.4,face) for i in range(3)]
    n=40;shell_meshes=[]
    for index,parent in enumerate(sectors):
        start=math.radians(-30+index*120)+.003;end=start+math.radians(120)-.006
        vs=[];fs=[];uv=[]
        for k,(y,r) in enumerate(profile):
            for j in range(n+1):
                a=start+(end-start)*j/n;vs.append((r*math.cos(a),y,r*.99*math.sin(a)));uv.append((j/n,k/(len(profile)-1)))
        for k in range(len(profile)-1):
            for j in range(n):
                q=k*(n+1)+j;fs.append((q,q+1,q+n+2,q+n+1))
        shell=b.fast['fast_instance'](b.name('RemovableCeramicSector'),vs,fs,'PlayerPorcelain',parent,(0,0,0),smooth_faces=True,uv=uv)
        shell_meshes.append(shell)
        solid=shell.modifiers.new('Ceramic moulded wall','SOLIDIFY');solid.thickness=.010
        edge=shell.modifiers.new('Glazed edge break','BEVEL');edge.width=.0012;edge.segments=3
        for a in [start+.017,end-.017]:
            seam=[((r-.006)*math.cos(a),y,(r-.006)*.99*math.sin(a)) for y,r in profile[4:-8]]
            b.tube('SectorSealingGasket',seam,.0026,'PlayerRubber',parent,1)
            for k in [10,30]:
                y,r=profile[k];pos=Vector(((r-.013)*math.cos(a),y,(r-.013)*math.sin(a)))
                normal=Vector((math.cos(a),0,math.sin(a)))
                b.cyl('CaptiveShellSeat',.010,.018,'PlayerGold',parent,pos,normal.to_track_quat('Z','Y'),32)
    # Bearing shafts and the neck enter actual machined openings. Hiding a
    # solid shaft inside an uncut porcelain skin was an intersection.
    cutters=[]
    for side in [-1,1]:cutters.append(b.cyl('TemporaryTrunnionCut',.085,.22,'Black',face,(side*.275,.02,0),(0,math.pi/2,0),64))
    cutters.append(b.cyl('TemporaryNeckCut',.074,.22,'Black',face,(0,0,-.27),n=64))
    cutters.append(b.cube('TemporaryNeckServiceSlot',(.148,.35,.22),'Black',face,(0,-.17,-.275),.006))
    cutters.append(b.cyl('TemporaryActuatorCut',.037,.13,'Black',face,(.260,-.058,.037),front,64))
    bpy.context.view_layer.update()
    for shell in shell_meshes:
        bpy.context.view_layer.objects.active=shell
        for modifier in list(shell.modifiers):bpy.ops.object.modifier_apply(modifier=modifier.name)
        for cutter in cutters:
            modifier=shell.modifiers.new('True service bore','BOOLEAN');modifier.operation='DIFFERENCE';modifier.solver='EXACT';modifier.object=cutter
            bpy.ops.object.modifier_apply(modifier=modifier.name)
    for cutter in cutters:bpy.data.objects.remove(cutter,do_unlink=True)
    for obj in list(body.children):
        if any(t in obj.name for t in ['GimbalCheek','GimbalRuby']):obj.parent=chassis
        else:
            p=obj.location;angle=math.degrees(math.atan2(p.z,p.x))
            obj.parent=sectors[int((angle+30)%360//120)]
    # Spherical, machined rib cage with a front cartridge register and rear
    # cap register. Open windows reveal wiring and the controller board.
    for y,r in [(-.115,.252),(.015,.269),(.14,.226)]:
        b.torus('ChassisRegister',r,.009,'PlayerNickel',chassis,(0,y,0),front)
    for i in range(8):
        a=i*math.tau/8;pts=[]
        for j in range(33):
            t=j/32;y=-.12+.30*t;r=.25+.02*math.sin(t*math.pi)-.045*t*t
            pts.append((r*math.cos(a),y,r*math.sin(a)))
        # Flat machined webs have legible edges and seats. A collection of
        # thin round rods looked like an empty wire sphere in service view.
        verts=[];faces=[];radial=Vector((math.cos(a),0,math.sin(a)));across=Vector((-math.sin(a),0,math.cos(a)))
        for j,p in enumerate(pts):
            half=.014+.004*math.cos(j/32*math.tau);p=Vector(p)
            for side,depth in [(-1,-1),(1,-1),(1,1),(-1,1)]:verts.append(p+across*half*side+radial*.005*depth)
        for j in range(32):
            for k in range(4):faces.append((j*4+k,j*4+(k+1)%4,(j+1)*4+(k+1)%4,(j+1)*4+k))
        faces.extend([(3,2,1,0),(128,129,130,131)])
        web=b.fast['fast_instance'](b.name('MachinedSphericalWeb'),verts,faces,'PlayerNickel',chassis,(0,0,0))
        bevel=web.modifiers.new('Machined rib edge radius','BEVEL');bevel.width=.002;bevel.segments=3
        for j in [8,24]:
            p=Vector(pts[j])+radial*.006;b.screw(chassis,p,radial,.004)
        for y,r in [(-.11,.251),(.13,.231)]:
            p=(r*math.cos(a),y,r*math.sin(a));b.screw(chassis,p,(0,-1,0),.0045)
    # Independent trunnions, real rollers, retaining collars and continuous
    # keyed spindle. These remain with the chassis when the skin is removed.
    for side in [-1,1]:
        for x,r,depth in [(side*.222,.075,.016),(side*.255,.071,.018)]:
            part=b.sleeve('TrunnionOuterRace',r,.046,depth,'PlayerNickel',chassis,(x,.02,0),64);part.rotation_euler=(0,math.pi/2,0)
        for j in range(14):
            a=j*math.tau/14;b.sphere('TrunnionRoller',.010,'PlayerGold',chassis,(side*.24,.02+.057*math.cos(a),.057*math.sin(a)))
        b.cyl('KeyedHeadSpindle',.041,.17,'PlayerNickel',chassis,(side*.223,.02,0),(0,math.pi/2,0),48)
        b.cube('SpindleKey',(.050,.014,.010),'PlayerGold',chassis,(side*.208,.053,.028),.0015)
    b.beam('GimbalAxleBridge',(-.16,.02,0),(.16,.02,0),.026,'PlayerNickel',chassis)
    socket=b.sphere('SphericalNeckSocket',.067,'PlayerNickel',chassis,(0,0,-.16))
    cutters=[b.sphere('TemporarySocketBall',.057,'Black',chassis,(0,0,-.16)),b.cyl('TemporarySocketMouth',.062,.10,'Black',chassis,(0,0,-.21),n=64)]
    bpy.context.view_layer.update();bpy.context.view_layer.objects.active=socket
    for cutter in cutters:
        modifier=socket.modifiers.new('Spherical bearing clearance','BOOLEAN');modifier.operation='DIFFERENCE';modifier.solver='EXACT';modifier.object=cutter;bpy.ops.object.modifier_apply(modifier=modifier.name);bpy.data.objects.remove(cutter,do_unlink=True)
    b.torus('NeckBearingGasket',.064,.0025,'PlayerGold',chassis,(0,0,-.164))
    b.beam('NeckToTrunnionBridge',(0,0,-.094),(0,.02,0),.024,'PlayerNickel',chassis)
    # Front cartridge is a genuine eight-leaf iris with an annular actuator.
    for r,inside,y,depth,key in [(.248,.207,.049,.009,'PlayerNickel'),(.237,.214,.037,.010,'PlayerGold')]:
        node=b.sleeve('IrisCartridgeRace',r,inside,depth,key,iris,(0,y,0),112);node.rotation_euler=front
    cam=b.empty('GA_AnnularCam',iris,(0,.044,0))
    ring=b.sleeve('CamGearBlank',.245,.221,.009,'PlayerGold',cam,n=128);ring.rotation_euler=front
    for i in range(96):
        a=i*math.tau/96
        b.cube('CamRingTooth',(.009,.010,.008),'PlayerNickel',cam,(.246*math.cos(a),0,.246*math.sin(a)),.001,(0,-a,0))
    for i in range(8):
        a=i*math.tau/8
        b.cyl('CamFollowerSeat',.007,.013,'PlayerGold',cam,(.229*math.cos(a),-.010,.229*math.sin(a)),front,24)
    motor=b.empty('GA_IrisMotorMount',cartridge,(.260,-.058,.037))
    b.cyl('GearedIrisMotor',.032,.092,'PlayerNickel',motor,rot=front,n=64)
    for y in [-.051,.048]:b.cyl('MotorEndBell',.034,.009,'PlayerGold',motor,(0,y,0),front,48)
    b.cube('MotorMountBracket',(.076,.022,.018),'PlayerGold',cartridge,(.248,-.008,.007),.004)
    pinion=b.empty('GA_IrisPinion',cartridge,(.263,-.154,.037))
    b.cyl('PinionCore',.017,.022,'PlayerGold',pinion,rot=front,n=32)
    for i in range(12):
        a=i*math.tau/12;b.cube('PinionTooth',(.009,.020,.008),'PlayerNickel',pinion,(.019*math.cos(a),0,.019*math.sin(a)),.001,(0,-a,0))
    b.cyl('IrisMotorShaft',.007,.057,'PlayerNickel',cartridge,(.263,-.117,.037),front,32)
    followers=[]
    for i in range(8):
        a=i*math.tau/8;leaf=bpy.data.objects['GA_Shutter_%02d'%i]
        # Rigid lever endpoint belongs to its blade; the cam end travels in
        # the drive-ring slot. Link transforms are solved from these anchors.
        pin=b.empty('GA_LeafDrivePin_'+str(i),leaf,(.023*math.cos(a+math.pi/2),.037,.023*math.sin(a+math.pi/2)))
        b.cyl('LeafActuatorPin',.004,.017,'PlayerNickel',pin,rot=front,n=24)
        anchor=b.empty('GA_CamAnchor_'+str(i),cam,(.229*math.cos(a+.10),-.004,.229*math.sin(a+.10)))
        link=b.empty('GA_IrisLink_'+str(i),iris)
        b.cyl('DriveLinkBody',.003,1.,'PlayerGold',link,(0,0,.5),n=20)
        bpy.context.view_layer.update();start=iris.matrix_world.inverted()@pin.matrix_world.translation;end=iris.matrix_world.inverted()@anchor.matrix_world.translation
        direction=end-start;link.location=start;link.rotation_mode='QUATERNION';link.rotation_quaternion=direction.to_track_quat('Z','Y');link.scale=(1,1,direction.length)
        followers.append({'link':link.name,'blade_pin':pin.name,'cam_pin':anchor.name})
    # The curved luminous screen has a separate real rear carrier, copper
    # heat plate, screw seats and socket; it is no longer a floating image.
    plate=b.sleeve('DisplayCarrierFrame',.209,.182,.027,'PlayerNickel',display,(0,-.133,0),112);plate.rotation_euler=front
    b.cyl('DisplayCopperBack',.186,.006,'HeatCopper',display,(0,-.116,0),front,96)
    for i in range(24):
        a=i*math.tau/24
        b.cube('DisplayHeatFin',(.041,.016,.003),'HeatCopper',display,(.139*math.cos(a),-.101,.139*math.sin(a)),.001,(0,-a,0))
    for i in range(8):
        a=i*math.tau/8;b.screw(display,(.198*math.cos(a),-.117,.198*math.sin(a)),(0,1,0),.004)
    b.cube('DisplayConnector',(.052,.020,.019),'ChipCeramic',display,(0,-.087,.14),.002)
    # Annular controller board, dense but organized. Actual copper traces,
    # packages, solder pads, connectors and a rear heat spreader are modeled.
    board=b.sleeve('AnnularControllerPCB',.226,.091,.008,'CircuitBoard',controller,(0,.116,0),128);board.rotation_euler=front
    b.cube('ControllerBoardBridge',(.192,.008,.080),'CircuitBoard',controller,(0,.116,.005),.004)
    b.cube('ProcessorSocket',(.083,.010,.078),'PlayerGold',controller,(0,.105,.005),.004)
    b.cube('OpticalCuratorProcessor',(.063,.012,.058),'ChipCeramic',controller,(0,.094,.005),.003)
    for side in [-1,1]:
        for i in range(10):
            x=(i-4.5)*.005
            b.cube('ProcessorPin',(.0025,.003,.009),'PlayerNickel',controller,(x,.100,.005+side*.034),.0005)
        for x in [-.067,.067]:
            b.cyl('BoardCapacitor',.010,.019,'ChipCeramic',controller,(x,.098,side*.033),front,32)
            b.cyl('CapacitorMetalTop',.009,.002,'PlayerNickel',controller,(x,.087,side*.033),front,32)
    for i in range(12):
        a=i*math.tau/12;r=.169
        b.cube('ControllerIC',(.030,.010,.025),'ChipCeramic',controller,(r*math.cos(a),.101,r*math.sin(a)),.002,(0,-a,0))
        for side in [-1,1]:
            for pad in range(4):
                p=Vector((side*.018,.0,(pad-1.5)*.006));co=math.cos(a);si=math.sin(a)
                b.cube('SolderPad',(.007,.003,.003),'PlayerNickel',controller,(r*co+p.x*co-p.z*si,.106,r*si+p.x*si+p.z*co),.0006,(0,-a,0))
        for offset in [0,.012,.024]:
            rr=.195+offset
            pts=[(rr*math.cos(a+t),.110,rr*math.sin(a+t)) for t in [j*.27/16 for j in range(17)]]
            b.tube('CopperSignalTrace',pts,.0008,'HeatCopper',controller,1)
        if i%2==0:
            b.cyl('BoardStandoff',.008,.024,'PlayerGold',controller,(.212*math.cos(a),.13,.212*math.sin(a)),front,24)
            b.screw(controller,(.212*math.cos(a),.098,.212*math.sin(a)),(0,-1,0),.004)
    heat=b.sleeve('RearCopperHeatSpreader',.185,.072,.016,'HeatCopper',heat_module,(0,.151,0),96);heat.rotation_euler=front
    b.cube('ProcessorHeatBridge',(.153,.019,.062),'HeatCopper',heat_module,(0,.148,.005),.006)
    for i in range(28):
        a=i*math.tau/28;b.cube('ControllerCoolingFin',(.065,.032,.003),'HeatCopper',heat_module,(.145*math.cos(a),.171,.145*math.sin(a)),.001,(0,-a,0))
    for i in range(6):
        a=i*math.tau/6;b.screw(heat_module,(.175*math.cos(a),.164,.175*math.sin(a)),(0,1,0),.0045)
    for side in [-1,1]:
        b.cube('ControllerHarnessSocket',(.043,.023,.027),'ChipCeramic',controller,(side*.107,.119,.16),.003)
        for k in range(4):
            b.cyl('SocketContact',.0018,.013,'PlayerGold',controller,(side*.107+(k-1.5)*.007,.102,.16),front,12)
        # Flexible loom remains wholly with the board cartridge. Its plug
        # meets a separate chassis socket when the controller is seated.
        pts=[(side*.107,.12,.17),(side*.152,.08,.172),(side*.17,.025,.156),(side*.19,-.023,.135)]
        b.tube('InsulatedInternalHarness',pts,.009,'PlayerRubber',controller,3)
        for i in range(1,12):
            t=i/12;p=Vector(pts[1]).lerp(Vector(pts[2]),t)
            b.torus('LoomRib',.010,.0012,'Black',controller,p,front)
        b.cube('KeyedHarnessPlug',(.028,.029,.025),'PlayerNickel',controller,pts[-1],.003)
        b.cube('ChassisHarnessSocket',(.030,.018,.027),'ChipCeramic',chassis,(side*.19,-.046,.135),.003)
    return {'cam':cam.name,'cam_home':pose(cam.matrix_basis),'pinion':pinion.name,'pinion_home':pose(pinion.matrix_basis),'followers':followers,'service_parts':[p.name for p in [*sectors,optics,cartridge,display,chassis,controller,heat_module]]}
