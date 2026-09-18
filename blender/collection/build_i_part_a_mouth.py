"""Part A only: detailed mouth anatomy from mouth_detail_r1 art. No whole-I overwrite."""
import bpy,bmesh,json,math,hashlib,sys
from pathlib import Path
from mathutils import Vector,Matrix,Quaternion
from mathutils.geometry import tessellate_polygon
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(Path(__file__).parent))
from geometry import Builder
OUT=ROOT/'review/I_refinement/part_a_mouth';OUT.mkdir(parents=True,exist_ok=True);TARGET=ROOT/'blender/collection/I_part_a_mouth.blend';sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
if TARGET.exists():
 prev=json.loads((OUT/'build.json').read_text());assert sha(TARGET)==prev['source_sha256'],'Unrecorded Part A edits';(TARGET.parent/'checkpoints'/('I-partA-'+sha(TARGET)[:12]+'.blend')).write_bytes(TARGET.read_bytes())
b=Builder('IAM','Helix mouth component A');scene=bpy.context.scene;mouth=b.empty('IAM_Mouth',b.upper)
DISH_DEPTH=.010;STACK_STEP=.010;BACK_SHIFT=.090;CAM_Z=.190
for name,color,metal,rough,coat in [('Ivory',(.80,.755,.66),0,.23,.45),('Nickel',(.33,.35,.33),.95,.25,.10),('Satin',(.22,.23,.21),.94,.32,.04),('Dark',(.043,.045,.038),.8,.33,0),('Bronze',(.36,.245,.11),.95,.30,0),('Rubber',(.012,.015,.012),0,.61,0),('Red',(.30,.009,.004),.2,.23,.4)]:
 b.material('A_'+name,color,metal,rough,coat=coat)
# Generated unlit brushing is a real component texture, mapped along each leaf.
brushed=b.material('A_LeafNickel',(.38,.365,.335),.96,.28)
p=next(x for x in brushed.node_tree.nodes if x.type=='BSDF_PRINCIPLED')
for filename,socket in [('nickel_roughness.png','Roughness'),('nickel_normal.png','Normal')]:
 tex=brushed.node_tree.nodes.new('ShaderNodeTexImage');tex.image=bpy.data.images.load(str(ROOT/'production/I_refinement/part_a_mouth/material_r2'/filename));tex.image.colorspace_settings.name='Non-Color';tex.image.pack()
 if socket=='Normal':
  normal=brushed.node_tree.nodes.new('ShaderNodeNormalMap');normal.inputs['Strength'].default_value=.8;brushed.node_tree.links.new(tex.outputs['Color'],normal.inputs['Color']);brushed.node_tree.links.new(normal.outputs[0],p.inputs[socket])
 else:brushed.node_tree.links.new(tex.outputs['Color'],p.inputs[socket])
def clean(o):
 bpy.context.view_layer.objects.active=o
 for m in list(o.modifiers):bpy.ops.object.modifier_apply(modifier=m.name)
 bm=bmesh.new();bm.from_mesh(o.data);bmesh.ops.remove_doubles(bm,verts=list(bm.verts),dist=1e-7)
 bmesh.ops.dissolve_degenerate(bm,dist=1e-7,edges=list(bm.edges))
 duplicates=[];seen=set()
 for face in bm.faces:
  key=frozenset(v for v in face.verts)
  if key in seen:duplicates.append(face)
  else:seen.add(key)
 if duplicates:bmesh.ops.delete(bm,geom=duplicates,context='FACES_ONLY')
 loose=[e for e in bm.edges if not e.link_faces]
 if loose:bmesh.ops.delete(bm,geom=loose,context='EDGES')
 bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces))
 for edge in bm.edges:
  if 'Porcelain' in o.name:edge.smooth=True
  elif edge.is_manifold and edge.calc_face_angle()>.55:edge.smooth=False
 if 'Porcelain' in o.name:
  for face in bm.faces:face.smooth=len(face.verts)==4
 bm.to_mesh(o.data);bm.free();return o
def lathe(name,profile,mat,parent=mouth,n=192,start=0,end=math.tau):
 closed=abs(end-start-math.tau)<1e-5;cols=n if closed else n+1;v=[];f=[];sm=[];uv=[]
 for r,z in profile:
  for k in range(cols):a=start+(end-start)*k/n;v.append((r*math.cos(a),r*math.sin(a),z));uv.append((k/n,z))
 for j in range(len(profile)):
  c=(j+1)%len(profile)
  for k in range(n):
   q=(k+1)%cols;f.append((j*cols+k,j*cols+q,c*cols+q,c*cols+k));sm.append(abs(profile[j][1]-profile[c][1])>1e-8)
 if not closed:
  f.extend([tuple(j*cols for j in range(len(profile))),tuple(j*cols+n for j in range(len(profile)-1,-1,-1))]);sm.extend([False,False])
 o=b.fast['fast_instance'](b.name(name),v,f,'A_'+mat,parent,(0,0,0),smooth_faces=sm,uv=uv);return clean(o)
