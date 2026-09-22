"""Replace wire-like fixed hinge braces with forged supports, external
collars and actual blind-fastened curved feet. Keeps all working axes/poses."""
import bpy,bmesh,json,math,hashlib,sys
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree
R=Path(__file__).resolve().parents[2];sys.path.insert(0,str(Path(__file__).parent))
from i_r82_coil_surface import CoilSurface
import i_machined_geometry as P
revision='r4' if '--relieved' in sys.argv else 'r3' if '--stable-sweep' in sys.argv else 'r2' if '--seated' in sys.argv else 'r1'
seated=revision!='r1'
stable=revision in ['r3','r4']
BASE=R/'review/I_refinement/nautilus_reset_r82';OUT=BASE/('back_hardware_r88/built_'+revision);OUT.mkdir(parents=True,exist_ok=True)
old=json.loads((BASE/'oblique_hinge_r87/build.json').read_text())
SRC=R/f'blender/collection/I_r88_forged_supports_{revision}.blend';COMP=R/f'app/assets/collection/components/I_r88_forged_supports_{revision}.glb';assert not SRC.exists() and not COMP.exists()
bpy.ops.wm.open_mainfile(filepath=str(R/old['source']));scene=bpy.context.scene;scene.frame_set(1);bpy.context.view_layer.update()
root=bpy.data.objects['R82_COIL_ROOT'];col=bpy.data.collections['R82_NEW_FORM'];P.configure(col)
surface=CoilSurface(json.loads((BASE/'mechanism_r9/build.json').read_text())['shape_parameters'])
def bvh(o):
 ev=o.evaluated_get(bpy.context.evaluated_depsgraph_get());me=ev.to_mesh();me.calc_loop_triangles();v=[ev.matrix_world@q.co for q in me.vertices];t=[tuple(x.vertices)for x in me.loop_triangles];ev.to_mesh_clear();return BVHTree.FromPolygons(v,t,all_triangles=True)
old_intersections=[]
for f in [1,110,175]:
 scene.frame_set(f);bpy.context.view_layer.update()
 for j in old['joints'][1:]:
  k=j['id']
  for side in [-1,1]:
   rod=bpy.data.objects[f'I85_Rod_{k}_{side}'];rb=bvh(rod)
   for stem in ['SupportA','SupportB']:
    name=f'I85_{stem}_{k}_{side}';n=len(rb.overlap(bvh(bpy.data.objects[name])))
    if n:old_intersections.append({'frame':f,'rod':rod.name,'support':name,'triangle_pairs':n})
print('R88_OLD_ROD_SUPPORT_CONTACTS',old_intersections,flush=True)
scene.frame_set(1);bpy.context.view_layer.update()
for name,color,rough in [('R88_Nickel',(.54,.52,.47),.245),('R88_Bronze',(.46,.285,.12),.28)]:
 ma=bpy.data.materials.new('Collection_'+name);ma.use_nodes=True;bs=ma.node_tree.nodes['Principled BSDF'];bs.inputs['Base Color'].default_value=(*color,1);bs.inputs['Metallic'].default_value=.96;bs.inputs['Roughness'].default_value=rough
def mesh(name,vs,fs,material):
 me=bpy.data.meshes.new(name+'Mesh');me.from_pydata(vs,[],fs);me.update();o=bpy.data.objects.new(name,me);col.objects.link(o);o.parent=root;me.materials.append(bpy.data.materials['Collection_'+material])
 bm=bmesh.new();bm.from_mesh(me);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(me);bm.free()
 for f in me.polygons:f.use_smooth=True
 return o
def cut(o,tool,operation='DIFFERENCE',solver='EXACT'):
 bpy.context.view_layer.update();bpy.context.view_layer.objects.active=o;m=o.modifiers.new('Fitted manufacture','BOOLEAN');m.operation=operation;m.solver=solver;m.object=tool
 bpy.ops.object.modifier_move_to_index(modifier=m.name,index=0);bpy.ops.object.modifier_apply(modifier=m.name);bpy.data.objects.remove(tool,do_unlink=True)
def rounded_profile(w,h,r):
 result=[]
 for x,y,start in [(w-r,h-r,0),(-w+r,h-r,90),(-w+r,-h+r,180),(w-r,-h+r,270)]:
  for i in range(5):
   a=math.radians(start+90*i/4);result.append((x+r*math.cos(a),y+r*math.sin(a)))
 return result
