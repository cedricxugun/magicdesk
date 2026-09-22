"""Build a separate installed metal-to-metal dock candidate, never overwrite R76.

The original pedestal silhouette is retained. Its candidate copy receives only
six blind mounting bores under the adapter; this copy is not the active common base.
"""
import bpy,bmesh,json,hashlib,math,sys,array,collections
from pathlib import Path
from mathutils import Vector,Matrix
from mathutils.bvhtree import BVHTree
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(Path(__file__).parent))
import i_machined_geometry as h
import i_trunnion_support_geometry as g
import i_fitted_surface as fit
import i_dock_fitted_r79 as fitted
OUT=ROOT/'review/I_refinement/nautilus_r1/base_dock_r79';OUT.mkdir(parents=True,exist_ok=True)
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
s=json.loads((ROOT/'review/I_refinement/nautilus_r1/coupling_repair_r76/build.json').read_text())
assert sha(ROOT/s['source'])==s['source_sha256']
assert (ROOT/'production/I_refinement/nautilus_r1/base_connection_r78/docking_connection_study_r1.png').exists()
bpy.ops.wm.open_mainfile(filepath=str(ROOT/s['source']));bpy.context.scene.frame_set(1);bpy.context.view_layer.update()
body=bpy.data.objects['IN1_BodyRoot'];base=bpy.data.objects['BASE_FIXED'];deck=bpy.data.objects['IN1_DeckFoot'];skin=bpy.data.objects['IN1_PorcelainPanel_02'];core=bpy.data.objects['IN3_ContinuousThroat'];base_mesh=bpy.data.objects['BASE_FIXED_DisplayMesh']
removed={'IN1_LowSaddle'}|{f'IN1_FittedSaddle{kind}_{i}' for kind in ['Seat','Gasket'] for i in range(1,5)}
modified={deck.name,skin.name,core.name,base_mesh.name}
def fingerprint(o):
 m=o.data;m.calc_loop_triangles();d=hashlib.sha256()
 for c,p,w,k in [(m.vertices,'co',3,'f'),(m.loop_triangles,'vertices',3,'I'),(m.corner_normals,'vector',3,'f')]:
  a=array.array(k,[0])*(len(c)*w);c.foreach_get(p,a);d.update(a.tobytes())
 for uv in m.uv_layers:
  a=array.array('f',[0])*(len(uv.data)*2);uv.data.foreach_get('uv',a);d.update(a.tobytes())
 if m.shape_keys:
  for key in m.shape_keys.key_blocks:
   a=array.array('f',[0])*(len(key.data)*3);key.data.foreach_get('co',a);d.update(key.name.encode());d.update(a.tobytes())
 return [d.hexdigest(),[list(r) for r in o.matrix_world],[x.name if x else None for x in m.materials],[p.material_index for p in m.polygons]]
protected={o.name:fingerprint(o) for o in bpy.data.objects if o.type=='MESH' and o.name not in modified|removed}
def open_edges(o):
 # Imported GLB splits vertices at normals/UVs. Compare exact-coordinate
 # geometric boundary edges, rather than treating every split as a hole.
 m=o.data;m.calc_loop_triangles();v=[tuple(o.matrix_world@p.co) for p in m.vertices]
 edges=collections.Counter(tuple(sorted((v[t.vertices[k]],v[t.vertices[(k+1)%3]]))) for t in m.loop_triangles for k in range(3))
 return sorted((edge,count) for edge,count in edges.items() if count!=2 and edge[0]!=edge[1])
base_existing_open_edges=open_edges(base_mesh)
col=bpy.data.collections.new('I_BASE_DOCK_R79');bpy.context.scene.collection.children.link(col);h.configure(col)
root=h.empty('ID79_Dock',body);root.matrix_world=Matrix.Identity(4);g.configure(col,root)
refs={}
for original in [skin,core,base_mesh]:
 ref=original.copy();ref.data=original.data.copy();ref.name='ID79_Ref_'+original.name;col.objects.link(ref);ref.parent=None;ref.matrix_world=original.matrix_world.copy();refs[original.name]=ref
for name in removed:bpy.data.objects.remove(bpy.data.objects[name],do_unlink=True)
def world_geo(o):
 m=o.data;m.calc_loop_triangles();v=[o.matrix_world@p.co for p in m.vertices];f=[tuple(t.vertices) for t in m.loop_triangles];return v,f
def tree(o):
 v,f=world_geo(o);return BVHTree.FromPolygons(v,f,all_triangles=True)
