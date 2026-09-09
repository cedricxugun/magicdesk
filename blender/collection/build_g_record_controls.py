"""Authored, engraved hardware for the record player's shared console.

Independent asset: never changes the shared base, generic controls or upper
machine. All API coordinates below are Godot Y-up, front face points +Z.
"""
import bpy, math, pathlib, sys
from mathutils import Vector, Quaternion
ROOT=pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0,str(pathlib.Path(__file__).parent))
from geometry import Builder
from optimize_runtime_meshes import optimize
b=Builder('GCTRL','Sixfold physical console')
b.material('ConsoleCeramic',(.86,.81,.70),0,.18,coat=.55)
b.material('ConsoleGold',(.82,.55,.20),.98,.22)
b.material('ConsoleNickel',(.40,.44,.46),.97,.25)
b.material('ConsoleRubber',(.012,.015,.014),.02,.6)
b.material('ConsoleInk',(.11,.014,.009),.20,.25)
b.material('ConsoleRuby',(.36,.012,.006),.26,.16,coat=.60)
b.material('ConsoleLamp',(1,.25,.055),.1,.20,emission=1.3)
font_path=pathlib.Path('C:/Windows/Fonts/msyhbd.ttc')
font=bpy.data.fonts.load(str(font_path)) if font_path.exists() else None
def g(v):return Vector((v[0],-v[2],v[1]))
def cube(name,size,key,parent,pos=(0,0,0),bevel=.004):return b.cube(name,(size[0],size[2],size[1]),key,parent,g(pos),bevel)
def cyl(name,r,depth,key,parent,pos=(0,0,0)):return b.cyl(name,r,depth,key,parent,g(pos),(math.pi/2,0,0),64)
def ring(name,r,t,key,parent,pos=(0,0,0)):return b.torus(name,r,t,key,parent,g(pos),(math.pi/2,0,0))
def beam(name,a,c,r,key,parent):return b.beam(name,g(a),g(c),r,key,parent)
def text(name,body,size,parent,pos=(0,0,0),key='ConsoleInk'):
    data=bpy.data.curves.new(name,'FONT');data.body=body;data.size=size;data.align_x='CENTER';data.align_y='CENTER';data.extrude=.00035;data.resolution_u=5
    if font:data.font=font
    obj=bpy.data.objects.new(name,data);b.col.objects.link(obj);obj.parent=parent;obj.location=g(pos);obj.rotation_euler=(math.pi/2,0,0);data.materials.append(b.mats[key]);return obj
def triangle(parent,x,y,z,side=1,size=.017):
    pts=[(x-size*.6*side,y-size,z),(x-size*.6*side,y+size,z),(x+size*side,y,z)]
    return b.fast['fast_instance'](b.name('InlayArrow'),[g(v) for v in pts],[(0,1,2)],'ConsoleInk',parent,(0,0,0))
def engraved_title(socket,word,y=.115):
    cube('EnamelLegend',(.205,.038,.008),'ConsoleCeramic',socket,(0,y,.024),.008)
    text('Legend_'+word,word,.024,socket,(0,y,.029))
def lamp(socket,name,x,y,r=.008):
    ring('LampBezel',r+.002,.002,'ConsoleGold',socket,(x,y,.031))
    root=b.empty(name,socket);cyl('LampLens',r,.004,'ConsoleLamp',root,(x,y,.033))
def socket_base(root,width=.230,height=.174):
    socket=b.empty('WidgetSocket',root);moving=b.empty('MovingGrip',root)
    cube('SocketGasket',(width+.005,height+.005,.012),'ConsoleRubber',socket,(0,0,-.005),.023)
    cube('CastGoldFrame',(width,height,.026),'ConsoleGold',socket,(0,0,.009),.024)
    cube('EnamelFace',(width-.012,height-.012,.010),'ConsoleCeramic',socket,(0,0,.026),.020)
    for sign in [-1,1]:
        cyl('ServiceScrew',.008,.004,'ConsoleNickel',socket,(sign*(width*.5-.015),0,.033))
        cube('ScrewSlot',(.007,.0015,.001),'ConsoleInk',socket,(sign*(width*.5-.015),0,.0355),.0003)
    return socket,moving
