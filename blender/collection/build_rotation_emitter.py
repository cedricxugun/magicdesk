"""Shared optical window conforming to the unchanged HELIOS lower ring."""
import bpy,sys,math,json,hashlib
from pathlib import Path
from mathutils import Vector
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(Path(__file__).parent))
from geometry import Builder
b=Builder('HR','Shared hidden optical rotation control')
b.material('OpticalGlass',(.004,.015,.018),.62,.12,coat=.7)
b.material('PortNickel',(.32,.36,.38),.95,.28,normal='metal_normal.png')
b.material('CyanLens',(.11,.50,.62),.15,.20,emission=.7)
root=b.empty('HR_Emitter',b.upper)
# Observed lower-ring ray hit from the real base; Z-up source, Y-up metadata below.
angle=.20;height=.145;radius=1.370

def point(u,v,depth):
    a=angle+u/radius
    return ((radius+depth)*math.cos(a),-(radius+depth)*math.sin(a),height+v)

def outline(hw,hh,r):
    pts=[]
    for q,(x,z) in enumerate([(hw-r,hh-r),(-hw+r,hh-r),(-hw+r,-hh+r),(hw-r,-hh+r)]):
        for j in range(9):
            a=q*math.pi/2+j*math.pi/16;pts.append((x+r*math.cos(a),z+r*math.sin(a)))
    return pts

def shape(name,outer,inner,mat,depth):
    n=len(outer);verts=[point(x,z,depth) for x,z in outer+inner];faces=[]
    for i in range(n):faces.append((i,(i+1)%n,(i+1)%n+n,i+n))
    obj=b.fast['fast_instance'](b.name(name),verts,faces,mat,root,(0,0,0),smooth_faces=True)
    return obj
outer=outline(.076,.009,.004);inner=outline(.069,.0045,.0025)
shape('RecessedWindowBezel',outer,inner,'PortNickel',.0007)
# A manufactured black-glass cover in the ring seam, with a narrow optical line.
verts=[point(0,0,.00085)]+[point(x,z,.00085) for x,z in inner]
faces=[(0,i+1,(i+1)%len(inner)+1) for i in range(len(inner))]
b.fast['fast_instance'](b.name('BlackOpticalWindow'),verts,faces,'OpticalGlass',root,(0,0,0),smooth_faces=True)
slit=outline(.043,.0012,.001)
verts=[point(0,0,.0011)]+[point(x,z,.0011) for x,z in slit]
faces=[(0,i+1,(i+1)%len(slit)+1) for i in range(len(slit))]
b.fast['fast_instance'](b.name('FlushOpticalSlit'),verts,faces,'CyanLens',root,(0,0,0),smooth_faces=True)
out=ROOT/'app/assets/collection/components';out.mkdir(exist_ok=True)
bpy.ops.object.select_all(action='DESELECT')
for obj in [root]+list(root.children_recursive):obj.select_set(True)
bpy.context.view_layer.objects.active=root
bpy.ops.export_scene.gltf(filepath=str(out/'shared_rotation_emitter.glb'),export_format='GLB',use_selection=True,export_apply=True,export_animations=False)
source=ROOT/'blender/collection/shared_rotation_emitter.blend'
bpy.ops.wm.save_as_mainfile(filepath=str(source));bpy.ops.file.make_paths_relative();bpy.ops.wm.save_as_mainfile(filepath=str(source))
(out/'shared_rotation_emitter.json').write_text(json.dumps({'source':str(source.relative_to(ROOT)),'position':[radius*math.cos(angle),height,radius*math.sin(angle)],'normal':[math.cos(angle),0,math.sin(angle)],'reference':'production/shared_rotation/concept_v2.png','base_modified':False,'scope':'Thin conforming optical-window insert; actual base unchanged; integration/occlusion/hit-region validation pending'},indent=2)+'\n')
print('SHARED_EMITTER_SAVED',flush=True)