def ring(cx,cy,r,n=64):return [(cx+r*math.cos(math.tau*i/n),cy+r*math.sin(math.tau*i/n)) for i in range(n)]
def plane_surface(reference,cx,cy,r,inside=False):
 return fitted.surface(reference,ring(cx,cy,r),inside=inside,z_limit=1.4)
def bolt(name,xy,bottom,head_z,r=.0055,head_r=.012):
 shank=h.cylinder(name,r,head_z-bottom,root,(*xy,(head_z+bottom)/2),'A_Nickel',bevel=.00015)
 head=h.screw(name+'_Head',root,(*xy,head_z+.0019),head_r);g.boolean(shank,head)
 return shank
def level(o,z):
 v,_=world_geo(o);return min(p.z for p in v) if z=='min' else max(p.z for p in v)
connections=[];stations=[];fasteners=[]
base_before_bounds=[[min(p[k] for p in world_geo(base_mesh)[0]) for k in range(3)],[max(p[k] for p in world_geo(base_mesh)[0]) for k in range(3)]]
# The new carrier plate is separated from the fixed adapter by a keyed, readable seam.
carrier=h.cylinder('ID79_Carrier',.425,.026,root,(.08,.13,.681),'A_Satin',bevel=.003)
seat_gasket=h.cylinder('ID79_DockSeatGasket',.415,.0005,root,(.08,.13,.66775),'A_Rubber',bevel=0)
# Three locating dowels; asymmetric X/Y pattern cannot seat in a wrong orientation.
for i,(x,y) in enumerate([(-.20,.14),(.32,.14),(.08,.39)]):
 h.drill(deck,.0102,.026,root,(x,y,.6615))
 pin=h.cylinder(f'ID79_Locator_{i}',.0097,.035,root,(x,y,.6675),'A_Bronze',bevel=.0004)
 h.drill(carrier,.0103,.06,root,(x,y,.69));h.drill(seat_gasket,.0105,.03,root,(x,y,.66775))
 connections.append({'type':'alignment','pin':pin.name,'fixed':deck.name,'moving':carrier.name,'axis':[0,0,1],'insertion':.012})
# Four independently releasable carrier bolts, distinct from pedestal fasteners.
for i,(x,y) in enumerate([(-.20,-.10),(.36,-.10),(-.20,.36),(.36,.36)]):
 h.drill(carrier,.0062,.075,root,(x,y,.69));h.drill(deck,.0060,.041,root,(x,y,.6475));h.drill(seat_gasket,.0064,.03,root,(x,y,.66775))
 washer=h.sleeve(f'ID79_LockWasher_{i}',.014,.0062,.0012,root,(x,y,.6947),'A_Bronze')
 b=bolt(f'ID79_LockBolt_{i}',(x,y),.633,.6955)
 fasteners.append({'id':b.name,'group':'carrier_release','washer':washer.name,'xy':[x,y],'bottom':.633,'release_axis':[0,0,1],'release_distance':.081})
# Six genuine blind bores in a candidate copy of the common mounting face.
survey=json.loads((OUT/'survey.json').read_text())
for i,row in enumerate(survey['deck_bolt_layers']):
 x,y=row['xy'];assert abs(row['layers'][0]-.5625)<1e-5 and row['layers'][1]<.51
 h.drill(base_mesh,.0061,.032,root,(x,y,.5505));h.drill(deck,.0063,.13,root,(x,y,.615))
 w=h.sleeve(f'ID79_BaseWasher_{i}',.014,.0064,.0014,root,(x,y,.6683),'A_Bronze')
 b=bolt(f'ID79_BaseBolt_{i}',(x,y),.5385,.6692,r=.0056)
 fasteners.append({'id':b.name,'group':'base_fixed','washer':w.name,'xy':[x,y],'bottom':.5385,'blind_floor':.5345,'original_base_top':row['layers'][0]})
if '--base-only' in sys.argv:
 after=open_edges(base_mesh)
 (OUT/'base_edge_diagnostic.json').write_text(json.dumps({'before':base_existing_open_edges,'after':after,'preserved':after==base_existing_open_edges},indent=2)+'\n')
 print('R79_BASE_EDGES',len(base_existing_open_edges),len(after),after==base_existing_open_edges,flush=True);sys.exit(0)