def forged(name,a,b,n,q,width_axis,radius):
 handle=min(.012,(b-a).length*.25) if stable else .020
 controls=[a,a+n*handle,b+q*handle,b];steps=36;vs=[];fs=[];N=20;last_tangent=None;last_x=None
 def position(t):return controls[0]*(1-t)**3+controls[1]*3*(1-t)**2*t+controls[2]*3*(1-t)*t*t+controls[3]*t**3
 for i in range(steps+1):
  t=i/steps;centre=position(t);v=(position(min(1,t+.001))-position(max(0,t-.001))).normalized()
  if stable and last_tangent is not None:
   x=last_tangent.rotation_difference(v)@last_x;x=(x-v*x.dot(v)).normalized()
  else:x=(width_axis-v*width_axis.dot(v)).normalized()
  y=v.cross(x).normalized();last_tangent=v.copy();last_x=x.copy()
  w=radius*(1.45-.20*t);h=radius*(.68+.08*t);edge=radius*.20
  vs.extend(centre+x*px+y*py for px,py in rounded_profile(w,h,edge))
 for i in range(steps):
  for k in range(N):fs.append((i*N+k,i*N+(k+1)%N,(i+1)*N+(k+1)%N,(i+1)*N+k))
 fs +=[tuple(range(N-1,-1,-1)),tuple(steps*N+i for i in range(N))]
 ob=mesh(name,vs,[] if stable else fs,'R88_Nickel')
 if stable:
  # A compact cast support uses a solid convex envelope. The former tight
  # rectangular sweep folded across its own foot cap at two stations.
  bm=bmesh.new();bm.from_mesh(ob.data);hull=bmesh.ops.convex_hull(bm,input=list(bm.verts),use_existing_faces=False)
  unused=[x for x in hull['geom_interior']+hull['geom_unused'] if isinstance(x,bmesh.types.BMVert) and x.is_valid]
  if unused:bmesh.ops.delete(bm,geom=list(set(unused)),context='VERTS')
  bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(ob.data);bm.free()
  # The sampled rounded sections provide the edge radii; beveling all tiny
  # triangulated hull edges introduces near-degenerate overlapping faces.
  for face in ob.data.polygons:face.use_smooth=True
  ob.data.calc_loop_triangles();tri=[tuple(x.vertices)for x in ob.data.loop_triangles];tree=BVHTree.FromPolygons([v.co for v in ob.data.vertices],tri,all_triangles=True)
  bad=[(i,j)for i,j in tree.overlap(tree) if i<j and not set(tri[i])&set(tri[j])]
  assert not bad,(name,'sweep self-intersections',bad[:12])
 return ob
def rear_clearance_tool(tp,up):
 nt=36;nu=36;stride=nu+1;count=(nt+1)*stride;vs=[];fs=[]
 for h in [-.045,.0005]:
  for i in range(nt+1):
   t=tp-.30+.60*i/nt
   for j in range(nu+1):
    u=up-.30+.60*j/nu;vs.append(surface.point(t,u,.016)+surface.normal(t,u)*h)
 for side in [0,1]:
  for i in range(nt):
   for j in range(nu):
    a=side*count+i*stride+j;q=(a,a+stride,a+stride+1,a+1);fs.append(q if side==0 else q[::-1])
 edge=list(range(stride))+[i*stride+nu for i in range(1,nt+1)]+[nt*stride+j for j in range(nu-1,-1,-1)]+[i*stride for i in range(nt-1,0,-1)]
 for i,a in enumerate(edge):
  b=edge[(i+1)%len(edge)];fs.append((a,b,b+count,a+count))
 return mesh('R88_FormedRearReliefTool',vs,fs,'R88_Nickel')