def cut(o,tool):
 if o.data.users>1:o.data=o.data.copy()
 bpy.context.view_layer.update();bpy.context.view_layer.objects.active=o;m=o.modifiers.new('Machined bore','BOOLEAN');m.operation='DIFFERENCE';m.object=tool;m.solver='EXACT';bpy.ops.object.modifier_apply(modifier=m.name)
def formed_leaf(outline,pivot,parent):
 xy=[Vector((x-pivot,y,0)) for x,y in outline];lookup={tuple(v):j for j,v in enumerate(xy)}
 fs=[tuple(v if isinstance(v,int) else lookup[tuple(v)] for v in tri) for tri in tessellate_polygon([xy])]
 mesh=bpy.data.meshes.new('Formed leaf surface');mesh.from_pydata(xy,[],fs)
 bm=bmesh.new();bm.from_mesh(mesh)
 for step in range(5):
  edges=[e for e in bm.edges if e.calc_length()>.075]
  if not edges:break
  bmesh.ops.subdivide_edges(bm,edges=edges,cuts=1,use_grid_fill=True)
 for v in bm.verts:
  x=v.co.x+pivot;y=v.co.y
  # Shallow formed steel dish. Stack separation is checked over the real sweep.
  v.co.z=DISH_DEPTH*((x*x+y*y)/(.813**2)-1)
 bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces))
 if sum(f.normal.z for f in bm.faces)<0:bmesh.ops.reverse_faces(bm,faces=list(bm.faces))
 bm.to_mesh(mesh);bm.free()
 layer=mesh.uv_layers.new(name='LeafGrain')
 for face in mesh.polygons:
  face.use_smooth=True
  for li in face.loop_indices:
   co=mesh.vertices[mesh.loops[li].vertex_index].co;layer.data[li].uv=((co.x+pivot)*2.5+.5,co.y*2.5+.5)
 o=bpy.data.objects.new(b.name('CurvedIrisSheet'),mesh);b.col.objects.link(o);o.parent=parent;o.data.materials.append(brushed)
 sol=o.modifiers.new('Retained spring steel thickness','SOLIDIFY');sol.thickness=.0014;sol.offset=0
 clean(o);return o
# Smooth the cross section itself; smooth normals cannot repair an angular silhouette.
def rounded_profile(points,steps=8):
 result=[]
 for i,p1 in enumerate(points):
  p0=Vector(points[(i-1)%len(points)]);p1=Vector(p1);p2=Vector(points[(i+1)%len(points)]);p3=Vector(points[(i+2)%len(points)])
  for j in range(steps):
   t=j/steps;result.append(tuple(.5*((2*p1)+(-p0+p2)*t+(2*p0-5*p1+4*p2-p3)*t*t+(-p0+3*p1-3*p2+p3)*t*t*t)))
 return result
