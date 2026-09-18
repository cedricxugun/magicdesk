"""New bulbous conch body from selected art. Does not load/rebuild the rejected tube host."""
import bpy,bmesh,math,sys,json,hashlib
from pathlib import Path
from mathutils import Vector,Matrix,Quaternion
from mathutils.geometry import tessellate_polygon
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(Path(__file__).parent))
from geometry import Builder
OUT=ROOT/'review/I_refinement/conch_r12';OUT.mkdir(parents=True,exist_ok=True)
TARGET=ROOT/'blender/collection/I_conch_r12.blend';sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
if TARGET.exists():
 old=json.loads((OUT/'build.json').read_text());assert sha(TARGET)==old['source_sha256'],'Unrecorded conch source edits'
 backup=TARGET.parent/'checkpoints'/('I-conch-'+sha(TARGET)[:12]+'.blend');backup.parent.mkdir(exist_ok=True);backup.write_bytes(TARGET.read_bytes())
assert sha(ROOT/'blender/collection/I_conch_r11.blend')=='2af199dc2ad0efbd0854875c59af72fbbf0373301d49c04e5087d304bfa14999','R11 input changed; re-evaluate before applying old form delta'
b=Builder('IC11','Original selected conch silhouette reconstruction');scene=bpy.context.scene
b.material('ConchPorcelain',(.80,.765,.675),0,.27,normal='ceramic_glaze_normal.png',coat=.45)
b.material('ConchNickel',(.38,.405,.395),.95,.25,coat=.12)
b.material('ConchDarkMetal',(.055,.060,.053),.86,.33)
b.material('ConchBrass',(.42,.25,.085),.94,.29)
b.material('ConchRubber',(.009,.013,.011),0,.57)
b.material('ConchRed',(.29,.01,.006),.2,.26,coat=.4)
fixed=b.empty('IC11_Cradle',b.upper);body=b.empty('IC11_ConchBody',b.upper)
mouth=b.empty('IH1_Mouth',body,(-.23,-.54,2.02));axis=Vector((.1,1,.02)).normalized();up=Vector((0,0,1));right=up.cross(axis).normalized();vertical=axis.cross(right).normalized();mouth.rotation_mode='QUATERNION';mouth.rotation_quaternion=Matrix((right,vertical,axis)).transposed().to_quaternion();mouth.scale=(.90,.90,.90)
bpy.context.view_layer.update()
def apply(o):
 if o.type!='MESH':return
 if o.data.users>1:o.data=o.data.copy()
 bpy.context.view_layer.objects.active=o
 for m in list(o.modifiers):bpy.ops.object.modifier_apply(modifier=m.name)
 bm=bmesh.new();bm.from_mesh(o.data);bmesh.ops.remove_doubles(bm,verts=list(bm.verts),dist=1e-7);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(o.data);bm.free()
def boolean(o,tool):
 bpy.context.view_layer.update();bpy.context.view_layer.objects.active=o
 m=o.modifiers.new('Side-facing throat opening','BOOLEAN');m.operation='DIFFERENCE';m.object=tool;m.solver='EXACT';bpy.ops.object.modifier_apply(modifier=m.name)
def radius(q):return .88*(.025+1.45*max(0.,math.sin(math.pi*q))**.50*(1-.70*q))
def center(q):return Vector((.20-1.0*q**1.5,.23+.10*math.sin(math.pi*q)-.15*q,1.16+2.26*q))
def surface(t,a,inside=False):
 q=t+.09*math.sin(a+.65)*math.sin(math.pi*t);rr=radius(q)*(1.+.095*math.sin(math.pi*(t*6.%1.)));thickness=min(.030,rr*.30)
 if inside:rr-=thickness
 return center(q)+Vector((rr*math.cos(a),rr*.80*math.sin(a),0))