removed=[];rows=[];cut_vs=[];cut_fs=[];changed=[];foot_witnesses={}
for p,j in zip(old['panels'][1:],old['joints'][1:]):
 k=p['id'];tm=(p['ta']+p['tb'])/2;axis=Vector(p['axis']);direction=Vector(j['slide_direction']);pivot=Vector(p['pivot']);length=j['guide_length'];radius=j['rod_radius'];span=j['crosshead_span']
 for side in [-1,1]:
  for stem in ['SupportA','SupportB']:
   o=bpy.data.objects[f'I85_{stem}_{k}_{side}'];removed.append(o.name);bpy.data.objects.remove(o,do_unlink=True)
  tp=tm+side*.10;up=math.tau-.24;normal=surface.normal(tp,up);foot=surface.point(tp,up,.016)
  guide_axis=pivot+axis*span*side-direction*(length-.014)
  q=foot-guide_axis;q=(q-direction*q.dot(direction)).normalized()
  collar_outer=radius*2.95;collar_inner=radius*2.25+.0003
  collar=P.sleeve(f'I88_OuterCollar_{k}_{side}',collar_outer,radius*2.60 if seated else collar_inner,.014,root,guide_axis,'R88_Nickel' if seated else 'R88_Bronze',direction)
  # Attach to the outer collar, never through the linear rod's bore.
  start=foot+normal*(.004 if seated else .005+radius*.8);end=guide_axis+q*(collar_outer+radius*(-.30 if seated else .40))
  beam=forged(f'I88_ForgedSupport_{k}_{side}',start,end,normal,q,axis,radius)
  if revision=='r4' and (k,side) in [(2,1),(3,1)]:
   bore=P.cylinder('R88_BearingFinishBore',radius*2.60+.00003,.018,root,guide_axis,'R88_Nickel',direction,0);cut(beam,bore,solver='MANIFOLD')
  shoe=bpy.data.objects[f'I85_FixedShoe_{k}_{side}']
  if stable:foot_witnesses[shoe.name]=[shoe.matrix_world@shoe.data.vertices[i].co for i in [0,12,156,168,169,181,325,337]]
  bearing=None
  if seated:
   cut(shoe,beam,'UNION');cut(shoe,collar,'UNION');shoe.data.materials.clear();shoe.data.materials.append(bpy.data.materials['Collection_R88_Nickel'])
   if revision=='r4':
    if (k,side) in [(5,1),(6,1)]:cut(shoe,rear_clearance_tool(tp,up))
   bearing=P.sleeve(f'I88_BronzeBearing_{k}_{side}',radius*2.60-.00015,collar_inner,.014,root,guide_axis,'R88_Bronze',direction)
   changed.extend([shoe,bearing])
  else:changed.extend([collar,beam,shoe])
  bolts=[]
  for offset in [-.040,.040]:
   bt=tp+offset;bn=surface.normal(bt,up);bp=surface.point(bt,up,.016);index=0 if offset<0 else 1
   tool=P.cylinder('R88_FootBoreTool',.0021,.026,root,bp-bn*.001,'R88_Nickel',bn,0)
   bpy.context.view_layer.update();me=tool.data;start_index=len(cut_vs);cut_vs.extend(tool.matrix_world@v.co for v in me.vertices);cut_fs.extend(tuple(start_index+i for i in face.vertices) for face in me.polygons)
   cut(shoe,tool)
   if seated:
    counter=P.cylinder('R88_FlatHeadSeat',.0038,.009,root,bp+bn*.0085,'R88_Nickel',bn,0);cut(shoe,counter)
   head=P.screw(f'I88_FootBolt_{k}_{side}_{index}',root,bp+bn*(.006 if seated else .007),r=.0036,axis=bn)
   stem=P.cylinder(f'I88_FootBoltStem_{k}_{side}_{index}',.0018,.016,root,bp-bn*.003,'R88_Nickel',bn,.00015)
   if seated:cut(head,stem,'UNION');bolts.append(head.name);changed.append(head)
   else:bolts.extend([head.name,stem.name]);changed.extend([head,stem])
  end_cap=None
  if stable:
   guide_end=pivot+axis*span*side-direction*length
   end_cap=P.screw(f'I88_GuideEndCap_{k}_{side}',root,guide_end-direction*.002,r=radius*2.21,axis=-direction)
   plug=P.cylinder('R88_EndPlugTool',radius+.001,.0035,root,guide_end+direction*.00125,'R88_Nickel',direction,.00015);cut(end_cap,plug,'UNION');changed.append(end_cap)
  rows.append({'id':k,'side':side,'support':shoe.name if seated else beam.name,'collar':shoe.name if seated else collar.name,'bearing':bearing.name if bearing else None,'end_cap':end_cap.name if end_cap else None,'shoe':shoe.name,'guide':f'I85_Guide_{k}_{side}','rod':f'I85_Rod_{k}_{side}','guide_axis_point':list(guide_axis),'collar_inner':collar_inner,'collar_outer':collar_outer,'fasteners':bolts})
