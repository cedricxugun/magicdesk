"""Visual rework against the approved book/butterfly art. New sibling source;
the functional archive and previous sources remain untouched."""
import bpy,bmesh,math,json,pathlib,sys
from mathutils import Vector,Matrix,Quaternion
ROOT=pathlib.Path(__file__).resolve().parents[2];sys.path.insert(0,str(pathlib.Path(__file__).parent))
from geometry import Builder,C,pose,window
from optimize_runtime_meshes import optimize
bpy.ops.wm.open_mainfile(filepath=str(ROOT/'blender/collection/G_archive.blend'))
scene=bpy.context.scene;scene.frame_set(1)
data=json.loads((ROOT/'app/assets/collection/models/G_archive.json').read_text(encoding='utf-8'))
b=Builder.__new__(Builder);b.id='G5';b.title='Palimpsest, sculptural book';b.scene=scene;b.col=bpy.data.collections['MODULE_G3'];b.root=bpy.data.objects[data['root']];b.upper=bpy.data.objects[data['upper']]
b.serial=40000;b.parts=[];b.controls=[];b.motions=[];b.sockets={};b.qa_shells=[];b.extra={}
b.mats={m.name.removeprefix('Collection_'):m for m in bpy.data.materials if m.name.startswith('Collection_')}
ns={'bpy':bpy,'math':math,'Vector':Vector,'Matrix':Matrix,'Quaternion':Quaternion,'COL':b.col,'M':b.mats}
exec(compile((ROOT/'blender/fast_geometry.py').read_text(),str(ROOT/'blender/fast_geometry.py'),'exec'),ns);b.fast=ns
for obj in b.col.all_objects:obj.animation_data_clear()
front=(math.pi/2,0,0)
def remove_tree(obj):
    if obj:
        for child in list(obj.children_recursive)+[obj]:bpy.data.objects.remove(child,do_unlink=True)

# Remove the literal cupboard enclosure and flat bridging strips. The book is
# formed by its layered folios, rounded covers and articulated cylindrical spine.
removed=set()
for name in ['G4_P_BackCase','G4_P_CaseSide-1','G4_P_CaseSide1']:
    obj=bpy.data.objects.get(name)
    if obj:removed.update(o.name for o in [obj]+list(obj.children_recursive));remove_tree(obj)
for name in [o.name for o in b.col.all_objects]:
    obj=bpy.data.objects.get(name)
    if obj and (any(k in name for k in ['SpineClosureLeaf','SpineClosureRim']) or name in ['G4_Lock-1','G4_Lock1']):remove_tree(obj)
data['parts']=[p for p in data['parts'] if p['name'] not in removed]
data['controls']=[c for c in data['controls'] if c['name'] not in removed]
data['g_archive']['case_nodes']=[];data['g_archive']['locks']=[]

def round_rect(width,height,radius,n=16):
    pts=[]
    for cx,cz,start in [(width/2-radius,height/2-radius,0),(-width/2+radius,height/2-radius,90),(-width/2+radius,-height/2+radius,180),(width/2-radius,-height/2+radius,270)]:
        for i in range(n):
            a=math.radians(start+i*90/n);pts.append((cx+radius*math.cos(a),cz+radius*math.sin(a)))
    return pts
def formed_panel(old,width,height,depth,radius):
    parent=old.parent;name=old.name;loc=old.location.copy()
    remove_tree(old)
    profiles=[(.035,-depth/2),(.015,-depth/2+.007),(0,-depth/2+.026),(0,depth/2-.026),(.015,depth/2-.007),(.035,depth/2)]
    verts=[];faces=[];uv=[]
    for inset,y in profiles:
        for x,z in round_rect(width-inset*2,height-inset*2,max(.02,radius-inset)):
            verts.append((x,y,z));uv.append((x/width+.5,z/height+.5))
    n=len(verts)//len(profiles)
    for band in range(len(profiles)-1):
        for i in range(n):faces.append((band*n+i,band*n+(i+1)%n,(band+1)*n+(i+1)%n,(band+1)*n+i))
    faces.extend([tuple(range(n-1,-1,-1)),tuple((len(profiles)-1)*n+i for i in range(n))])
    obj=b.fast['fast_instance'](name,verts,faces,'Porcelain',parent,loc,smooth_faces=[True]*((len(profiles)-1)*n)+[False,False],uv=uv)
    hole=b.cyl('PanelReceiverBore',.126,depth+.18,'Black',parent,(.47,0,-.09),front,96)
    bpy.context.view_layer.update();bpy.context.view_layer.objects.active=obj
    modifier=obj.modifiers.new('Sealed receiver seat','BOOLEAN');modifier.operation='DIFFERENCE';modifier.object=hole;modifier.solver='EXACT';bpy.ops.object.modifier_apply(modifier=modifier.name);bpy.data.objects.remove(hole,do_unlink=True)
    rim=obj.modifiers.new('Glazed seat rim','BEVEL');rim.width=.002;rim.segments=3
    return obj