# A rounded outer porcelain rim with only a shallow rear return; not a massive cone into the core.
profile=[(.812,.180),(.861,.105),(.892,.008),(.892,-.060),(.877,-.119),(.849,-.149),(.813,-.149),(.789,-.132),(.784,-.100),(.802,-.072),(.816,.004),(.821,.08),(.788,.167)]
profile=rounded_profile(profile)
collars=[lathe('PorcelainUpper',profile,'Ivory',start=.018,end=math.pi-.018,n=160),lathe('PorcelainLower',profile,'Ivory',start=math.pi+.018,end=math.tau-.018,n=160)]
lathe('RolledNickelEdge',[(.782,-.106),(.790,-.118),(.802,-.119),(.807,-.108),(.803,-.099),(.789,-.097)],'Nickel')
# The art shows outer overlapping leaves. A broad opaque washer was hiding them.
lathe('ConcaveMachinedMask',rounded_profile([(.787,-.100),(.773,-.100),(.767,-.094),(.767,-.075),(.779,-.068),(.790,-.082)],4),'Nickel')
lathe('ClearApertureFineLip',[(.598,.149),(.605,.149),(.609,.156),(.605,.161),(.599,.161)],'Nickel')
lathe('IrisOuterCase',[(.821,-.081),(.838,-.081),(.838,.212),(.823,.212)],'Dark')
# Behind the aperture: concentric stepped perforated surfaces, separate rings and visible cavities.
guard=b.empty('IAM_AcousticGuard',mouth,(0,0,BACK_SHIFT));screens=[]
def perforated(name,ri,ro,depth,rows,mat,parent=guard):
 v=[];f=[];uv=[]
 for row in range(rows):
  low=ri+(ro-ri)*row/rows;high=ri+(ro-ri)*(row+1)/rows;mid=(low+high)/2;pitch=(high-low);count=round(math.tau*((ri+ro)/2)/pitch);da=math.pi/count
  for k in range(count):
   a=(k+.5)*math.tau/count;center=Vector((mid*math.cos(a),mid*math.sin(a)));off=len(v);circle_r=min(pitch*.34,mid*math.sin(da)*.69)
   # Rectilinear annular cell boundary and a ROUND 16-gon bore.
   for back in [False,True]:
    for hole in [False,True]:
     for j in range(16):
      theta=j*math.tau/16;dx=math.cos(theta);dy=math.sin(theta)
      if hole:p=center+Vector((math.cos(a)*dx-math.sin(a)*dy,math.sin(a)*dx+math.cos(a)*dy))*circle_r
      else:
       scale=1/max(abs(dx),abs(dy));radius=mid+dx*scale*pitch*.5;angle=a+dy*scale*da;p=Vector((radius*math.cos(angle),radius*math.sin(angle)))
      z=depth+.014*(p.length/ro)**2+(.007 if back else 0);v.append((p.x,p.y,z));uv.append((p.x/ro/2+.5,p.y/ro/2+.5))
   for j in range(16):
    q=(j+1)%16
    for d,rev in [(0,False),(32,True)]:
     face=(off+d+j,off+d+q,off+d+16+q,off+d+16+j);f.append(face[::-1] if rev else face)
    f.append((off+16+j,off+16+q,off+48+q,off+48+j))
    aa=v[off+j];bb=v[off+q];ra=math.hypot(aa[0],aa[1]);rb=math.hypot(bb[0],bb[1])
    if (row==0 and abs(ra-ri)<1e-6 and abs(rb-ri)<1e-6) or (row==rows-1 and abs(ra-ro)<1e-6 and abs(rb-ro)<1e-6):f.append((off+j,off+32+j,off+32+q,off+q))
 o=b.fast['fast_instance'](b.name(name),v,f,'A_'+mat,parent,(0,0,0),smooth_faces=False,uv=uv);clean(o);screens.append(o.name);return o
perforated('OuterGuard',.444,.597,.065,3,'Satin')
perforated('MiddleGuard',.29,.419,.104,3,'Dark')
perforated('InnerGuard',.099,.267,.135,4,'Satin')
for radius,depth in [(.601,.083),(.434,.104),(.278,.139),(.093,.153)]:
 lathe('SteppedGuardRetainer',[(radius-.008,depth-.012),(radius+.009,depth-.012),(radius+.014,depth-.003),(radius+.010,depth+.010),(radius-.006,depth+.010)],'Nickel',guard)
 b.torus('BronzeRetainerBead',radius+.008,.0018,'A_Bronze',guard,(0,0,depth-.012))
# Thin seats connect stepped screens to their concentric support frames.
for ra,rb,z0,z1 in [(.416,.446,.118,.079),(.264,.293,.149,.118)]:
 lathe('SteppedScreenBridge',[(ra,z0),(rb,z1),(rb,z1+.006),(ra,z0+.006)],'Dark',guard)
for i in range(12):
 a=i*math.tau/12;p=(.616*math.cos(a),.616*math.sin(a),.085)
 washer=b.sleeve('GuardFastenerSeat',.012,.004,.004,'A_Nickel',guard,p,32);clean(washer)
 b.cyl('GuardBoltShank',.0038,.032,'A_Nickel',guard,(p[0],p[1],.105),None,24);b.cyl('GuardHexHead',.008,.008,'A_Bronze',guard,(p[0],p[1],.08),None,6)
