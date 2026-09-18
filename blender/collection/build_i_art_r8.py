"""Artwork-led I acoustic core and actual perforated cage liners, forked from R7."""
import bpy,bmesh,sys,math,json,hashlib,shutil
from pathlib import Path
from mathutils import Vector,Matrix,Quaternion
from mathutils.bvhtree import BVHTree
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(Path(__file__).parent))
from geometry import Builder
SOURCE=ROOT/'blender/collection/I_service_r7_motion.blend';TARGET=ROOT/'blender/collection/I_art_r8.blend'
OUT=ROOT/'review/I_refinement/art_r8';OUT.mkdir(parents=True,exist_ok=True)
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
prior=json.loads((ROOT/'review/I_refinement/service_r7/build.json').read_text());assert sha(SOURCE)==prior['source_sha256']
if TARGET.exists():
    old=json.loads((OUT/'build.json').read_text());assert sha(TARGET)==old['source_sha256'],'Unrecorded R8 source edits'
    (TARGET.parent/'checkpoints'/('I-art-'+sha(TARGET)[:12]+'.blend')).write_bytes(TARGET.read_bytes())
bpy.ops.wm.open_mainfile(filepath=str(SOURCE));scene=bpy.context.scene;scene.frame_set(1)
root=bpy.data.objects['IH1_MODULE'];fixed=bpy.data.objects['IH1_FixedChamber'];mouth=bpy.data.objects['IH1_Mouth']
plate=bpy.data.objects['IS4_PerforatedCartridge'];diaphragm=bpy.data.objects['IH1_Diaphragm'];diaphragm_case=bpy.data.objects['IS4_DiaphragmCartridge']
b=Builder.__new__(Builder);b.id='IR8';b.serial=0;b.root=root;b.upper=fixed
b.col=bpy.data.collections.new('I_ART_REBUILD_R8');scene.collection.children.link(b.col);b.mats={}
for name,color,metal,rough,coat in [('CoreNickel',(.43,.46,.47),.96,.26,.10),('CoreBronze',(.44,.25,.085),.95,.30,.05),('CoreOxide',(.048,.057,.055),.88,.34,0),('ManifoldLacquer',(.018,.022,.020),.25,.27,.32),('Liner',(.045,.052,.049),.42,.44,0),('AcousticFelt',(.004,.005,.0045),0,.88,0),('CoreRubber',(.014,.016,.015),0,.52,0),('IrisA',(.24,.27,.27),.95,.33,0),('IrisB',(.32,.34,.33),.95,.29,0)]:
    b.material(name,color,metal,rough,coat=coat)
ns={'bpy':bpy,'math':math,'Vector':Vector,'Matrix':Matrix,'Quaternion':Quaternion,'COL':b.col,'M':b.mats}
exec(compile((ROOT/'blender/fast_geometry.py').read_text(),str(ROOT/'blender/fast_geometry.py'),'exec'),ns);b.fast=ns
def apply(obj):
    if obj.data.users>1:obj.data=obj.data.copy()
    bpy.context.view_layer.objects.active=obj
    for modifier in list(obj.modifiers):bpy.ops.object.modifier_apply(modifier=modifier.name)
    bm=bmesh.new();bm.from_mesh(obj.data)
    if 'PerforatedLiner' in obj.name or 'AcousticFeltBacking' in obj.name:bmesh.ops.remove_doubles(bm,verts=list(bm.verts),dist=1e-6)
    bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(obj.data);bm.free()
def sleeve(name,outer,inner,depth,mat,parent,z,segments=128):
    obj=b.sleeve(name,outer,inner,depth,mat,parent,(0,0,z),segments);obj.modifiers[0].width=min(.0005,depth*.15);return obj
def bore(obj,tool):
    if obj.data.users>1:obj.data=obj.data.copy()
    bpy.context.view_layer.update();bpy.context.view_layer.objects.active=obj
    mod=obj.modifiers.new('Machined fastener bore','BOOLEAN');mod.operation='DIFFERENCE';mod.object=tool;bpy.ops.object.modifier_apply(modifier=mod.name)