# A narrow machined relief makes the adapter's fixed part read as one flange.
groove=h.sleeve('ID79_AdapterGrooveTool',.615,.607,.0024,root,(.08,.13,.595),'A_Dark');g.boolean(deck,groove,'DIFFERENCE')
# Two real lower-housing hardpoints. Carrier loads pass through shell clearances,
# then into fitted exterior metal shoes and separate interior backing plates.
core_ref=refs[core.name];skin_ref=refs[skin.name]
for i,(cx,cy) in enumerate([(-.18,.10),(.18,.04)]):
 prefix=f'ID79_Stanchion{i}_'
 pts,polys,edges=plane_surface(core_ref,cx,cy,.095)
 sole=min(p.z for p in pts)-.034
 vv,ff=fit.extruded_patch(pts,polys,edges,-.0003,bottom_z=sole)
 shoe=g.own(prefix+'OuterShoe',vv,ff,root,'A_Satin')
 ip,ipoly,iedges=plane_surface(core_ref,cx,cy,.095,True)
 top=max(p.z for p in ip)+.023
 vv,ff=fit.extruded_patch(ip,ipoly,iedges,.0003,bottom_z=top)
 back=g.own(prefix+'InnerBacking',vv,ff,root,'A_Satin')
 # Straight load column with an actual centre relief, hidden length is intentional.
 tube=h.sleeve(prefix+'Column',.052,.024,sole-.715+.012,root,(cx,cy,(sole+.012+.715)/2),'A_Nickel')
 g.boolean(shoe,tube)
 # A broad curved cast foot: smoothed square sections taper toward the metal neck.
 vv=[];ff=[];steps=18;n=64
 for j in range(steps+1):
  t=j/steps;ease=t*t*(3-2*t);z=.687+(.806-.687)*t
  rx=.108+(.055-.108)*ease;ry=.132+(.055-.132)*ease
  for k in range(n):
   a=math.tau*k/n;c=math.cos(a);sn=math.sin(a);power=.63+.37*ease
   vv.append((cx+rx*math.copysign(abs(c)**power,c),cy+ry*math.copysign(abs(sn)**power,sn),z))
 for j in range(steps):
  for k in range(n):ff.append((j*n+k,j*n+(k+1)%n,(j+1)*n+(k+1)%n,(j+1)*n+k))
 ff.extend([tuple(range(n-1,-1,-1)),tuple(steps*n+k for k in range(n))])
 foot=g.own(prefix+'FootWeb',vv,ff,root,'A_Satin')
 for face in foot.data.polygons:face.use_smooth=len(face.vertices)==4
 g.boolean(shoe,foot);g.boolean(carrier,shoe)
 # Independent shell opening. Neither porcelain nor its lip takes the chassis load.
 h.drill(skin,.067,.7,root,(cx,cy,1.))
 lp,lpoly,ledge=plane_surface(skin_ref,cx,cy,.074)
 vv,ff=fit.extruded_patch(lp,lpoly,ledge,-.0006,bottom_offset=-.0048)
 lip=g.own(prefix+'PortRim',vv,ff,root,'A_Nickel');h.drill(lip,.0615,.7,root,(cx,cy,1.))
 # Skin and this trim must move together when that panel is removed.
 mat=lip.matrix_world.copy();lip.parent=skin.parent;lip.matrix_world=mat
 for j in range(4):
  a=math.pi/4+j*math.pi/2;x=cx+.074*math.cos(a);y=cy+.074*math.sin(a)
  hole_bottom=sole+.005;hole_top=top+.02
  for target in [carrier,core,back]:
   print('R79_BORE',i,j,target.name,flush=True)
   h.drill(target,.0045,hole_top-hole_bottom,root,(x,y,(hole_top+hole_bottom)/2))
  w=h.sleeve(prefix+f'CoreWasher_{j}',.0095,.0046,.0012,root,(x,y,top+.0007),'A_Bronze')
  b=bolt(prefix+f'CoreBolt_{j}',(x,y),sole+.012,top+.0016,r=.004,head_r=.008)
  # This fastening is inserted from above: cylindrical lower end remains captive
  # in the exterior shoe's counterbore, accessible after the metal cover is off.
  # Positive modeled fit is documented; fine hidden thread teeth are a later pass.
  fasteners.append({'id':b.name,'group':'housing_hardpoint','xy':[x,y],'shoe_bottom':sole,'backing_top':top,'hole_radius':.0045,'shaft_radius':.004})
 stations.append({'id':i,'center':[cx,cy],'carrier':carrier.name,'backing':back.name,'shoe_bottom':sole,'backing_top':top,'column_outer_radius':.052,'shell_hole_radius':.067,'lip_inner_radius':.0615,'shell_rim':lip.name})
 connections.append({'type':'housing_clamp','outer':carrier.name,'inner':back.name,'housing':core.name,'fasteners':[f'{prefix}CoreBolt_{j}' for j in range(4)]})
 print('R79_STATION',i,sole,top,flush=True)
