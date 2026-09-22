"""R89 graduated acoustic cells in the R88 mechanism, retaining the complete
Moonlight core, formed mouth return, rear supports and editable animation.
Cell construction is a frozen adaptation of the R84 authored morph/UV recipe.
"""
import bpy,bmesh,json,math,hashlib,sys,array
from pathlib import Path
from mathutils import Vector
R=Path(__file__).resolve().parents[2];sys.path.insert(0,str(Path(__file__).parent))
from i_r82_coil_surface import CoilSurface
import i_machined_geometry as P
revision='r3' if '--rim-clearance' in sys.argv else 'r2' if '--seated-rims' in sys.argv else 'r1'
BASE=R/'review/I_refinement/nautilus_reset_r82';OUT=BASE/f'chambers_r89/built_{revision}';OUT.mkdir(parents=True,exist_ok=True)
old=json.loads((BASE/'back_hardware_r88/built_r4/build.json').read_text());plan=json.loads((BASE/'chambers_r89/layout_selected.json').read_text());assert plan['source_sha256']==old['source_sha256']
assert hashlib.sha256((R/old['source']).read_bytes()).hexdigest()==old['source_sha256']
SRC=R/f'blender/collection/I_r89_graduated_resonators_{revision}.blend';COMP=R/f'app/assets/collection/components/I_r89_graduated_resonators_{revision}.glb';assert not SRC.exists() and not COMP.exists()
bpy.ops.wm.open_mainfile(filepath=str(R/old['source']));scene=bpy.context.scene;scene.frame_set(1);bpy.context.view_layer.update()
root=bpy.data.objects['R82_COIL_ROOT'];col=bpy.data.collections['R82_NEW_FORM'];liner=bpy.data.objects['R82_Acoustic_Chamber_Liner'];P.configure(col)
base_surface=CoilSurface(json.loads((BASE/'mechanism_r9/build.json').read_text())['shape_parameters'])
mouth_inverse=bpy.data.objects['IAM_Mouth'].matrix_world.inverted();VISIBLE=True
cells=plan['selected'];assert len(cells)==12
# Preserve every existing non-cell mesh and its closed world placement.
def fingerprint(o):
 h=hashlib.sha256();v=array.array('f',[0.])*(3*len(o.data.vertices));o.data.vertices.foreach_get('co',v);h.update(v.tobytes());idx=array.array('i',[0])*len(o.data.loops);o.data.loops.foreach_get('vertex_index',idx);h.update(idx.tobytes());h.update(str([tuple(row)for row in o.matrix_world]).encode());return h.hexdigest()
protected={o.name:fingerprint(o)for o in bpy.data.objects if o.type=='MESH' and not o.name.startswith('I84_Cell_') and o!=liner}
removed=[]
for o in list(bpy.data.objects):
 if o.name.startswith('I84_Cell_'):removed.append(o.name);bpy.data.objects.remove(o,do_unlink=True)
def create(name,vs,fs,parent=root):
 me=bpy.data.meshes.new(name+'Mesh');me.from_pydata(vs,[],fs);me.update();o=bpy.data.objects.new(name,me);col.objects.link(o);o.parent=parent
 bm=bmesh.new();bm.from_mesh(me);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(me);bm.free()
 return o
def boolean(obj,tool,operation='DIFFERENCE'):
 bpy.context.view_layer.update();bpy.context.view_layer.objects.active=obj
 m=obj.modifiers.new('Fitted receiver space','BOOLEAN');m.operation=operation;m.solver='EXACT';m.object=tool
 bpy.ops.object.modifier_move_to_index(modifier=m.name,index=0);bpy.ops.object.modifier_apply(modifier=m.name);bpy.data.objects.remove(tool,do_unlink=True)
def grid_shell(name,ta,tb,ua,ub,nt,nu,layer_point):
 vs=[];fs=[];stride=nu+1;count=(nt+1)*stride
 for side in [0,1]:
  for i in range(nt+1):
   t=ta+(tb-ta)*i/nt
   for j in range(nu+1):vs.append(layer_point(t,ua+(ub-ua)*j/nu,side))
 for side in [0,1]:
  for i in range(nt):
   for j in range(nu):
    k=side*count+i*stride+j;q=(k,k+stride,k+stride+1,k+1);fs.append(q if side==0 else q[::-1])
 edge=list(range(stride))+[i*stride+nu for i in range(1,nt+1)]+[nt*stride+j for j in range(nu-1,-1,-1)]+[i*stride for i in range(nt-1,0,-1)]
 for i,a in enumerate(edge):
  b=edge[(i+1)%len(edge)];fs.append((a,b,b+count,a+count))
 return create(name,vs,fs)