for obj in list(b.col.all_objects):
    if obj.type=='MESH' and 'CoverPorcelain' in obj.name:formed_panel(obj,.96,1.90,.096,.108)
    elif obj.type=='MESH' and 'GlazedLamina' in obj.name:formed_panel(obj,.80,1.50,.071,.083)
for control in data['controls']:
    if control['name'] in ['G3_C_Cover-1','G3_C_Cover1']:
        side=-1 if 'Cover-1' in control['name'] else 1
        for i,sample in enumerate(control['samples']):sample['p'][1]+=.070;sample['p'][0]+=side*.24*window(i/100,.08,.32)
for side in [-1,1]:
    face=bpy.data.objects['G3_CoverFace'+str(side)]
    for obj in face.children:
        if obj.type=='FONT':obj.location.y-=side*.021
        elif any(k in obj.name for k in ['CoverEtchedScale','CoverOpticalTick','InsetCeramicRim']):
            y=obj.location.y
            if obj.type=='CURVE' and obj.data.splines:y+=obj.data.splines[0].points[0].co.y
            obj.location.y+=math.copysign(.015,y if abs(y)>.001 else -side)
for leaf in data['g_mechanism']['leaves']:
    for obj in bpy.data.objects[leaf['face']].children:
        if any(k in obj.name for k in ['EngravedOpticalScale','Graduation']):
            y=obj.location.y
            if obj.type=='CURVE' and obj.data.splines:y+=obj.data.splines[0].points[0].co.y
            obj.location.y+=math.copysign(.012,y if abs(y)>.001 else -leaf['side'])

spine=bpy.data.objects['G3_P_Spine']
for z in [.99,2.74]:
    b.sleeve('SpineEndHousing',.23,.11,.092,'ArchiveGold',spine,(0,0,z))
    b.torus('SpineEndDarkGroove',.232,.004,'Black',spine,(0,0,z+.018))
    for k in range(16):
        a=k*math.tau/16;b.cube('HousingRadialSlot',(.015,.005,.036),'Black',spine,(.231*math.cos(a),.231*math.sin(a),z),.002,(0,0,a))
