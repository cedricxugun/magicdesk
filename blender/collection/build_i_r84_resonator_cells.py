"""R84: twelve physically formed resonator cells, morph diaphragms and real
opal conduits fitted to the current coiled liner. No whole-art acceptance."""
import bpy,bmesh,json,math,hashlib,sys
from pathlib import Path
from mathutils import Vector
R=Path(__file__).resolve().parents[2];sys.path.insert(0,str(Path(__file__).parent))
from i_r82_coil_surface import CoilSurface
import i_machined_geometry as P
VISIBLE='--concert-visible' in sys.argv
LARGE='--large-cells' in sys.argv or VISIBLE
OUT=R/'review/I_refinement/nautilus_reset_r82'/('chambers_r3' if VISIBLE else 'chambers_r2' if LARGE else 'chambers_r1')
OUT.mkdir(parents=True,exist_ok=True)
ART=R/'app/assets/collection/art/I/r84_chambers'
if LARGE:ART=ART/('r3' if VISIBLE else 'r2')
ART.mkdir(parents=True,exist_ok=True)
suffix='r3' if VISIBLE else 'r2' if LARGE else 'r1'
SRC=R/('blender/collection/I_r84_resonator_cells_'+suffix+'.blend');COMP=R/('app/assets/collection/components/I_r84_resonator_cells_'+suffix+'.glb')
assert not SRC.exists()and not COMP.exists()
parent=json.loads((R/'review/I_refinement/nautilus_reset_r82/chambers_r2/mechanism.json').read_text()) if LARGE else json.loads((R/'review/I_refinement/nautilus_reset_r82/music_interface_r1/installed_r5/build.json').read_text())
body=json.loads((R/'review/I_refinement/nautilus_reset_r82/mechanism_r9/build.json').read_text());surface=CoilSurface(body['shape_parameters'])
if VISIBLE:
 cells=sorted(json.loads((R/'review/I_refinement/nautilus_reset_r82/chambers_r2/visibility.json').read_text())['selected'],key=lambda c:c['t'])
elif LARGE:
 cells=[]
 for offset in [7.4,6.2,5.,3.8,2.6,1.4]:
  for u in [.80,2.30]:
   t=surface.T-offset;cells.append({'t':t,'u':u,'half_t':.28,'half_u':.40,'radius':surface.frame(t)[0],'visibility':None})
else:
 layout=json.loads((OUT/'visibility.json').read_text());cells=sorted(layout['selected'],key=lambda c:c['t'])
assert len(cells)==12
bpy.ops.wm.open_mainfile(filepath=str(R/parent['source']));scene=bpy.context.scene;scene.frame_set(1)
root=bpy.data.objects['R82_COIL_ROOT'];col=bpy.data.collections['R82_NEW_FORM'];P.configure(col)
def mat(n,c,metal,rough,emit=0):
 ma=bpy.data.materials.new(n);ma.use_nodes=True;bs=ma.node_tree.nodes.get('Principled BSDF')
 bs.inputs['Base Color'].default_value=(*c,1);bs.inputs['Metallic'].default_value=metal;bs.inputs['Roughness'].default_value=rough
 bs.inputs['Emission Color'].default_value=(1.,.55,.16,1);bs.inputs['Emission Strength'].default_value=emit
 return ma
nickel=mat('Collection_I84_Nickel',(.49,.45,.37),.93,.23)
graphite=mat('I84_Diaphragm_Titanium',(.023,.029,.036) if VISIBLE else (.055,.060,.067),.65 if VISIBLE else .46,.28 if VISIBLE else .34)
champagne=mat('I84_Centre_Champagne',(.48,.29,.115),.86,.22)
opal=mat('I84_OpalConduit',(.63,.49,.29),0,.24,1.4)
gasket=mat('I84_Gasket',(.018,.017,.014),0,.53)
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
   toolv.extend(point(c,.915*j/NR,math.tau*k/N,h)for k in range(N))
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
# Old minimal hoop guides were shape placeholders; the new framed cells replace them.
removed=[]
for o in list(bpy.data.objects):
 if o.name.startswith('R82_Acoustic_Rib_'):removed.append(o.name);bpy.data.objects.remove(o,do_unlink=True)
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
scene.frame_set(1);bpy.context.view_layer.update();bpy.ops.wm.save_as_mainfile(filepath=str(SRC),compress=True)
# Preserve source modifiers and morphs; bake only non-morph static export copies.
export_objects=[root,*root.children_recursive]
for o in export_objects:
 if o.type=='MESH' and o.modifiers and not o.data.shape_keys:
  ev=o.evaluated_get(bpy.context.evaluated_depsgraph_get());me=bpy.data.meshes.new_from_object(ev,preserve_all_data_layers=True,depsgraph=bpy.context.evaluated_depsgraph_get())
  o.modifiers.clear();o.data=me