def lathe(name,profile,mat,parent,n=128):
    vertices=[(r*math.cos(k*math.tau/n),r*math.sin(k*math.tau/n),z) for r,z in profile for k in range(n)]
    faces=[(j*n+k,j*n+(k+1)%n,((j+1)%len(profile))*n+(k+1)%n,((j+1)%len(profile))*n+k) for j in range(len(profile)) for k in range(n)]
    smooth=[abs(profile[j][1]-profile[(j+1)%len(profile)][1])>1e-8 for j in range(len(profile)) for _ in range(n)]
    return b.fast['fast_instance'](b.name(name),vertices,faces,mat,parent,(0,0,0),smooth_faces=smooth)
front=sleeve('PlateFrontRetainer',.583,.542,.008,'CoreNickel',plate,.090)
back=sleeve('PlateRearShoulder',.575,.540,.007,'CoreOxide',plate,.1095)
sleeve('RetainerBronzeEdge',.584,.578,.003,'CoreBronze',plate,.0865)
sleeve('RearSealSeat',.555,.540,.003,'CoreRubber',plate,.1145)
cone=lathe('DeepResonatorThroat',[(.548,.113),(.538,.135),(.508,.176),(.503,.185),(.485,.185),(.490,.176),(.520,.135),(.530,.113)],'CoreOxide',plate)
sleeve('ThroatExitLip',.504,.484,.005,'CoreBronze',plate,.184)
bolts=[]
for obj in [front,back]:apply(obj)
bezel=bpy.data.objects['IH1_PerforatedPlateBezel_0216']
for i in range(8):
    a=i*math.tau/8+.15;p=Vector((.563*math.cos(a),.563*math.sin(a),.082))
    head=b.cyl('RetainerCaptiveHead',.0075,.008,'CoreBronze',plate,p,None,12);bolts.append(head.name)
    b.cube('RetainerHeadSlot',(.008,.0015,.0008),'CoreOxide',plate,p-Vector((0,0,.0043)),.0002,(0,0,a))
    b.cyl('RetainerScrewShank',.0033,.033,'CoreNickel',plate,(p.x,p.y,.1025),None,32)
    tool=b.cyl('RetainerBoreTool',.0036,.046,'CoreOxide',plate,(p.x,p.y,.098),None,48)
    for obj in [front,back,bezel]:bore(obj,tool)
    bpy.data.objects.remove(tool,do_unlink=True)
for i in range(3):
    a=i*math.tau/3+.35
    b.beam('ResonatorBridge',(.578*math.cos(a),.578*math.sin(a),.115),(.519*math.cos(a),.519*math.sin(a),.165),.009,'CoreNickel',plate)
    b.cyl('BridgeSeatBolt',.011,.006,'CoreBronze',plate,(.566*math.cos(a),.566*math.sin(a),.119),None,12)
# Connect the visible front hub to the moving diaphragm, not to a static sibling.
hub=bpy.data.objects['IH1_DiaphragmHub_0312'];world=hub.matrix_world.copy();hub.parent=diaphragm;hub.matrix_world=world;bpy.context.view_layer.update()
hub.data=hub.data.copy();hub.data.materials.clear();hub.data.materials.append(b.mats['CoreNickel'])
tool=b.cyl('PistonServiceHexTool',.022,.012,'CoreOxide',hub,(0,0,-.044),None,6);bore(hub,tool);bpy.data.objects.remove(tool,do_unlink=True)
sleeve('PistonFaceMachinedRing',.078,.070,.002,'CoreOxide',hub,-.046,96)
stem=b.cyl('ContinuousPistonStem',.035,.175,'CoreNickel',diaphragm,(0,0,-.0825),None,96)
sleeve('PistonRootCollar',.065,.034,.016,'CoreBronze',diaphragm,-.031,96)
for radius in [.24,.31,.39]:
    z=-.0322*math.sqrt(1-(radius/.46)**2)-.001
    b.torus('DiaphragmRolledBead',radius,.002,'CoreNickel',diaphragm,(0,0,z))