for side in [-1,1]:
    def shutter_pose(o,t,s=side):o.rotation_euler.z=s*math.pi/2*window(t,.035,.20)
    shutter=b.control('SpineShutter'+str(side),spine,shutter_pose)
    start=190 if side<0 else 270
    profiles=[(1.025,.207),(1.06,.221),(1.10,.221),(1.15,.208),(1.62,.208),(1.67,.219),(1.72,.219),(1.77,.208),(2.34,.208),(2.39,.222),(2.44,.222),(2.50,.207),(2.68,.207)]
    verts=[];faces=[];steps=28
    for inner in [False,True]:
        for z,r in profiles:
            for i in range(steps+1):
                a=math.radians(start+i*80/steps);radius=r-(.018 if inner else 0);verts.append((radius*math.cos(a),radius*math.sin(a),z))
    band=(steps+1)*len(profiles)
    for shell in range(2):
        for j in range(len(profiles)-1):
            for i in range(steps):
                k=shell*band+j*(steps+1)+i;f=(k,k+1,k+steps+2,k+steps+1);faces.append(tuple(reversed(f)) if shell else f)
    edge=list(range(steps+1))+[j*(steps+1)+steps for j in range(1,len(profiles))]+list(range(band-2,band-steps-2,-1))+[j*(steps+1) for j in range(len(profiles)-2,0,-1)]
    for a,c in zip(edge,edge[1:]+edge[:1]):faces.append((a,c,c+band,a+band))
    b.fast['fast_instance'](b.name('RolledSpineGuard'),verts,faces,'Satin',shutter,(0,0,0),smooth_faces=True)
    for z in [1.08,1.69,2.42,2.64]:
        b.tube('GuardGoldBinding',[(.224*math.cos(math.radians(start+a*80/40)),.224*math.sin(math.radians(start+a*80/40)),z) for a in range(41)],.0065,'ArchiveGold',shutter)
    for a in [start+4,start+76]:
        angle=math.radians(a);b.beam('GuardRolledEdge',(.211*math.cos(angle),.211*math.sin(angle),1.09),(.211*math.cos(angle),.211*math.sin(angle),2.65),.006,'ArchiveGold',shutter)
    for z in [1.23,1.43,1.91,2.13,2.55]:
        a=math.radians(start+40);normal=(math.cos(a),math.sin(a),0);b.screw(shutter,(.212*normal[0],.212*normal[1],z),normal,.009)

# A sculpted cap, indexing apertures and fine copper tubes replace a bare pole.
b.cyl('IndexHeadExtension',.107,.27,'Satin',spine,(0,0,2.805))
for z in [2.78,2.89,2.952]:b.torus('IndexHeadGoldRing',.145,.012,'ArchiveGold',spine,(0,0,z))
b.cyl('IndexHeadCap',.146,.041,'Black',spine,(0,0,2.955))
for k in range(12):
    a=k*math.tau/12;x=.117*math.cos(a);y=.117*math.sin(a)
    b.beam('IndexHeadKnurl',(x,y,2.79),(x,y,2.90),.006,'ArchiveGold',spine)
for side in [-1,1]:
    b.tube('ReaderCopperFeed',[(side*.10,-.13,1.11),(side*.13,-.12,1.24),(side*.13,-.12,2.41),(side*.09,-.12,2.59)],.009,'Copper',spine)

# Four separately hinged wing lobes. Each is a domed enamel plate with a solid
# gold rim, curved venation and inset ruby corner, not a single flat silhouette.
old=bpy.data.objects[data['g_archive']['contents'][1]['root']];parent=old.parent;root_name=old.name;remove_tree(old)
root=b.empty(root_name,parent);butterfly=data['g_archive']['contents'][1];butterfly['rig']=[]
def register(obj,kind,**extra):butterfly['rig'].append({'name':obj.name,'kind':kind,'home':pose(obj.matrix_basis),**extra})
def curve_outline(control,subdiv=8):
    control=[Vector(p) for p in control];out=[]
    for k in range(len(control)):
        p0,p1,p2,p3=[control[j%len(control)] for j in [k-1,k,k+1,k+2]]
        for j in range(subdiv):
            t=j/subdiv;out.append(.5*(2*p1+(-p0+p2)*t+(2*p0-5*p1+4*p2-p3)*t*t+(-p0+3*p1-3*p2+p3)*t*t*t))
    return out