def smooth(a,b,x):
 v=max(0.,min(1.,(x-a)/(b-a)));return v*v*(3.-2.*v)

def formed_point(t,u,inset=None):
 if inset is None:inset=base_surface.wall(t)[0]
 p=base_surface.point(t,u,inset)
 if t>base_surface.T-.7:
  ref=base_surface.point(t,u);local=mouth_inverse@ref;angle=math.atan2(local.y,local.x)
  weight=smooth(-.42,-.26,angle)*(1.-smooth(.28,.48,angle))*smooth(.09,.15,local.z)*(1.-smooth(.255,.30,local.z))
  p+=base_surface.normal(t,u)*(.012*weight)
 return p
class FormedSurface:
 T=base_surface.T
 def point(self,t,u,inset=None):return formed_point(t,u,inset)
 def frame(self,t):return base_surface.frame(t)
 def wall(self,t):return base_surface.wall(t)
 def normal(self,t,u):
  h=.0001;dt=self.point(t+h,u)-self.point(t-h,u);du=self.point(t,u+h)-self.point(t,u-h);n=dt.cross(du).normalized()
  return n if n.dot(self.point(t,u)-self.frame(t)[3])>0 else -n
surface=FormedSurface()
new=grid_shell('I89_RestoredLiner',.01,surface.T,.06,math.pi-.06,600,96,lambda t,u,side:surface.point(t,u,surface.wall(t)[0]+surface.wall(t)[1]*side))
for ma in liner.data.materials:new.data.materials.append(ma)
liner.data=new.data;bpy.data.objects.remove(new,do_unlink=True)
for face in liner.data.polygons:face.use_smooth=True
for j in old['joints'][:1]:
 pivot=Vector(j['pivot']);axis=Vector(j['axis']);direction=Vector(j['slide_direction']);length=j['guide_length']
 for side in [-1,1]:
  start=pivot+axis*j['crosshead_span']*side-direction*(length+.05);depth=length+j['stroke']+.10
  bpy.ops.mesh.primitive_cylinder_add(vertices=96,radius=j['rod_radius']*2.25+.002,depth=depth);tool=bpy.context.object;tool.location=start+direction*depth/2;tool.rotation_mode='QUATERNION';tool.rotation_quaternion=direction.to_track_quat('Z','Y');boolean(liner,tool)
for c in cells:c['centre']=list(surface.point(c['t'],c['u']))
def mat(n,c,metal,rough,emit=0):
 ma=bpy.data.materials.new(n);ma.use_nodes=True;bs=ma.node_tree.nodes.get('Principled BSDF')
 bs.inputs['Base Color'].default_value=(*c,1);bs.inputs['Metallic'].default_value=metal;bs.inputs['Roughness'].default_value=rough
 bs.inputs['Emission Color'].default_value=(1.,.55,.16,1);bs.inputs['Emission Strength'].default_value=emit
 return ma
nickel=mat('Collection_I89_Nickel',(.57,.53,.45),.94,.27)
graphite=mat('I89_Diaphragm_Titanium',(.050,.061,.078),.68,.34)
champagne=mat('I89_Centre_Champagne',(.48,.29,.115),.86,.22)
opal=mat('I89_OpalConduit',(.63,.49,.29),0,.24,1.4)
gasket=mat('I89_Gasket',(.018,.017,.014),0,.53)
def create_mesh(n,vs,fs,material,uv=None):
 me=bpy.data.meshes.new(n+'Mesh');me.from_pydata(vs,[],fs);me.update();o=bpy.data.objects.new(n,me);col.objects.link(o);o.parent=root;me.materials.append(material)
 bm=bmesh.new();bm.from_mesh(me);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(me);bm.free()
 for p in me.polygons:p.use_smooth=True
 if uv is not None:
  for lname in ['SurfaceUV','ChamberConductorUV']:
   layer=me.uv_layers.new(name=lname)
   for p in me.polygons:
    values=[uv[me.loops[li].vertex_index]for li in p.loop_indices]
    wrap=max(v[0]for v in values)-min(v[0]for v in values)>.5
    for li,value in zip(p.loop_indices,values):layer.data[li].uv=(value[0]+1 if wrap and value[0]<.5 else value[0],value[1])
 return o
def chart(c,s,a):
 # Small skew gives the rim a growth-directed teardrop instead of a generic circle.
 return c['t']+c['half_t']*s*(math.cos(a)+.10*math.sin(a)**2),c['u']+c['half_u']*s*math.sin(a)
