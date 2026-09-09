"""Independent tactile cassette hardware based on the interaction review boards.

Creates only control_library.glb and Control_Library.blend. It never rebuilds or
overwrites HELIOS or any device upper assembly. Coordinates below are Godot Y-up.
"""
import bpy, json, math, pathlib, sys
from mathutils import Vector, Quaternion

ROOT=pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0,str(pathlib.Path(__file__).parent))
from geometry import Builder
b=Builder('CTRL','Tactile control cassette library')
def g(v):return Vector((v[0],-v[2],v[1]))
def cube(name,size,key,parent,pos=(0,0,0),bevel=.004,rotation=None):
    return b.cube(name,(size[0],size[2],size[1]),key,parent,g(pos),bevel,rotation)
def cyl(name,r,depth,key,parent,pos=(0,0,0)):
    return b.cyl(name,r,depth,key,parent,g(pos),(math.pi/2,0,0),64)
def ring(name,r,thickness,key,parent,pos=(0,0,0)):
    return b.torus(name,r,thickness,key,parent,g(pos),(math.pi/2,0,0))
def beam(name,a,c,r,key,parent):return b.beam(name,g(a),g(c),r,key,parent)
def sphere(name,r,key,parent,pos):return b.sphere(name,r,key,parent,g(pos))