rear=bpy.data.objects['R82_Fixed_Rear_Keel'];tool=mesh('R88_RearBlindHoleTool',cut_vs,cut_fs,'R88_Nickel');cut(rear,tool);changed.append(rear)
validation=[]
for o in changed:
 repair=o.data.validate(verbose=True,clean_customdata=False);bm=bmesh.new();bm.from_mesh(o.data)
 initial_bad=sum(not e.is_manifold for e in bm.edges)
 if revision=='r4' and initial_bad:
  bmesh.ops.dissolve_degenerate(bm,dist=1e-7,edges=list(bm.edges));bm.to_mesh(o.data)
  remaining=[e for e in bm.edges if not e.is_manifold]
  if remaining:print('R88_EDGE_DIAG',o.name,[{'length':e.calc_length(),'faces':[f.calc_area() for f in e.link_faces],'points':[list(v.co)for v in e.verts]}for e in remaining[:8]],flush=True)
 unseen=set(bm.verts);components=0
 while unseen:
  components+=1;stack=[unseen.pop()]
  while stack:
   v=stack.pop()
   for edge in v.link_edges:
    other=edge.other_vert(v)
    if other in unseen:unseen.remove(other);stack.append(other)
 row={'name':o.name,'automatic_repair':repair,'initial_nonmanifold':initial_bad,'nonmanifold':sum(not e.is_manifold for e in bm.edges),'volume':bm.calc_volume(signed=True),'components':components};bm.free();validation.append(row)
assert all(not x['automatic_repair'] and x['nonmanifold']==0 and x['volume']>0 for x in validation),validation
if seated:assert all(x['components']==1 for x in validation),validation
foot_errors=[]
for name,points in foot_witnesses.items():
 tree=bvh(bpy.data.objects[name]);distances=[tree.find_nearest(p)[3]for p in points];foot_errors.append({'name':name,'corner_samples':8,'maximum_distance':max(distances)})
assert all(x['maximum_distance']<1e-5 for x in foot_errors),foot_errors
if stable:
 bpy.data.materials['Collection_R88_Nickel'].node_tree.nodes['Principled BSDF'].inputs['Roughness'].default_value=.30
 ma=rear.data.materials[0].copy();ma.name='R88_Burnished_Rear_Nickel';bs=ma.node_tree.nodes['Principled BSDF'];assert not bs.inputs['Roughness'].is_linked
 bs.inputs['Base Color'].default_value=(.52,.515,.49,1);bs.inputs['Metallic'].default_value=.98;bs.inputs['Roughness'].default_value=.38;rear.data.materials[0]=ma
scene.frame_set(1);bpy.ops.wm.save_as_mainfile(filepath=str(SRC),compress=True)
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
ART=R/'app/assets/collection/art/I/r88_forged_supports'
if seated:ART=ART/revision
ART.mkdir(parents=True,exist_ok=True)
layout=json.loads((R/'app'/old['chamber_response_layout'].removeprefix('res://')).read_text());layout['source_sha256']=sha(SRC);layout['component_sha256']=sha(COMP);(ART/'chamber_layout.json').write_text(json.dumps(layout,indent=2)+'\n')
report={**old,'source':SRC.relative_to(R).as_posix(),'source_sha256':sha(SRC),'component':COMP.relative_to(R).as_posix(),'component_sha256':sha(COMP),'parent_source':old['source'],'forged_supports':rows,'removed_wire_supports':removed,'former_rod_contacts':old_intersections,'support_topology':validation,'foot_corner_preservation':foot_errors,'chamber_response_layout':'res://'+(ART/'chamber_layout.json').relative_to(R/'app').as_posix(),'scope':'Forged curved supports with external annular collars and twenty real blind-fastened foot screws. Working motion and functional core retained. Complete clearance, joining and art review pending.'}
(OUT/'build.json').write_text(json.dumps(report,indent=2)+'\n')
bpy.ops.wm.open_mainfile(filepath=str(SRC));scene=bpy.context.scene;scene.frame_set(205)
try:
 pref=bpy.context.preferences.addons['cycles'].preferences;pref.compute_device_type='CUDA';pref.get_devices()
 for dv in pref.devices:dv.use=dv.type=='CUDA'
 scene.cycles.device='GPU'
except:pass
scene.cycles.samples=48;scene.render.resolution_x=1000;scene.render.resolution_y=1100
cam=scene.camera;cam.location=(4,7,3.65);cam.rotation_euler=(Vector((0,0,1.57))-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.ortho_scale=4.1
scene.render.filepath=str(OUT/'rear_open.png');bpy.ops.render.render(write_still=True)
print('R88_FORGED_BUILT',report['source_sha256'],flush=True)