for i in range(3):
    a=i*math.tau/3;xy=Vector((.35*math.cos(a),.35*math.sin(a),.335))
    o=b.sleeve('SpringDamperHousing',.048,.033,.018,'CoreOxide',diaphragm_case,xy,64);o.modifiers[0].width=.0006
    b.torus('SpringSeatTrim',.041,.002,'CoreBronze',diaphragm_case,xy+Vector((0,0,.009)))
for i in range(6):
    leaf=bpy.data.objects['IH1_IrisLeaf'+str(i)]
    for obj in leaf.children:
        if obj.type=='MESH' and 'IrisLeafSheet' in obj.name:
            obj.data=obj.data.copy();obj.data.materials.clear();obj.data.materials.append(b.mats['IrisA' if i%2==0 else 'IrisB'])
            bevel=obj.modifiers.new('Leaf edge radius','BEVEL');bevel.width=.00025;bevel.segments=2;apply(obj)
# A sectional manufactured jacket gives the existing pressure line a coherent housing.
bell=bpy.data.objects['IH1_Bellows'];M=fixed.matrix_world.inverted()@mouth.matrix_world;B=fixed.matrix_world.inverted()@bell.matrix_world
p0=M@Vector((0,0,.610));p3=B@Vector((0,0,-.37));p1=p0+M.to_3x3().col[2]*.28;p2=p3-B.to_3x3().col[2]*.25
def line_point(t):return p0*(1-t)**3+p1*3*(1-t)**2*t+p2*3*(1-t)*t*t+p3*t**3
def line_axis(t):return ((p1-p0)*(1-t)**2+(p2-p1)*2*(1-t)*t+(p3-p2)*t*t).normalized()
transport=[];last=line_axis(0);normal=M.to_3x3().col[0].normalized()
for j in range(97):
    t=j/96;axis=line_axis(t);normal=last.rotation_difference(axis)@normal;normal=(normal-axis*normal.dot(axis)).normalized();transport.append((line_point(t),normal.copy(),axis.cross(normal).normalized(),axis));last=axis
jackets=[]
for lo,hi in [(8,31),(35,61),(65,88)]:
    vertices=[];faces=[];sides=64;length=hi-lo+1
    for inner in [False,True]:
        for j in range(lo,hi+1):
            point,n,v,axis=transport[j];radius=.078 if inner else .11+.06*math.sin(math.pi*j/96)
            for k in range(sides):vertices.append(point+(n*math.cos(k*math.tau/sides)+v*math.sin(k*math.tau/sides))*radius)
    size=length*sides
    for inner in [0,1]:
        for j in range(length-1):
            for k in range(sides):
                a=inner*size+j*sides+k;c=inner*size+j*sides+(k+1)%sides;face=(a,c,c+sides,a+sides);faces.append(tuple(reversed(face)) if inner else face)
    for j in [0,length-1]:
        for k in range(sides):a=j*sides+k;c=j*sides+(k+1)%sides;faces.append((a,c,c+size,a+size))
    jacket=b.fast['fast_instance'](b.name('SectionedPressureHousing'),vertices,faces,'ManifoldLacquer',fixed,(0,0,0),smooth_faces=True)
    for polygon in jacket.data.polygons:
        if polygon.index>=2*(length-1)*sides:polygon.use_smooth=False
    jackets.append(jacket.name)
    for j in [lo,hi]:
        point,n,v,axis=transport[j];radius=.11+.06*math.sin(math.pi*j/96)
        collar=b.sleeve('ManifoldCouplingFlange',radius+.010,.0775,.012,'CoreNickel',fixed,point,96);collar.rotation_euler=axis.to_track_quat('Z','Y').to_euler();collar.modifiers[0].width=.0008
        rim=b.torus('CouplingBronzeSeal',radius+.002,.0025,'CoreBronze',fixed,point,axis.to_track_quat('Z','Y'))