curves=[o for o in export_objects if o.type=='CURVE']
if curves:
 bpy.ops.object.select_all(action='DESELECT')
 for o in curves:o.select_set(True)
 bpy.context.view_layer.objects.active=curves[0];bpy.ops.object.convert(target='MESH')
bpy.ops.object.select_all(action='DESELECT')
for o in [root,*root.children_recursive]:o.select_set(True)
bpy.context.view_layer.objects.active=root
bpy.ops.export_scene.gltf(filepath=str(COMP),export_format='GLB',use_selection=True,export_animations=False,export_morph=True,export_morph_normal=True,export_apply=False,export_tangents=True,export_extras=True)
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
chambers={'source_sha256':sha(SRC),'component_sha256':sha(COMP),'mask':'res://assets/collection/art/I/chamber_response_r35/conductor_mask.png','mask_sha256':sha(R/'app/assets/collection/art/I/chamber_response_r35/conductor_mask.png'),'cells':records,
 'illumination':{'open_floor':.15,'playing_floor':.38,'emission_gain':6.,'mask_cross_scale':1.,'packet_floor':.75,'spill_gain':.4,'light_color':[1.,.55,.16],'physical_conductors':True,'wavefront':True}}
(ART/'chamber_layout.json').write_text(json.dumps(chambers,indent=2)+'\n')
report={**parent,'source':SRC.relative_to(R).as_posix(),'source_sha256':sha(SRC),'component':COMP.relative_to(R).as_posix(),'component_sha256':sha(COMP),'parent_source':parent['source'],'chamber_response_layout':'res://'+(ART/'chamber_layout.json').relative_to(R/'app').as_posix(),'new_cells':records,'removed_shape_hoops':removed,'scope':'Twelve formed chamber candidates with true openings, restrained physical conduits and pressure/rebound morphs. Visibility-informed placement; full collision/art/export/runtime checks pending.'}
(OUT/'build.json').write_text(json.dumps(report,indent=2)+'\n')
# First renders are actual model, with an explicit diagnostic pressure pose.
bpy.ops.wm.open_mainfile(filepath=str(SRC));scene=bpy.context.scene
try:
 pref=bpy.context.preferences.addons['cycles'].preferences;pref.compute_device_type='CUDA';pref.get_devices()
 for v in pref.devices:v.use=v.type=='CUDA'
 scene.cycles.device='GPU'
except:pass
scene.cycles.samples=48;scene.render.resolution_x=1100;scene.render.resolution_y=1210;cam=scene.camera
for name,f in [('closed',1),('open',205)]:
 scene.frame_set(f)
 for cell in records:
  obj=bpy.data.objects[cell['diaphragm']];obj.data.shape_keys.key_blocks['MusicPressure'].value=.45 if f==205 else 0.
 cam.location=(-4,-7,3.65);cam.rotation_euler=(Vector((0,0,1.57))-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.ortho_scale=4.1
 scene.render.filepath=str(OUT/(name+'.png'));bpy.ops.render.render(write_still=True)
# Cutaway is explicitly diagnostic, never passed off as the normal open state.
for p in body['panels']:
 node=bpy.data.objects[p['node']]
 for child in node.children_recursive:
  if child.name.startswith(('R82_Porcelain','R82_Rolled_Edge','R82_Seal','R82_R3_Latch_','R82_R3_Enamel_Lock','R82_R3_Latch_Tip')):child.hide_render=True
scene.frame_set(205);scene.render.filepath=str(OUT/'internal_cutaway.png');bpy.ops.render.render(write_still=True)
print('R84_CHAMBERS_BUILT',len(records),flush=True)