def shell_section(index):
 lo=index/6+.0018;hi=(index+1)/6-.0018;nu=32;nv=192;verts=[];faces=[];uv=[]
 parent=b.empty('IC11_SpiralPlate'+str(index),body)
 for inside in [False,True]:
  for j in range(nu+1):
   t=lo+(hi-lo)*j/nu
   for k in range(nv):
    a=k*math.tau/nv;verts.append(surface(t,a,inside));uv.append((k/nv,t))
 size=(nu+1)*nv
 for layer in [0,1]:
  for j in range(nu):
   for k in range(nv):
    a=layer*size+j*nv+k;c=layer*size+j*nv+(k+1)%nv;face=(a,c,c+nv,a+nv);faces.append(face if layer==0 else face[::-1])
 for j in [0,nu]:
  for k in range(nv):a=j*nv+k;c=j*nv+(k+1)%nv;faces.append((a,c,c+size,a+size))
 o=b.fast['fast_instance'](b.name('PorcelainSpiral'+str(index)),verts,faces,'ConchPorcelain',parent,(0,0,0),smooth_faces=True,uv=uv);apply(o)
 return parent,o,lo,hi
# Cut a side-facing aperture into a round shell body; do not start from a horn/pipe sweep.
bpy.ops.mesh.primitive_cone_add(vertices=192,radius1=.797,radius2=.567,depth=1.50)
cut=bpy.context.object;cut.name='IC11_ThroatCutTool';cut.parent=mouth;cut.location=(0,0,.10);cut.rotation_euler=(0,0,0);apply(cut)
shells=[]
for i in range(6):
 parent,o,lo,hi=shell_section(i);boolean(o,cut)
 bevel=o.modifiers.new('Porcelain moulded edge','BEVEL');bevel.width=.004;bevel.segments=3;apply(o)
 shells.append({'node':parent.name,'mesh':o.name,'t':[lo,hi]})
 # Rolled seams use the same surface, and are cut by the actual throat opening too.
 for t in [lo,hi]:
  lip=b.tube('SpiralNickelEdge',[surface(t,k*math.tau/192) for k in range(193)],.008,'ConchNickel',parent)
  bpy.ops.object.select_all(action='DESELECT');lip.select_set(True);bpy.context.view_layer.objects.active=lip;lip.data.use_fill_caps=True;bpy.ops.object.convert(target='MESH');boolean(lip,cut)
 # Small paired clamp seats around visible seams, sized down towards apex.
 for a in [.35,2.1,3.8,5.35]:
  t=hi-.015;q=t+.09*math.sin(a+.65)*math.sin(math.pi*t);p=surface(t,a);normal=Vector((math.cos(a),math.sin(a)/.8,.18)).normalized();scale=min(1.,radius(q)/.30)
  local=mouth.matrix_world.inverted()@(body.matrix_world@p)
  if math.hypot(local.x,local.y)<.84 and local.z<.45:continue
  seat=b.cube('ClampSaddle',(.035*scale,.063*scale,.014*scale),'ConchNickel',parent,p,.004*scale,normal.to_track_quat('Z','Y'))
  b.cyl('RedCaptiveLatch',.009*scale,.048*scale,'ConchRed',parent,p+normal*.016,normal.to_track_quat('Y','Z'),32)
bpy.data.objects.remove(cut,do_unlink=True)
# Lip is deep/rounded ceramic, not a large planar washer.
def lathe(name,profile,mat,parent,n=192):
 verts=[(r*math.cos(k*math.tau/n),r*math.sin(k*math.tau/n),z) for r,z in profile for k in range(n)];faces=[];smooth=[]
 for j in range(len(profile)):
  c=(j+1)%len(profile)
  for k in range(n):faces.append((j*n+k,j*n+(k+1)%n,c*n+(k+1)%n,c*n+k));smooth.append(abs(profile[j][1]-profile[c][1])>.00001)
 uv=[(k/n,(z-min(v[1] for v in profile))/max(.001,max(v[1] for v in profile)-min(v[1] for v in profile))) for r,z in profile for k in range(n)]
 o=b.fast['fast_instance'](b.name(name),verts,faces,mat,parent,(0,0,0),smooth_faces=smooth,uv=uv);apply(o);return o