lathe('GuardOuterSeat',[(.595,.064),(.628,.064),(.636,.075),(.636,.14),(.618,.15),(.607,.133)],'Dark',guard)
# Continuously connected diaphragm/head subassembly. Membrane recess sits behind the guard.
moving=b.empty('IAM_DiaphragmMotion',mouth)
lathe('CentralResonatorCap',[(0,-.116),(.049,-.116),(.074,-.099),(.086,-.072),(.083,-.044),(.064,-.032),(.030,-.032),(.030,.325+BACK_SHIFT),(0,.325+BACK_SHIFT)],'Nickel',moving)
lathe('HeadBronzeCollar',[(.082,-.061),(.088,-.061),(.088,-.044),(.082,-.044)],'Bronze',moving)
for i in range(3):
 y=(i-1)*.062;x=math.sqrt(max(.001,.079**2-y*y));rootp=Vector((x,y,-.07));end=Vector((.18,y,-.097))
 b.beam('TineRoot',rootp,end,.010,'A_Nickel',moving);b.beam('EnamelTine',end,(.275,y,-.115),.010,'A_Red',moving);b.sphere('TineRoundedTip',.010,'A_Red',moving,(.275,y,-.115))
# Diaphragm front is convex, with a rolled compliant surround and three explicit support springs.
lathe('DomedDiaphragm',[(.03,.311),(.14,.298),(.28,.276),(.43,.268),(.48,.290),(.49,.311),(.48,.319),(.425,.280),(.28,.285),(.14,.307),(.03,.320)],'Satin',moving)
for r in [.21,.34,.455]:b.torus('DiaphragmFormedBead',r,.0025,'A_Nickel',moving,(0,0,.286 if r<.35 else .286))
lathe('DiaphragmRubberSurround',[(.479,.29),(.491,.28),(.510,.280),(.523,.298),(.520,.315),(.51,.321),(.496,.311),(.486,.312)],'Rubber')
lathe('DiaphragmFixedSeat',[(.516,.280),(.555,.280),(.567,.292),(.565,.333),(.520,.333)],'Dark')
lathe('RearMountFlange',[(.085,.492),(.559,.492),(.583,.504),(.583,.535),(.080,.535)],'Satin')
for i in range(6):
 a=i*math.tau/6+.2;x=.548*math.cos(a);y=.548*math.sin(a)
 b.beam('GuardToRearStandoff',(x,y,.138),(x,y,.496),.014,'A_Nickel',mouth)
for i in range(3):
 a=i*math.tau/3;x=.405*math.cos(a);y=.405*math.sin(a);pts=[]
 for j in range(97):
  t=j/96;ang=t*math.tau*6;pts.append((x+.025*math.cos(ang),y+.025*math.sin(ang),.342+.137*t))
 b.tube('MembraneReturnSpring',pts,.0035,'A_Bronze',mouth,2)
 for z in [.327,.484]:b.cyl('SpringSeat',.033,.015,'A_Dark',mouth,(x,y,z),None,48)
# Axial space is explicit: move the entire rear membrane/frame/spring stack together.
for o in b.col.objects:
 if o.type=='MESH' and any(key in o.name for key in ['DomedDiaphragm','DiaphragmFormedBead','DiaphragmRubber','DiaphragmFixed','RearMountFlange','GuardToRearStandoff','MembraneReturnSpring','SpringSeat']):o.location.z+=BACK_SHIFT
# Fine overlapping blades matched to the visible circular aperture; keep a deliberate resting glimpse.
design=json.loads((ROOT/'production/I_refinement/part_a_mouth/iris_design.json').read_text());pivot=design['pivot'];outline=design['profile'];leaves=[];leaf_count=design['leaf_count']
for i in range(leaf_count):
 a=i*math.tau/leaf_count;leaf_z=.013+i*STACK_STEP;leaf=b.empty('IAM_IrisLeaf'+str(i),mouth,(pivot*math.cos(a),pivot*math.sin(a),leaf_z));leaf.rotation_euler.z=a
 o=formed_leaf(outline,pivot,leaf)
 tool=b.cyl('PivotDrillTool',.0074,.05,'A_Dark',leaf,(0,0,0),None,48);cut(o,tool);bpy.data.objects.remove(tool,do_unlink=True)
 b.cyl('IrisPivotPin',.007,.207,'A_Nickel',mouth,(pivot*math.cos(a),pivot*math.sin(a),.1095),None,48)
 eye=b.sleeve('LeafPivotEye',.017,.0075,.005,'A_Satin',leaf,(0,0,DISH_DEPTH*((pivot/.813)**2-1)+.003),48);clean(eye)
 # Follower at a stable offset, deep enough to enter the rotating cam slot.
 root_z=DISH_DEPTH*(((pivot+.035)**2+.077**2)/(.813**2)-1)
 follower=b.cyl('CamFollower',.0055,(CAM_Z-.007)-leaf_z-root_z,'A_Nickel',leaf,(.035,.077,((CAM_Z-.007)-leaf_z+root_z)*.5),None,32)
 leaves.append({'name':leaf.name,'home':a,'travel':design['travel'],'sheet':o.name,'follower':follower.name})