def point(c,s,a,height):
 t,u=chart(c,s,a);return surface.point(t,u)+surface.normal(t,u)*height
def annulus(name,c,profile,material,N=96):
 vs=[];fs=[];uv=[]
 for j,(s,h)in enumerate(profile):
  for k in range(N):
   a=math.tau*k/N;vs.append(point(c,s,a,h));uv.append((k/N,j/max(1,len(profile)-1)))
 for j in range(len(profile)):
  for k in range(N):fs.append((j*N+k,j*N+(k+1)%N,((j+1)%len(profile))*N+(k+1)%N,((j+1)%len(profile))*N+k))
 return create_mesh(name,vs,fs,material,uv)
# Prepare disjoint, curved through-cut volumes; all windows are actual openings.
toolv=[];toolf=[]
for c in cells:
 N=96;NR=8;layers=[]
 for h in [-.036,.026]:
  rings=[[len(toolv)]];toolv.append(point(c,0,0,h))
  for j in range(1,NR+1):
   rings.append(list(range(len(toolv),len(toolv)+N)))
   cut_radius=.950 if revision=='r3' and c is cells[0] else .936 if revision!='r1' else .915
   toolv.extend(point(c,cut_radius*j/NR,math.tau*k/N,h)for k in range(N))
  layers.append(rings)
 for layer,rings in enumerate(layers):
  for k in range(N):
   tri=(rings[0][0],rings[1][k],rings[1][(k+1)%N]);toolf.append(tri if layer==0 else tri[::-1])
  for j in range(1,NR):
   for k in range(N):
    q=(rings[j][k],rings[j+1][k],rings[j+1][(k+1)%N],rings[j][(k+1)%N]);toolf.append(q if layer==0 else q[::-1])
 for k in range(N):toolf.append((layers[0][-1][k],layers[0][-1][(k+1)%N],layers[1][-1][(k+1)%N],layers[1][-1][k]))
tool=create_mesh('I84_Window_CuttingTool',toolv,toolf,nickel)
liner=bpy.data.objects['R82_Acoustic_Chamber_Liner'];bpy.context.view_layer.objects.active=liner
mod=liner.modifiers.new('Twelve formed acoustic openings','BOOLEAN');mod.operation='DIFFERENCE';mod.solver='EXACT';mod.object=tool
bpy.ops.object.modifier_apply(modifier=mod.name);bpy.data.objects.remove(tool,do_unlink=True)
assert not liner.data.validate(verbose=True,clean_customdata=False),'Invalid liner after new openings'

# Preserve the verified formed receiver clearance, affecting the liner only.
profile=old['liner_receiver_profile'];sector=old['receiver_sector_clearance']
def profile_radius(z):
 for (za,ra),(zb,rb)in zip(profile,profile[1:]):
  if za<=z<=zb:return ra+(rb-ra)*(z-za)/(zb-za)
 raise ValueError(z)
depths=sorted(set([z for z,_ in profile]+[.245,.25,.255,.26,.265,.27,.3,.34,.38,.42,.435,.44,.445,.45]));vs=[];fs=[];N=384
for z in depths:
 for i in range(N):
  a=math.tau*i/N;angle=a if a<=math.pi else a-math.tau;r=profile_radius(z);aa,ab,ac,ad=sector['angle'];da,db,dc,dd=sector['depth'];weight=smooth(aa,ab,angle)*(1-smooth(ac,ad,angle))*smooth(da,db,z)*(1-smooth(dc,dd,z));r+=(min(r,sector['radius'])-r)*weight;vs.append((r*math.cos(a),r*math.sin(a),z))
for j in range(len(depths)-1):
 for i in range(N):fs.append((j*N+i,j*N+(i+1)%N,(j+1)*N+(i+1)%N,(j+1)*N+i))