# Perforated acoustic backing mounted inside each rear half, using actual shell surfaces.
P=[Vector(v) for v in [(-.38,-.53,2.25),(-.15,.62,2.10),(.45,.78,2.82),(.45,.74,3.38)]]
def center(t):return P[0]*(1-t)**3+P[1]*3*(1-t)**2*t+P[2]*3*(1-t)*t*t+P[3]*t**3
def tangent(t):return ((P[1]-P[0])*(1-t)**2+(P[2]-P[1])*2*(1-t)*t+(P[3]-P[2])*t*t).normalized()
frames=[];last=tangent(0);normal=(Vector((0,0,1))-last*last.z).normalized()
for j in range(301):
    axis=tangent(j/300);normal=last.rotation_difference(axis)@normal;normal=(normal-axis*normal.dot(axis)).normalized();frames.append((normal.copy(),axis.cross(normal).normalized()));last=axis
liner_rows=[]
for index in range(5):
    low=max(index/6+.023,.072);high=(index+1)/6-.023
    for side in [-1,1]:
        suffix='_A' if side<0 else '_B';shell=next(o for o in root.children_recursive if o.name.startswith('IH1_RearPorcelain'+str(index)+'_') and o.name.endswith(suffix))
        parent=bpy.data.objects['IS7_CageLeft' if side<0 else 'IS7_CageRight']
        ev=shell.evaluated_get(bpy.context.evaluated_depsgraph_get());m=ev.to_mesh();m.calc_loop_triangles();to_fixed=fixed.matrix_world.inverted()@shell.matrix_world
        vertices=[to_fixed@v.co for v in m.vertices];faces=[tuple(t.vertices) for t in m.loop_triangles];ev.to_mesh_clear();surface=BVHTree.FromPolygons(vertices,faces,all_triangles=True)
        cache={}
        def mapped(t,a,layer):
            key=(round(t,9),round(a,9))
            if key not in cache:
                n,v=frames[min(300,max(0,round(t*300)))];radial=(n*math.cos(a)+v*math.sin(a)).normalized()
                hit,normal,tri,d=surface.ray_cast(center(t),radial)
                if hit is None:raise RuntimeError(('liner surface miss',index,side,t,a))
                cache[key]=(hit,radial)
            hit,radial=cache[key];point=hit-radial*(.006+layer*.004)
            return parent.matrix_world.inverted()@(fixed.matrix_world@point)
        a0,a1=(math.radians(190),math.radians(264)) if side<0 else (math.radians(96),math.radians(170))
        mid=(low+high)/2;arc=(mapped(mid,a1,0)-mapped(mid,a0,0)).length
        cols=max(6,round(arc/.045));rows=max(3,round((mapped(high,(a0+a1)/2,0)-mapped(low,(a0+a1)/2,0)).length/.045))
        vs=[];fs=[];uv=[];bv=[];bf=[]
        for y in range(rows):
            for x in range(cols):
                u0=low+(high-low)*y/rows;u1=low+(high-low)*(y+1)/rows;v0=a0+(a1-a0)*x/cols;v1=a0+(a1-a0)*(x+1)/cols;u=(u0+u1)/2;v=(v0+v1)/2
                corners=[(u0,v0),(u0,v1),(u1,v1),(u1,v0)];outer=[]
                for edge in range(4):
                    aa=corners[edge];bb=corners[(edge+1)%4]
                    for j in range(6):outer.append((aa[0]+(bb[0]-aa[0])*j/6,aa[1]+(bb[1]-aa[1])*j/6))
                inner=[]
                for t,a in outer:
                    du=(t-u)/(u1-u0);dv=(a-v)/(v1-v0);length=math.hypot(du,dv)
                    inner.append((u+(u1-u0)*.24*du/length,v+(v1-v0)*.24*dv/length))
                base=len(vs)
                for layer in [0,1]:
                    for ring in [outer,inner]:
                        for t,a in ring:vs.append(mapped(t,a,layer));uv.append(((a-a0)/(a1-a0),(t-low)/(high-low)))
                for layer in [-.375,-.75]:
                    for ring in [outer,inner]:
                        for t,a in ring:bv.append(mapped(t,a,layer))
                bf.append(tuple(base+24+k for k in range(24)));bf.append(tuple(base+72+k for k in range(23,-1,-1)))
                for k in range(24):
                    nk=(k+1)%24
                    for a,b_ in [(0,24),(72,48),(48,0),(24,72)]:
                        if a==48 and not ((y==0 and k<6) or (x==cols-1 and 6<=k<12) or (y==rows-1 and 12<=k<18) or (x==0 and k>=18)):continue
                        fs.append((base+a+k,base+a+nk,base+b_+nk,base+b_+k))
                        if a!=24:bf.append((base+a+k,base+a+nk,base+b_+nk,base+b_+k))
        liner=b.fast['fast_instance'](b.name('PerforatedLiner'),vs,fs,'Liner',parent,(0,0,0),smooth_faces=False,uv=uv)
        backing=b.fast['fast_instance'](b.name('AcousticFeltBacking'),bv,bf,'AcousticFelt',parent,(0,0,0),smooth_faces=False)
        # Folded metal boundary belongs to this installed liner cassette.
        for t in [low,high]:
            line=[mapped(t,a0+(a1-a0)*k/32,1) for k in range(33)]
            b.tube('LinerFoldedRim',line,.0025,'CoreNickel',parent,3)
        for a in [a0,a1]:
            line=[mapped(low+(high-low)*k/32,a,1) for k in range(33)]
            b.tube('LinerSideHem',line,.0025,'CoreNickel',parent,3)
        spines=[o for o in parent.children if o.type=='CURVE' and 'ChamberSpine' in o.name]
        mounts=[]
        for fraction in [.18,.82]:
            t=low+(high-low)*fraction;a=a1 if side<0 else a0;edge=mapped(t,a,1);candidates=[]
            for spine in spines:
                points=[parent.matrix_world.inverted()@spine.matrix_world@Vector(p.co[:3]) for p in spine.data.splines[0].points]
                for first,last in zip(points,points[1:]):
                    span=last-first;u=max(0.,min(1.,(edge-first).dot(span)/span.length_squared));hit=first+span*u;candidates.append(((hit-edge).length,hit,spine.name))
            distance,hit,rail=min(candidates,key=lambda item:item[0]);tab=b.beam('LinerMountTab',edge,hit,.005,'CoreNickel',parent)
            n,v=frames[round(t*300)];radial=parent.matrix_world.to_3x3().inverted()@(fixed.matrix_world.to_3x3()@(n*math.cos(a)+v*math.sin(a)))
            bolt=b.cyl('LinerCaptiveBolt',.006,.004,'CoreBronze',parent,edge-radial*.002,(-radial).to_track_quat('Z','Y'),12)
            mounts.append({'tab':tab.name,'bolt':bolt.name,'rail':rail,'length':distance})
        liner_rows.append({'name':liner.name,'backing':backing.name,'shell':shell.name,'cage':parent.name,'cells':rows*cols,'thickness':.004,'shell_clearance':.006,'mounts':mounts})