lip=lathe('RolledThroatPorcelain',[(.600,.850),(.690,.520),(.793,.200),(.870,.045),(.898,-.035),(.890,-.105),(.857,-.157),(.807,-.178),(.750,-.148),(.736,-.127),(.842,-.110),(.846,.015),(.758,.055),(.678,.180),(.577,.840)],'ConchPorcelain',mouth)
lathe('ThinMouthMachinedLip',[(.754,-.129),(.762,-.138),(.774,-.138),(.779,-.127),(.772,-.119),(.758,-.118)],'ConchNickel',mouth)
lathe('DarkRecessedThroat',[(.748,-.105),(.732,-.02),(.709,.14),(.701,.21),(.680,.21),(.688,.13),(.710,-.02),(.728,-.105)],'ConchDarkMetal',mouth)
# Preserve a legible deep grille behind the leaves with real open holes.
verts=[];faces=[]
for row in range(9):
 ri=.105+row*.061;ro=ri+.061;rm=(ri+ro)/2;count=round(math.tau*rm/.058)
 for cell in range(count):
  a=(cell+.5)*math.tau/count;da=math.pi/count;boundary=[(ri,a-da),(rm,a-da),(ro,a-da),(ro,a),(ro,a+da),(rm,a+da),(ri,a+da),(ri,a)];offset=len(verts)
  for z in [.12,.132]:
   for hole in [False,True]:
    for rr,angle in boundary:
     x=rr*math.cos(angle);y=rr*math.sin(angle)
     if hole:x=rm*math.cos(a)+(x-rm*math.cos(a))*.52;y=rm*math.sin(a)+(y-rm*math.sin(a))*.52
     verts.append((x,y,z))
  for k in range(8):
   q=(k+1)%8
   for shift in [0,16]:faces.append((offset+shift+k,offset+shift+q,offset+shift+8+q,offset+shift+8+k))
   faces.append((offset+8+k,offset+8+q,offset+24+q,offset+24+k));faces.append((offset+k,offset+16+k,offset+16+q,offset+q))
grille=b.fast['fast_instance'](b.name('PerforatedAcousticGrille'),verts,faces,'ConchBrass',mouth,(0,0,0),smooth_faces=False);apply(grille)
lathe('GrilleSeatedFrame',[(.655,.106),(.670,.106),(.678,.119),(.678,.145),(.651,.145),(.643,.132),(.643,.115)],'ConchNickel',mouth)
# Six actual curved blades derived from the independent circular-edge envelope candidate.
profile_spec=json.loads((ROOT/'production/I_refinement/conch_r11/iris_with_hub_relief.json').read_text());assert not profile_spec['interior_rings'];pivot=profile_spec['pivot'];profile=profile_spec['closed_outline'];factor=.83/.86
leaves=[]
for i in range(6):
 a=i*math.tau/6;leaf=b.empty('IC11_IrisLeaf'+str(i),mouth,(pivot*factor*math.cos(a),pivot*factor*math.sin(a),-.061-i*.003));leaf.rotation_euler.z=a
 xy=[((x-pivot)*factor,y*factor) for x,y in profile];n=len(xy);vs=[(x,y,z) for z in [-.0007,.0007] for x,y in xy];fs=[tuple(range(n-1,-1,-1)),tuple(range(n,2*n))];fs.extend((j,(j+1)%n,(j+1)%n+n,j+n) for j in range(n))
 o=b.fast['fast_instance'](b.name('CurvedShutterBlade'),vs,fs,'ConchDarkMetal' if i%2 else 'ConchNickel',leaf,(0,0,0),smooth_faces=False);apply(o);leaves.append({'name':leaf.name,'home':a,'travel':profile_spec['travel']})
# Central resonator with seated red-tipped forks, visible through the grille when open.
hub=b.cyl('ResonatorHub',.088,.09,'ConchNickel',mouth,(0,0,-.132),None,96)
for i in range(3):
 y=(i-1)*.085
 b.beam('ForkRoot',(.01,y,-.132),(.12,y,-.173),.017,'ConchNickel',mouth)
 b.beam('RedForkTip',(.12,y,-.173),(.245,y,-.207),.014,'ConchRed',mouth)