# All original neighboring fields remain unchanged; modified source surfaces stay
# explicit in the report, rather than being hidden in a broad preservation claim.
for ref in refs.values():bpy.data.objects.remove(ref,do_unlink=True)
bpy.context.view_layer.update()
changed=[n for n,value in protected.items() if fingerprint(bpy.data.objects[n])!=value]
assert not changed,changed
new_names=[n for n in h.parts if n in bpy.data.objects]
checks=[]
for name in sorted(set(new_names)|modified):
 o=bpy.data.objects[name];bm=bmesh.new();bm.from_mesh(o.data)
 checks.append({'name':name,'nonmanifold':sum(not e.is_manifold for e in bm.edges),'signed_volume':bm.calc_volume(signed=True),'vertices':len(bm.verts)})
 bm.free()
base_after_bounds=[[min(p[k] for p in world_geo(base_mesh)[0]) for k in range(3)],[max(p[k] for p in world_geo(base_mesh)[0]) for k in range(3)]]
base_open_edges_preserved=base_existing_open_edges==open_edges(base_mesh)
proof={'parent_source_sha256':s['source_sha256'],'protected_meshes':len(protected),'protected_unchanged':not changed,'modified':sorted(modified),'removed':sorted(removed),'new_meshes':new_names,'solids':checks,'stations':stations,'connections':connections,'fasteners':fasteners,'original_base_bounds':base_before_bounds,'candidate_base_bounds':base_after_bounds,'base_existing_nonmanifold_edges':len(base_existing_open_edges),'base_existing_edge_signature_preserved':base_open_edges_preserved,'scope':'Independent assembled dock candidate. Detailed geometry, imports, surrounding contact, release motion and art still require separate checks. Base blind bores exist only in this candidate copy; current shared runtime base untouched. Existing merged pedestal boundaries are compared exactly rather than called watertight.'}
(OUT/'build_check.json').write_text(json.dumps(proof,indent=2)+'\n')
print('R79_SOLIDS',[(r['name'],r['nonmanifold']) for r in checks if r['nonmanifold']],flush=True)
assert all((r['nonmanifold']==0 or (r['name']==base_mesh.name and base_open_edges_preserved)) and r['signed_volume']>0 for r in checks), 'Open/invalid candidate solid'
assert base_before_bounds==base_after_bounds
source=ROOT/'blender/collection/I_base_dock_r79.blend';component=ROOT/'app/assets/collection/components/I_base_dock_r79.glb';base_component=ROOT/'app/assets/collection/components/I_base_dock_pedestal_r79.glb'
assert not source.exists() and not component.exists() and not base_component.exists()
bpy.ops.wm.save_as_mainfile(filepath=str(source),compress=True)
for target,path in [(body,component),(base,base_component)]:
 bpy.ops.object.select_all(action='DESELECT')
 for o in [target,*target.children_recursive]:o.select_set(True)
 bpy.context.view_layer.objects.active=target;bpy.ops.export_scene.gltf(filepath=str(path),export_format='GLB',use_selection=True,export_animations=False,export_morph=True,export_morph_normal=True,export_extras=True)
result={**s,'source':source.relative_to(ROOT).as_posix(),'source_sha256':sha(source),'component':component.relative_to(ROOT).as_posix(),'component_sha256':sha(component),'candidate_base_component':base_component.relative_to(ROOT).as_posix(),'candidate_base_sha256':sha(base_component),'base_dock':proof,'status':'independent_installed_dock_candidate_not_yet_verified'}
art=ROOT/'app/assets/collection/art/I/base_dock_r79';art.mkdir(parents=True,exist_ok=True)
layout=json.loads((ROOT/s['chamber_response_layout'].replace('res://','app/')).read_text())
layout.update(source_sha256=result['source_sha256'],component_sha256=result['component_sha256'])
(art/'chamber_layout.json').write_text(json.dumps(layout,indent=2)+'\n')
result['chamber_response_layout']='res://assets/collection/art/I/base_dock_r79/chamber_layout.json'
(OUT/'build.json').write_text(json.dumps(result,indent=2)+'\n');print('R79_SAVED',result['source_sha256'],flush=True)