roots=[]
for index,kind in enumerate(['rotary','slider_x','hold','detent','service']):
    root=b.empty('GCTRL_'+kind,b.upper);roots.append(root)
    if kind=='rotary':
        socket=b.empty('WidgetSocket',root);moving=b.empty('MovingGrip',root)
        cyl('DialGasket',.108,.015,'ConsoleRubber',socket)
        cyl('DialHousing',.104,.028,'ConsoleGold',socket,(0,0,.012))
        ring('DialFrame',.100,.005,'ConsoleNickel',socket,(0,0,.030))
        cyl('NumberWheel',.092,.026,'ConsoleCeramic',moving,(0,0,.043))
        ring('GoldDialBorder',.091,.004,'ConsoleGold',moving,(0,0,.058))
        for j in range(6):
            a=j*math.tau/6
            glyph=text('DiscNumber'+str(j+1),str(j+1),.031,moving,(.070*math.sin(a),.070*math.cos(a),.060))
            glyph.rotation_mode='QUATERNION';glyph.rotation_quaternion=Quaternion((0,-1,0),-a)@Quaternion((1,0,0),math.pi/2)
        for j in range(36):
            a=j*math.tau/36
            cyl('KnurlDot',.0034,.022,'ConsoleGold',moving,(.091*math.sin(a),.091*math.cos(a),.042))
        cube('WingGrip',(.082,.032,.035),'ConsoleGold',moving,(0,0,.076),.012)
        cube('GripEnamel',(.066,.023,.010),'ConsoleRuby',moving,(0,0,.097),.009)
        # Fixed top datum aligns with the chosen rotating number.
        beam('IndexNeedle',(-.010,.112,.061),(0,.099,.063),.0028,'ConsoleRuby',socket)
        beam('IndexNeedle',(0,.099,.063),(.010,.112,.061),.0028,'ConsoleRuby',socket)
        engraved_title(socket,'选 片',-.136)
    else:
        socket,moving=socket_base(root,.25 if kind=='slider_x' else .23)
        if kind=='slider_x':
            engraved_title(socket,'调 节',-.121)
            cube('RecessedSlideSlot',(.152,.041,.009),'ConsoleRubber',socket,(0,0,.034),.014)
            beam('SlideRail',(-.077,0,.041),(.077,0,.041),.004,'ConsoleGold',socket)
            for j in range(7):
                x=(j-3)*.022
                cube('CalibrationTick',(.0018,.013 if j in [0,3,6] else .008,.001),'ConsoleInk',socket,(x,.043,.032),.0003)
            text('Minus','−',.026,socket,(-.077,-.045,.032));text('Plus','+',.026,socket,(.077,-.045,.032))
            cube('SlideShoe',(.045,.058,.022),'ConsoleGold',moving,(0,0,.049),.010)
            cube('SlideGrip',(.032,.048,.026),'ConsoleRuby',moving,(0,0,.068),.011)
            cube('SlideIndex',(.002,.026,.002),'ConsoleCeramic',moving,(0,0,.082),.0004)
        elif kind=='hold':
            engraved_title(socket,'按 住 演 绎',-.121)
            cube('PressureBed',(.169,.105,.008),'ConsoleNickel',socket,(0,0,.036),.021)
            cube('PressurePaddle',(.156,.092,.026),'ConsoleGold',moving,(0,0,.054),.024)
            cube('IvoryPressureFace',(.143,.080,.007),'ConsoleCeramic',moving,(0,0,.071),.022)
            # A mechanical spark / bloom engraving, not a screen icon.
            for j in range(8):
                a=j*math.tau/8
                beam('BloomInlay',(.012*math.sin(a),.012*math.cos(a),.075),(.027*math.sin(a),.027*math.cos(a),.075),.0018,'ConsoleInk',moving)
            cyl('BloomCore',.006,.002,'ConsoleRuby',moving,(0,0,.075))
            for j,(name,word) in enumerate([('Read','读'),('Print','印'),('Play','演')]):
                x=(j-1)*.073;lamp(socket,'ConsoleLamp'+name,x,.105)
                text('LampLegend'+name,word,.017,socket,(x,.079,.033))
        elif kind=='detent':
            engraved_title(socket,'转  /  停',-.121)
            cube('RockerWell',(.110,.125,.010),'ConsoleNickel',socket,(0,0,.038),.022)
            cube('TwoPositionRocker',(.097,.108,.027),'ConsoleGold',moving,(0,0,.056),.019)
            cube('CeramicRocker',(.084,.097,.007),'ConsoleCeramic',moving,(0,0,.073),.017)
            triangle(moving,0,.025,.078,size=.015)
            for x in [-.006,.006]:cube('PauseInlay',(.004,.023,.0015),'ConsoleInk',moving,(x,-.025,.078),.001)
            lamp(socket,'ConsoleLampSpin',.084,.042,.009)
            lamp(socket,'ConsoleLampStop',.084,-.042,.009)
        elif kind=='service':
            engraved_title(socket,'拆  /  装',-.121)
            cube('ServiceBed',(.170,.095,.010),'ConsoleNickel',socket,(0,0,.038),.020)
            cube('ServiceRocker',(.160,.082,.030),'ConsoleGold',moving,(0,0,.058),.020)
            cube('IvoryService',(.146,.070,.007),'ConsoleCeramic',moving,(0,0,.077),.018)
            text('DisassembleLegend','拆',.025,moving,(-.040,0,.082));text('AssembleLegend','装',.025,moving,(.040,0,.082))
            cube('ServiceDivider',(.002,.050,.002),'ConsoleRuby',moving,(0,0,.082),.0004)
    root.location=g((index*.30,0,0))