fs +=[tuple(range(N-1,-1,-1)),tuple((len(depths)-1)*N+i for i in range(N))]
boolean(liner,create('I89_ReceiverEnvelope',vs,fs,parent=bpy.data.objects['IAM_Mouth']))
records=[]
for index,c in enumerate(cells):
 k=index+1;pre=f'I84_Cell_{k:02d}'
 frame=annulus(pre+'_Frame',c,[(1.10,.001),(1.10,.005),(1.065,.009),(.94,.009),(.885,.004),(.885,-.012),(.90,-.012),(.93,.001)],nickel)
 seal=annulus(pre+'_Seat',c,[(.887,-.0008),(.887,.0010),(.847,.0010),(.847,-.0008)],gasket)
 # Closed diaphragm volume: the outer ring is pinned in both morph directions.
 N=96;NR=24;vs=[];fs=[];uv=[];weights=[];normals=[];rings=[]
 for layer in [0,1]:
  layer_rings=[]
  for j in range(NR+1):
   s=j/NR*.853
   ids=[]
   count=1 if j==0 else N
   for q in range(count):
    a=math.tau*q/N;t,u=chart(c,s,a);normal=surface.normal(t,u)
    # Shallow pressed corrugations, not material noise or fabric bump.
    taper=max(0.,1-(s/.853)**2)
    groove=(.003+.004*c['radius']/.94 if VISIBLE else .0016)*math.sin(7*math.pi*s/.853)**2*taper if s>.24 else 0.
    height=(.006 if VISIBLE else .0018)*taper-groove-layer*.0018
    if revision!='r1' and s<.24:height+=.003*(1-(s/.24)**2)**2
    ids.append(len(vs));vs.append(surface.point(t,u)+normal*height)
    uv.append((.5+.5*s*math.cos(a)/.853,.5+.5*s*math.sin(a)/.853))
    weights.append(1. if s<.24 else max(0.,1-((s-.24)/(.853-.24))**2)**2)
    normals.append(normal)
   layer_rings.append(ids)
  rings.append(layer_rings)
 for layer,rr in enumerate(rings):
  for q in range(N):
   tri=(rr[0][0],rr[1][q],rr[1][(q+1)%N]);fs.append(tri if layer==0 else tri[::-1])
  for j in range(1,NR):
   for q in range(N):
    face=(rr[j][q],rr[j+1][q],rr[j+1][(q+1)%N],rr[j][(q+1)%N]);fs.append(face if layer==0 else face[::-1])
 for q in range(N):fs.append((rings[0][-1][q],rings[0][-1][(q+1)%N],rings[1][-1][(q+1)%N],rings[1][-1][q]))
 membrane=create_mesh(pre+'_Diaphragm',vs,fs,graphite,uv);membrane.data.materials.append(champagne)
 for poly in membrane.data.polygons:
  if all(weights[v]>.999 for v in poly.vertices):poly.material_index=1
 membrane.shape_key_add(name='Basis')
 stroke=.0045+.0045*(c['radius']/.94)
 for name,sign in [('MusicPressure',1),('MusicRebound',-1)]:
  key=membrane.shape_key_add(name=name)
  for j,p in enumerate(key.data):p.co=Vector(vs[j])+normals[j]*(stroke*weights[j]*sign)
 # Real rounded opal conduit, with a narrow metal channel behind it.
 channel=annulus(pre+'_LightChannel',c,[(1.032,.0076),(1.032,.0102),(.988,.0102),(.988,.0076)],champagne)
 vs=[];fs=[];uv=[];NL=128;NC=12
 for i in range(NL):
  a=math.tau*i/NL;t,u=chart(c,1.01,a);centre=point(c,1.01,a,.0104)
  tangent=(point(c,1.01,a+.001,.0104)-point(c,1.01,a-.001,.0104)).normalized()
  normal=surface.normal(t,u);side=tangent.cross(normal).normalized();radius=.0014+.0012*c['radius']
  for j in range(NC):
   b=math.tau*j/NC;vs.append(centre+side*(radius*math.cos(b))+normal*(radius*math.sin(b)));uv.append((i/NL,j/NC))
 for i in range(NL):
  for j in range(NC):fs.append((i*NC+j,((i+1)%NL)*NC+j,((i+1)%NL)*NC+(j+1)%NC,i*NC+(j+1)%NC))
 conduit=create_mesh(pre+'_Opal',vs,fs,opal,uv)
 # Four retained heads have real hex recesses and follow the local surface normal.
 for number,a in enumerate([.30,math.pi-.30,math.pi+.30,math.tau-.30]):
  t,u=chart(c,1.03,a);normal=surface.normal(t,u);loc=point(c,1.03,a,.0105)
  P.screw(pre+'_Retainer_'+str(number),root,loc,.0024+.0012*c['radius'],normal)
 band=2 if index<4 else 1 if index<8 else 0
 centre=surface.point(c['t'],c['u'])+surface.normal(c['t'],c['u'])*.023
 records.append({'frame':frame.name,'diaphragm':membrane.name,'cell_index':index,'uv2_layer':'ChamberConductorUV','band':band,'phase_offset':index/12,
 'light_position_godot':[centre.x,centre.z,-centre.y],'light_enabled':index in [2,6,10],
 'diffusers':[{'mesh':conduit.name,'runtime_mesh':conduit.name,'material':opal.name}],
 'membrane_motion':{'mesh':membrane.name,'pressure_key':'MusicPressure','rebound_key':'MusicRebound','max_world_stroke':stroke,'band':band,'natural_frequency_hz':3.4 if band==2 else 2.8 if band==1 else 2.2,'damping_ratio':.48},
 'surface_chart':c,'pinned_vertices':sum(w==0 for w in weights)})