flanges=[]
for row in prior['split_ribs']:
    rib=bpy.data.objects[row['part']];index=int(row['source'][-4:])-194;t=.05+.83*index/14;n,v=frames[round(t*300)];side=row['side'];parent=rib.parent
    # Actual rib centerline endpoints; cap plates sit on their own side of the seam.
    radius_table=[(0,.90),(.14,.89),(.28,.93),(.43,.85),(.60,.65),(.76,.39),(.9,.18),(1,.055)]
    rr=.055
    for (aa,ra),(bb,rb) in zip(radius_table,radius_table[1:]):
        if t<=bb:
            u=(t-aa)/(bb-aa);u=max(0.,min(1.,u));rr=ra+(rb-ra)*u*u*(3-2*u);break
    # Formed channel section replaces the bare round rod while keeping its centerline.
    profile=[(-.014,-.034),(.014,-.034),(.014,-.024),(.004,-.024),(.004,.024),(.014,.024),(.014,.034),(-.014,.034)]
    eps=math.asin(.0015/(rr*.66));a0=eps if side>0 else math.pi+eps;a1=math.pi-eps if side>0 else math.tau-eps
    segments=96;vertices=[];faces=[];axis_t=tangent(t);to_rib=rib.matrix_world.inverted()@fixed.matrix_world
    for j in range(segments+1):
        angle=a0+(a1-a0)*j/segments;radial=n*math.cos(angle)+v*math.sin(angle)
        for dr,dz in profile:
            point=center(t)+radial*(rr*.66+dr)+axis_t*dz
            if j in [0,segments]:point+=v*(side*.0015-(point-center(t)).dot(v))
            vertices.append(to_rib@point)
    for j in range(segments):
        for k in range(8):faces.append((j*8+k,j*8+(k+1)%8,(j+1)*8+(k+1)%8,(j+1)*8+k))
    faces.extend([tuple(range(7,-1,-1)),tuple(segments*8+k for k in range(8))])
    data=bpy.data.meshes.new(rib.name+'_FormedChannel');data.from_pydata(vertices,[],faces);data.materials.append(b.mats['CoreNickel']);data.materials.append(b.mats['CoreBronze'])
    for polygon in data.polygons:
        polygon.use_smooth=polygon.index<segments*8
        if polygon.index<segments*8 and polygon.index%8 in [1,5]:polygon.material_index=1
    bm=bmesh.new();bm.from_mesh(data)
    for edge in bm.edges:
        aa,bb=[vv.index for vv in edge.verts]
        if aa%8==bb%8:edge.smooth=False
    bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(data);bm.free();rib.data=data
    bevel=rib.modifiers.new('Formed channel edge break','BEVEL');bevel.width=.0012;bevel.segments=2;apply(rib)
    for sign in [-1,1]:
        point=center(t)+n*sign*rr*.66+v*side*.0055
        point=parent.matrix_world.inverted()@(fixed.matrix_world@point)
        axis=parent.matrix_world.to_3x3().inverted()@(fixed.matrix_world.to_3x3()@(v*side));q=axis.to_track_quat('Z','Y')
        flange=b.sleeve('RibSeamFlange',.038,.010,.008,'CoreNickel',parent,point,64);flange.rotation_euler=q.to_euler();flange.modifiers[0].width=.0005;apply(flange)
        for bolt_side in [-1,1]:
            location=point+q@Vector((bolt_side*.028,0,-.0025))
            tool=b.cyl('FlangeSeatTool',.0045,.0035,'CoreOxide',parent,location,q,32);bore(flange,tool);bpy.data.objects.remove(tool,do_unlink=True)
            b.cyl('FlushFlangeFastener',.004,.003,'CoreBronze',parent,location,q,12)
        flanges.append(flange.name)