cam=b.empty('IAM_IrisCam',mouth,(0,0,CAM_Z));cam_ring=lathe('IrisSlottedCam',[(.656,-.008),(.800,-.008),(.800,.008),(.656,.008)],'Bronze',cam)
slot=json.loads((ROOT/'production/I_refinement/part_a_mouth/cam_slot_profile.json').read_text())
for i,row in enumerate(leaves):
 a=i*math.tau/leaf_count;n=len(slot['points']);v=[(x*math.cos(a)-y*math.sin(a),x*math.sin(a)+y*math.cos(a),z) for z in [-.025,.025] for x,y in slot['points']];f=[tuple(range(n-1,-1,-1)),tuple(range(n,2*n))];f.extend((j,(j+1)%n,(j+1)%n+n,j+n) for j in range(n))
 tool=b.fast['fast_instance'](b.name('ExactCamSlotCut'),v,f,'A_Dark',cam,(0,0,0),smooth_faces=False);clean(tool);cut(cam_ring,tool);bpy.data.objects.remove(tool,do_unlink=True)
for i in range(6):
 a=i*math.tau/6+.35;b.cyl('CamSupportRoller',.008,.018,'A_Nickel',mouth,(.809*math.cos(a),.809*math.sin(a),CAM_Z),None,48)
# Porcelain latch seats at the visible rim, tied to a common rear ring via short brackets.
for i in range(6):
 a=i*math.tau/6+.20;p=Vector((.838*math.cos(a),.838*math.sin(a),-.154));q=Quaternion(Vector((0,0,1)),a)
 b.cube('CollarLatchSeat',(.073,.038,.015),'A_Nickel',mouth,p,.005,q)
 b.cyl('EnamelLatchBar',.010,.051,'A_Red',mouth,p+Vector((0,0,-.017)),q@Quaternion(Vector((1,0,0)),math.pi/2),48)
 for sign in [-1,1]:
  tip=p+q@Vector((0,sign*.030,-.013));b.cyl('LatchCaptiveHead',.011,.016,'A_Nickel',mouth,tip,None,64)
  # A true machined screw slot with a retained shank, not a dot pasted onto the shell.
  head=b.cyl('LatchSlottedCap',.008,.006,'A_Satin',mouth,tip+Vector((0,0,-.009)),None,48)
  tool=b.cube('ScrewSlotCut',(.018,.0022,.003),'A_Dark',mouth,tip+Vector((0,0,-.012)),0,q);cut(head,tool);bpy.data.objects.remove(tool,do_unlink=True)
for obj in b.col.objects:
 if obj.type=='MESH':clean(obj)
scene.frame_start=1;scene.frame_end=241;scene.render.fps=30
for frame in range(1,242):
 t=(frame-1)/30;v=max(0,min(1,(t-.6)/1.6)) if t<4.5 else 1-max(0,min(1,(t-5.)/1.6));amount=v*v*(3-2*v)
 for row in leaves:
  o=bpy.data.objects[row['name']];o.rotation_euler.z=row['home']-row['travel']*amount;o.keyframe_insert('rotation_euler',frame=frame)
 cam.rotation_euler.z=-.25*amount;cam.keyframe_insert('rotation_euler',frame=frame)
 # No membrane performance is accepted until the surrounding suspension is rigged.
scene.frame_set(1);bpy.ops.wm.save_as_mainfile(filepath=str(TARGET));bpy.ops.object.select_all(action='DESELECT')
for o in [b.root]+list(b.root.children_recursive):o.select_set(True)
bpy.context.view_layer.objects.active=b.root;component=ROOT/'app/assets/collection/components/I_part_a_mouth.glb';bpy.ops.export_scene.gltf(filepath=str(component),export_format='GLB',use_selection=True,export_apply=False,export_animations=False,export_extras=True)
result={'source':str(TARGET.relative_to(ROOT)),'source_sha256':sha(TARGET),'component':str(component.relative_to(ROOT)),'component_sha256':sha(component),'leaves':leaves,'cam':cam.name,'screens':screens,'reference':'production/I_refinement/part_a_mouth/mouth_detail_r1.png','whole_conch_integrated':False,'scope':'Part A only, detailed appearance/assembly candidate. Actual round perforations, stepped acoustic layers, central shaft, diaphragm/springs and six-blade cam. Requires geometry inspection, exact cam engagement, material/render review and final motion assets. No whole-device art acceptance.'}
(OUT/'build.json').write_text(json.dumps(result,indent=2)+'\n');print('I_PART_A_BUILT',flush=True)