# Short articulated cradle connected below the broad belly.
b.sleeve('CentralPedestal',.32,.24,.10,'ConchNickel',fixed,(.08,.18,.6125),96)
b.cyl('CradleNeck',.115,.435,'ConchNickel',fixed,(.08,.18,.88),None,64)
b.sphere('CradleSeat',.23,'ConchDarkMetal',fixed,(.03,.22,1.10),scale=(1.5,1,.56))
for x in [-.48,.48]:
 foot=Vector((x,-.30,.68));knee=Vector((x*.8,-.27,.95));top=Vector((x*.65,.04,1.29));direction=Vector((0,1,0))
 b.cube('SeatedCradleFoot',(.23,.16,.0275),'ConchNickel',fixed,(x,-.30,.57625),.009)
 b.sleeve('FootBearingHousing',.105,.033,.09,'ConchNickel',fixed,foot,64).rotation_euler=direction.to_track_quat('Z','Y').to_euler()
 b.cyl('FootCrossPin',.032,.13,'ConchBrass',fixed,foot,direction.to_track_quat('Z','Y'),48)
 b.beam('CradleLowerLink',foot,knee,.055,'ConchNickel',fixed);b.beam('CradleUpperLink',knee,top,.057,'ConchNickel',fixed)
 for p in [knee,top]:
  b.sleeve('ArticulatedEye',.078,.025,.09,'ConchDarkMetal',fixed,p,64).rotation_euler=direction.to_track_quat('Z','Y').to_euler();b.cyl('ArticulatedPin',.024,.105,'ConchNickel',fixed,p,direction.to_track_quat('Z','Y'),48)
# Tucked apex follows the new body center, not the rejected horn's endpoint.
apex=b.empty('IC11_Apex',body,center(1));apex.rotation_euler.y=-.35
b.sleeve('ApexCollar',.063,.022,.025,'ConchNickel',apex,(0,0,0),64);b.cyl('ApexStem',.026,.075,'ConchNickel',apex,(0,0,.035),None,48);b.sphere('ApexRedCap',.030,'ConchRed',apex,(0,0,.085))
b.upper.rotation_euler.z=-.55
for obj in b.col.objects:
 if obj.type=='MESH':apply(obj)
# Static anatomy gates first. Opening pose is only the iris, not a claim of full shell choreography.
scene.frame_start=1;scene.frame_end=91;scene.render.fps=30
for frame,amount in [(1,0.),(31,0.),(61,1.),(91,1.)]:
 for row in leaves:
  o=bpy.data.objects[row['name']];o.rotation_euler.z=row['home']-row['travel']*amount;o.keyframe_insert('rotation_euler',frame=frame)
for image in bpy.data.images:
 if image.source=='FILE' and image.filepath and not image.packed_file:image.filepath=bpy.path.relpath(bpy.path.abspath(image.filepath),start=str(TARGET.parent))
scene.frame_set(1);bpy.context.view_layer.update();bpy.ops.wm.save_as_mainfile(filepath=str(TARGET))
bpy.ops.object.select_all(action='DESELECT')
for obj in [b.root]+list(b.root.children_recursive):obj.select_set(True)
bpy.context.view_layer.objects.active=b.root;component=ROOT/'app/assets/collection/components/I_conch_r12.glb'
bpy.ops.export_scene.gltf(filepath=str(component),export_format='GLB',use_selection=True,export_apply=False,export_animations=False,export_extras=True)
result={'source':str(TARGET.relative_to(ROOT)),'source_sha256':sha(TARGET),'component':str(component.relative_to(ROOT)),'component_sha256':sha(component),'shells':shells,'leaves':leaves,'mouth':'IH1_Mouth','shape':'Broad rounded body with side-facing mouth and tucked spiral apex; no old I tube body loaded','reference':'concepts/collection_20260909/I_回声海螺.png','scope':'New independent closed-form reconstruction. Shell choreography, detailed mechanical load path, iris cam/pins, full clearance, main-App controls/music and final art acceptance remain.'}
(OUT/'build.json').write_text(json.dumps(result,indent=2)+'\n');print('I_CONCH_R12_BUILT',flush=True)