def wing(side,upper):
    z=.535 if upper else .445;node=b.empty('G5_Wing%s%d'%('Upper' if upper else 'Lower',side),root,(side*.036,0,z))
    control=[(0,.025),(.045,.21),(.17,.42),(.37,.49),(.47,.43),(.43,.21),(.28,.065),(.055,-.008)] if upper else [(0,0),(.10,.025),(.28,-.035),(.34,-.16),(.28,-.27),(.145,-.275),(.045,-.16)]
    outline=curve_outline(control);center=sum(outline,Vector((0,0)))/len(outline);n=len(outline);rings=12;verts=[];uv=[];faces=[]
    def surface(p,t,back=False):return (side*p.x,(-.015 if not back else .006)-(.032 if upper else .026)*math.sin(math.pi*t)*(.3+.7*p.x/max(.01,center.x)),p.y)
    for back in [False,True]:
        for j in range(rings+1):
            t=max(.0001,j/rings)
            for k,p in enumerate(outline):
                pos=center.lerp(p,t);verts.append(surface(pos,t,back));uv.append((k/n,t))
    count=(rings+1)*n
    for shell in range(2):
        for j in range(rings):
            for k in range(n):
                a=shell*count+j*n+k;f=(a,shell*count+j*n+(k+1)%n,shell*count+(j+1)*n+(k+1)%n,a+n);faces.append(tuple(reversed(f)) if shell else f)
    for k in range(n):faces.append((rings*n+k,rings*n+(k+1)%n,count+rings*n+(k+1)%n,count+rings*n+k))
    b.fast['fast_instance'](b.name('DomedWingEnamel'),verts,faces,'Porcelain',node,(0,0,0),smooth_faces=True,uv=uv)
    b.tube('WingRolledGoldRim',[(side*p.x,-.019,p.y) for p in outline+[outline[0]]],.0095,'ArchiveGold',node)
    # Large curved branches with a finer repeating edge stitch.
    root_point=Vector((.012,.006))
    for tip in [control[k] for k in ([2,3,4,5,6] if upper else [1,2,3,4,5])]:
        end=Vector(tip);middle=(end+root_point)*.5+Vector((-.026,.016));path=[]
        for j in range(25):
            t=j/24;p=(1-t)**2*root_point+2*(1-t)*t*middle+t*t*end
            path.append((side*p.x,-.027-.028*math.sin(math.pi*t),p.y))
        b.tube('CurvedWingSpar',path,.0048,'ArchiveGold',node)
    for k in range(0,n,5):
        p=outline[k];b.sphere('WingRimRivet',.0038,'Nickel',node,(side*p.x,-.030,p.y))
    tip_index=3 if upper else 4;tip=Vector(control[tip_index])
    patch=[Vector(control[tip_index-1]).lerp(tip,.50),Vector(control[(tip_index+1)%len(control)]).lerp(tip,.45),tip.lerp(center,.46)]
    def cross(a,c):return a.x*c.y-a.y*c.x
    def patch_surface(p):
        direction=p-center;distance=100.0
        for a,c in zip(outline,outline[1:]+outline[:1]):
            edge=c-a;den=cross(direction,edge)
            if abs(den)<1e-9:continue
            t=cross(a-center,edge)/den;u=cross(a-center,direction)/den
            if t>0 and 0<=u<=1:distance=min(distance,t)
        t=min(1,1/max(.001,distance));x,y,z=surface(p,t,False);return (x,y-.003,z)
    pv=[];pf=[];count=10;rows=[]
    for a in range(count+1):
        row=[]
        for c in range(count+1-a):
            p=patch[0]*(1-(a+c)/count)+patch[1]*(a/count)+patch[2]*(c/count);row.append(len(pv));pv.append(patch_surface(p))
        rows.append(row)
    for a in range(count):
        for c in range(len(rows[a+1])):
            pf.append((rows[a][c],rows[a+1][c],rows[a][c+1]))
            if c+1<len(rows[a+1]):pf.append((rows[a][c+1],rows[a+1][c],rows[a+1][c+1]))
    patch_obj=b.fast['fast_instance'](b.name('BurgundyEnamelInset'),pv,pf,'Red',node,(0,0,0),smooth_faces=True)
    shell=patch_obj.modifiers.new('Enamel inlay thickness','SOLIDIFY');shell.thickness=.002
    border=[]
    for a,c in zip(patch,patch[1:]+patch[:1]):
        for j in range(12):border.append(patch_surface(a.lerp(c,j/12)))
    b.tube('WingInlayGoldSeat',border+[border[0]],.0035,'ArchiveGold',node)
    b.joint(node,(0,0,0),.035,(0,0,1));b.torus('HingeGoldCollar',.031,.005,'ArchiveGold',node,(0,0,.012))
    register(node,'wing',side=side,phase=0.0 if upper else .38,upper=upper)
for side in [-1,1]:wing(side,True);wing(side,False)