scene.frame_set(1);bpy.context.view_layer.update()
changed=[name for name,value in protected.items()if fingerprint(bpy.data.objects[name])!=value];assert not changed,changed
bm=bmesh.new();bm.from_mesh(liner.data);bmesh.ops.dissolve_degenerate(bm,dist=1e-7,edges=list(bm.edges));bm.to_mesh(liner.data);topology={'nonmanifold':sum(not e.is_manifold for e in bm.edges),'volume':bm.calc_volume(signed=True)};bm.free();assert topology['nonmanifold']==0 and topology['volume']>0,topology
bpy.ops.wm.save_as_mainfile(filepath=str(SRC),compress=True)
for ob in root.children_recursive:
 if ob.type=='MESH' and ob.modifiers and not ob.data.shape_keys:
  ev=ob.evaluated_get(bpy.context.evaluated_depsgraph_get());me=bpy.data.meshes.new_from_object(ev,preserve_all_data_layers=True,depsgraph=bpy.context.evaluated_depsgraph_get());ob.modifiers.clear();ob.data=me
curves=[o for o in root.children_recursive if o.type=='CURVE']
if curves:
 bpy.ops.object.select_all(action='DESELECT')
 for o in curves:o.select_set(True)
 bpy.context.view_layer.objects.active=curves[0];bpy.ops.object.convert(target='MESH')
bpy.ops.object.select_all(action='DESELECT')
for o in [root,*root.children_recursive]:o.select_set(True)
bpy.context.view_layer.objects.active=root
bpy.ops.export_scene.gltf(filepath=str(COMP),export_format='GLB',use_selection=True,export_animations=False,export_morph=True,export_morph_normal=True,export_apply=False,export_tangents=True,export_extras=True)
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
ART=R/'app/assets/collection/art/I/r89_resonators'
if revision!='r1':ART=ART/revision
ART.mkdir(parents=True,exist_ok=True)
layout=json.loads((R/'app'/old['chamber_response_layout'].removeprefix('res://')).read_text());layout.update({'source_sha256':sha(SRC),'component_sha256':sha(COMP),'cells':records});layout['illumination'].update({'shadow_normal_bias':.005,'shadow_bias':.01})
(ART/'chamber_layout.json').write_text(json.dumps(layout,indent=2)+'\n')
report={**old,'source':SRC.relative_to(R).as_posix(),'source_sha256':sha(SRC),'component':COMP.relative_to(R).as_posix(),'component_sha256':sha(COMP),'parent_source':old['source'],'parent_source_sha256':old['source_sha256'],'chamber_response_layout':'res://'+(ART/'chamber_layout.json').relative_to(R/'app').as_posix(),'new_cells':records,'preserved_non_cell_meshes':len(protected),'preserved_meshes_changed':changed,'liner_topology':topology,'scope':'Twelve newly arranged graduated resonators, larger visible outer banks and smaller inner cells; true new openings and inherited formed mouth clearance. Existing non-cell geometry/world positions retained. Motion/contact/art/import checks pending.'}
(OUT/'build.json').write_text(json.dumps(report,indent=2)+'\n')
bpy.ops.wm.open_mainfile(filepath=str(SRC));scene=bpy.context.scene
try:
 pref=bpy.context.preferences.addons['cycles'].preferences;pref.compute_device_type='CUDA';pref.get_devices()
 for dv in pref.devices:dv.use=dv.type=='CUDA'
 scene.cycles.device='GPU'
except:pass
scene.cycles.samples=48;scene.render.resolution_x=1000;scene.render.resolution_y=1100;cam=scene.camera;cam.location=(-4,-7,3.65);cam.rotation_euler=(Vector((0,0,1.57))-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.ortho_scale=4.1
scene.frame_set(205);scene.render.filepath=str(OUT/'open.png');bpy.ops.render.render(write_still=True)
scene.frame_set(1);scene.render.filepath=str(OUT/'closed.png');bpy.ops.render.render(write_still=True)
print('R89_RESONATORS_BUILT',report['source_sha256'],flush=True)