types=['rotary','hold','slider_x','slider_y','detent','pump','crank','joystick','gauge','service']
records=[]
for index,kind in enumerate(types):
    root=b.empty('CTRL_'+kind,b.upper)
    socket=b.empty('WidgetSocket',root)
    moving=b.empty('MovingGrip',root)
    if kind in ['rotary','crank','joystick','gauge']:
        cyl('Socket',.092 if kind in ['rotary','gauge'] else .072,.026,'Steel',socket)
        ring('SocketRim',.085 if kind in ['rotary','gauge'] else .065,.008,'Chrome',socket,(0,0,.015))
    else:
        dims=(.248,.075,.030) if kind=='slider_x' else (.095,.218,.030) if kind in ['slider_y','pump'] else (.210,.135,.030)
        cube('SocketPlate',dims,'Steel',socket)
        cube('Inset',tuple(v*.88 if i<2 else .007 for i,v in enumerate(dims)),'Black',socket,(0,0,.019),.008)
        for sign in [-1,1]:cyl('MountFastener',.009,.006,'Chrome',socket,(sign*(dims[0]*.5-.017),0,.018))
    if kind=='rotary':
        cyl('DialCarrier',.080,.036,'Chrome',moving,(0,0,.035))
        cyl('IvoryDial',.066,.019,'Ivory',moving,(0,0,.062))
        ring('DialBezel',.067,.004,'Chrome',moving,(0,0,.072))
        for j in range(32):
            a=j*math.tau/32
            cube('Knurl',(.006,.009,.027),'Steel',moving,(.078*math.cos(a),.078*math.sin(a),.037),.001,Quaternion((0,-1,0),a))
        cube('RedIndex',(.005,.050,.002),'Red',moving,(0,.028,.073),.0008)
    elif kind=='hold':
        for side in [-1,1]:cube('SqueezePad',(.078,.092,.038),'Ivory',moving,(side*.043,0,.045),.016)
        cube('CenterSpine',(.010,.082,.007),'Red',moving,(0,0,.064),.002)
    elif kind in ['slider_x','slider_y','pump']:
        horizontal=kind=='slider_x'
        cube('TravelRail',(.218,.015,.006) if horizontal else (.015,.188,.006),'Chrome',socket,(0,0,.021),.002)
        for j in range(9):
            v=-.080+j*.020
            cube('ScaleTick',(.002,.009,.002) if horizontal else (.009,.002,.002),'Ivory',socket,(v,.026,.021) if horizontal else (.037,v,.021),.0004)
        cube('SlideShoe',(.048,.058,.024) if horizontal else (.057,.043,.024),'Chrome',moving,(0,0,.038),.007)
        cube('RedGrip',(.034,.049,.023) if horizontal else (.049,.032,.023),'Red',moving,(0,0,.057),.007)
        if kind=='pump':
            beam('Piston',(-.026,0,.048),(.026,0,.048),.010,'Chrome',moving)
            sphere('PumpHandle',.026,'Ivory',moving,(0,0,.090))
    elif kind=='detent':
        beam('LeverStem',(0,-.035,.022),(0,.033,.080),.011,'Chrome',moving)
        sphere('LeverGrip',.025,'Red',moving,(0,.039,.087))
        for y in [-.043,0,.043]:cube('DetentMark',(.015,.003,.004),'Ivory',socket,(-.064,y,.024),.0005)
    elif kind=='crank':
        cyl('CrankHub',.046,.036,'Chrome',moving,(0,0,.035))
        cube('CrankArm',(.118,.022,.021),'Chrome',moving,(.042,0,.055),.005)
        cyl('HandleAxle',.016,.063,'Steel',moving,(.100,0,.088))
        cyl('RedHandgrip',.023,.055,'Red',moving,(.100,0,.117))
        ring('HandgripCollar',.024,.003,'Chrome',moving,(.100,0,.140))
    elif kind=='joystick':
        for j in range(5):ring('RubberBoot',.048-j*.005,.006,'Black',socket,(0,0,.024+j*.008))
        beam('GimbalStem',(0,0,.026),(0,0,.123),.011,'Chrome',moving)
        sphere('StickCap',.031,'Ivory',moving,(0,0,.132))
        ring('StickCapBand',.027,.003,'Red',moving,(0,0,.132))
    elif kind=='gauge':
        cyl('GaugeFace',.074,.010,'Ivory',socket,(0,0,.027))
        for j in range(13):
            a=-1+j/6
            beam('GaugeTick',(-math.sin(a)*.057,math.cos(a)*.057,.034),(-math.sin(a)*.066,math.cos(a)*.066,.034),.0012,'Steel',socket)
        beam('GaugeNeedle',(0,-.012,.037),(0,.058,.037),.0024,'Red',moving)
        cyl('GaugePivot',.009,.007,'Chrome',moving,(0,0,.038))
    elif kind=='service':
        cube('ServiceRocker',(.150,.070,.038),'Ivory',moving,(0,0,.040),.012)
        for sign in [-1,1]:
            beam('DirectionalMark',(sign*.045,-.012,.062),(sign*.060,0,.062),.002,'Steel',moving)
            beam('DirectionalMark',(sign*.060,0,.062),(sign*.045,.012,.062),.002,'Steel',moving)
        cube('ServiceDivider',(.003,.052,.004),'Red',moving,(0,0,.062),.0006)
    root.location=g(((index%5)*.34,(index//5)*.34,0))
    records.append({'gesture':kind,'root':root.name,'moving':'MovingGrip','static':'WidgetSocket'})

# Shared materials are embedded. Collection controls remain independent source objects.
for image in bpy.data.images:
    if image.source=='FILE' and image.filepath and not image.packed_file:image.pack()
b.scene.render.engine='CYCLES';b.scene.cycles.samples=32
b.scene.world=bpy.data.worlds.new('Control_Studio');b.scene.world.use_nodes=True
b.scene.world.node_tree.nodes.get('Background').inputs['Strength'].default_value=.35
camera_data=bpy.data.cameras.new('Control_Library_Camera');camera=bpy.data.objects.new(camera_data.name,camera_data);b.scene.collection.objects.link(camera)
camera.location=(.68,-2.1,.30);camera.rotation_euler=(Vector((.68,0,.17))-camera.location).to_track_quat('-Z','Y').to_euler();camera_data.type='ORTHO';camera_data.ortho_scale=1.9;b.scene.camera=camera
for location,energy,size in [((.0,-1,1.5),100,2),((1.8,-.7,.7),80,1)]:
    light_data=bpy.data.lights.new('Softbox','AREA');light_data.energy=energy;light_data.shape='DISK';light_data.size=size
    light=bpy.data.objects.new(light_data.name,light_data);b.scene.collection.objects.link(light);light.location=location;light.rotation_euler=(Vector((.68,0,.17))-light.location).to_track_quat('-Z','Y').to_euler()
b.scene.render.resolution_x=1600;b.scene.render.resolution_y=720;b.scene.render.resolution_percentage=100
bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'blender/collection/Control_Library.blend'))
bpy.ops.object.select_all(action='DESELECT')
for obj in b.col.objects:obj.select_set(True)
bpy.context.view_layer.objects.active=b.root
output=ROOT/'app/assets/collection/control_library.glb'
bpy.ops.export_scene.gltf(filepath=str(output),export_format='GLB',use_selection=True,export_animations=False,export_extras=True,export_apply=True)
(ROOT/'app/assets/collection/control_library.json').write_text(json.dumps({'gestures':records,'source':'blender/collection/Control_Library.blend','shared_base_modified':False},indent=2),encoding='utf-8')
print('CONTROL_LIBRARY_EXPORTED',len(records),output,flush=True)