for obj in b.col.objects:
    if obj.type=='MESH':apply(obj)
for image in bpy.data.images:
    if image.source=='FILE' and image.filepath and not image.packed_file:image.filepath=bpy.path.relpath(bpy.path.abspath(image.filepath),start=str(TARGET.parent))
scene.frame_set(1);bpy.ops.wm.save_as_mainfile(filepath=str(TARGET))
bpy.ops.object.select_all(action='DESELECT')
for obj in [root]+list(root.children_recursive):obj.select_set(True)
bpy.context.view_layer.objects.active=root;component=ROOT/'app/assets/collection/components/I_art_r8.glb'
bpy.ops.export_scene.gltf(filepath=str(component),export_format='GLB',use_selection=True,export_apply=False,export_animations=False,export_morph=True,export_extras=True)
shutil.copy2(ROOT/'review/I_refinement/service_r7/take.json',OUT/'take.json')
result={'source':str(TARGET.relative_to(ROOT)),'source_sha256':sha(TARGET),'input_source_sha256':sha(SOURCE),'component':str(component.relative_to(ROOT)),'component_sha256':sha(component),'groups':prior['groups'],'retainer':front.name,'rear_shoulder':back.name,'resonator':cone.name,'piston_stem':stem.name,'hub':hub.name,'pressure_jackets':jackets,'liners':liner_rows,'rib_flanges':flanges,'reference':['production/I_refinement/art_rebuild_r8/acoustic_core.png','production/I_refinement/art_rebuild_r8/cage_hinge_liner.png'],'scope':'Artwork-led partial rebuild: acoustic retention/resonator/piston, sectional pressure-line housing, backed liners and formed ribs/flanges. Rotating hinges, seam locks and full geometry/native acceptance remain pending.'}
(OUT/'build.json').write_text(json.dumps(result,indent=2)+'\n');print('I_ART_R8',len(liner_rows),'liners',flush=True)