scene=b.scene;scene.render.engine='CYCLES';scene.cycles.samples=32
scene.world=bpy.data.worlds.new('ConsoleStudio');scene.world.use_nodes=True;scene.world.node_tree.nodes['Background'].inputs['Strength'].default_value=.3
camera_data=bpy.data.cameras.new('PhysicalConsoleCamera');camera=bpy.data.objects.new(camera_data.name,camera_data);scene.collection.objects.link(camera)
camera.location=(.60,-1.7,.42);camera.rotation_euler=(Vector((.60,0,0))-camera.location).to_track_quat('-Z','Y').to_euler();camera_data.type='ORTHO';camera_data.ortho_scale=1.6;scene.camera=camera
for pos,energy,size in [((.0,-1.0,1.0),80,1.2),((1.6,-.5,.8),55,.8)]:
    d=bpy.data.lights.new('Softbox','AREA');d.energy=energy;d.shape='DISK';d.size=size;o=bpy.data.objects.new(d.name,d);scene.collection.objects.link(o);o.location=pos;o.rotation_euler=(Vector((.6,0,0))-o.location).to_track_quat('-Z','Y').to_euler()
scene.render.resolution_x=1600;scene.render.resolution_y=550;scene.render.resolution_percentage=100
bpy.ops.file.pack_all()
bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'blender/collection/G_Record_Controls.blend'))
bpy.ops.object.select_all(action='DESELECT')
for obj in b.col.objects:obj.select_set(True)
bpy.context.view_layer.objects.active=b.root
output=ROOT/'app/assets/collection/record_controls.glb'
bpy.ops.export_scene.gltf(filepath=str(output),export_format='GLB',use_selection=True,export_animations=False,export_extras=True,export_apply=True)
optimize(output)
print('RECORD_PHYSICAL_CONSOLE_EXPORTED',output,flush=True)