for i,(z,r) in enumerate([(.30,.018),(.345,.026),(.388,.035),(.435,.042),(.485,.044),(.535,.041),(.58,.035)]):
    b.sphere('SculptedAbdomen',r,'Nickel' if i%2 else 'Satin',root,(0,0,z),(.82,.85,1.2));b.torus('AbdomenGoldJoint',r*.88,.0048,'ArchiveGold',root,(0,0,z+.013))
    if i in [2,4,5]:b.sphere('VentralEnamel',r*.68,'Porcelain',root,(0,-r*.80,z),(.65,.18,1.0))
b.sphere('GarnetHead',.042,'Red',root,(0,0,.637),(.8,.72,1.12));b.torus('GarnetSetting',.035,.004,'ArchiveGold',root,(0,-.010,.637),front)
for side in [-1,1]:
    a=Vector((side*.015,0,.68));c=Vector((side*.018,0,.84));end=Vector((side*.105,0,.79))
    b.tube('CurvedAntenna',[tuple((1-t)**2*a+2*(1-t)*t*c+t*t*end) for t in [j/32 for j in range(33)]],.0045,'ArchiveGold',root)
    b.sphere('AntennaPearl',.010,'Porcelain',root,(side*.105,0,.79))
    a=Vector((side*.035,0,.075));c=Vector((side*.075,0,.19));d=Vector((-side*.025,0,.24));end=Vector((0,0,.30))
    b.tube('PerchClevis',[tuple((1-t)**3*a+3*(1-t)**2*t*c+3*(1-t)*t*t*d+t**3*end) for t in [j/40 for j in range(41)]],.012,'ArchiveGold',root)
    b.tube('ButterflyLeg',[(side*.02,-.018,.43),(side*.07,-.07,.31),(side*.10,-.07,.255)],.006,'Satin',root)
b.sleeve('PerchMovementRim',.128,.094,.035,'ArchiveGold',root,(0,0,.048))
b.cyl('PerchMovementWell',.094,.012,'Black',root,(0,0,.04))
for i in range(8):
    a=i*math.tau/8;b.beam('PerchRadialSpoke',(.025*math.cos(a),.025*math.sin(a),.067),(.113*math.cos(a),.113*math.sin(a),.067),.006,'ArchiveGold',root)
b.cyl('PerchAxle',.030,.085,'Nickel',root,(0,0,.085))

for obj,fn in b.controls:
    samples=[]
    for i in range(101):fn(obj,i/100);samples.append(pose(obj.matrix_basis))
    fn(obj,0);data['controls'].append({'name':obj.name,'samples':samples})
data['part_count']=len(data['parts']);data['source_blend']='blender/collection/G_archive_refined.blend';data['g_archive']['visual_revision']='reference geometry rework 1: formed folios, articulated spine, four-wing butterfly';data['g_archive']['leaf_half_height']=.75;data['g_archive']['indexed_presentation']=True
for item in data['controls']:
    obj=bpy.data.objects.get(item['name']);p=item['samples'][0]
    if obj:obj.matrix_basis=C.inverted()@Matrix.LocRotScale(Vector(p['p']),Quaternion((p['q'][3],*p['q'][:3])),Vector(p['s']))@C
seen=set()
for obj in b.col.all_objects:
    if obj.type=='MESH' and obj.data.as_pointer() not in seen:
        seen.add(obj.data.as_pointer());bm=bmesh.new();bm.from_mesh(obj.data);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(obj.data);bm.free()
scene.timeline_markers.clear();scene.timeline_markers.new('Visual rework; awaiting current runtime bake',frame=1)
out=ROOT/'app/assets/collection/models/G_archive_refined.glb';out.with_suffix('.json').write_text(json.dumps(data,separators=(',',':')),encoding='utf-8')
bpy.ops.object.select_all(action='DESELECT')
for obj in b.col.all_objects:obj.select_set(True)
bpy.context.view_layer.objects.active=b.root
bpy.ops.export_scene.gltf(filepath=str(out),export_format='GLB',use_selection=True,export_apply=True,export_animations=False,export_extras=True)
for item in data['g_archive']['contents']:bpy.data.objects[item['root']].hide_render=True
bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/data['source_blend']));optimize(out)
print('G_REFERENCE_GEOMETRY_REWORK',data['part_count'],'parts',len(butterfly['rig']),'butterfly hinges',flush=True)
