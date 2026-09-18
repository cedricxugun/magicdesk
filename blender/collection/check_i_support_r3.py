"""Check actual saved support contact planes and nearby hardware, preserving source."""
import bpy,json,hashlib
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree
ROOT=Path(__file__).resolve().parents[2];OUT=ROOT/'review/I_refinement/support_r3'
info=json.loads((OUT/'build.json').read_text());source=ROOT/info['source']
bpy.ops.wm.open_mainfile(filepath=str(source));scene=bpy.context.scene;root=bpy.data.objects['IH1_MODULE']
def geometry(obj):
    ev=obj.evaluated_get(bpy.context.evaluated_depsgraph_get());mesh=ev.to_mesh();mesh.calc_loop_triangles()
    points=[obj.matrix_world@v.co for v in mesh.vertices];faces=[tuple(t.vertices) for t in mesh.loop_triangles];ev.to_mesh_clear()
    return points,faces
def tree(obj):
    points,faces=geometry(obj);return BVHTree.FromPolygons(points,faces,all_triangles=True)
def zrange(name):
    points,_=geometry(bpy.data.objects[name]);return min(v.z for v in points),max(v.z for v in points)
new=[o for o in bpy.data.collections['I_SUPPORT_R3'].objects if o.type=='MESH']
old=[o for o in root.children_recursive if o not in new and o.type in ['MESH','CURVE']]
scene.frame_set(1)
socket=bpy.data.objects['IS3_ColumnSocket'];column=next(o for o in old if 'CentralBearingColumn' in o.name)
points,_=geometry(column);local=[socket.matrix_world.inverted()@p for p in points]
seat_error=abs(min(p.z for p in local));shaft_radius=max((p.x*p.x+p.y*p.y)**.5 for p in local if p.z<.121)
column_fit=seat_error<.00001 and shaft_radius<.1312
issues=[];contacts=[];tested=0
for frame in [1,88]:
    scene.frame_set(frame);bpy.context.view_layer.update()
    trees={o.name:tree(o) for o in new+old}
    for a in new:
        for b in old:
            count=len(trees[a.name].overlap(trees[b.name]));tested+=1
            if not count:continue
            row={'frame':frame,'new':a.name,'existing':b.name,'triangles':count}
            seated=('PedestalGroundPad' in a.name and 'MountFoot' in b.name) or ('AxleHexCap' in a.name and 'RedPin' in b.name) or (a.name==info['column_socket'] and b==column and column_fit)
            (contacts if seated else issues).append(row)
scene.frame_set(1)
planes={'pedestal_pad':zrange(info['pedestal_pad']),'column_socket':zrange(info['column_socket'])}
for foot in info['feet']:
    planes[foot['group']+'_gasket']=zrange(foot['gasket']);planes[foot['group']+'_sole']=zrange(foot['sole'])
ground_error=max(abs(v[0]-info['ground']) for k,v in planes.items() if 'gasket' in k or k=='pedestal_pad')
join_error=max(abs(planes[foot['group']+'_gasket'][1]-planes[foot['group']+'_sole'][0]) for foot in info['feet'])
base=json.loads((OUT/'actual_base_triangles.json').read_text());assert base['source_sha256']==info['base_mesh_sha256']
vertices=base['triangle_vertices'];base_faces=[(i,i+1,i+2) for i in range(0,len(vertices),3)];base_tree=BVHTree.FromPolygons(vertices,base_faces,all_triangles=True)
base_issues=[];base_contacts=[]
for obj in new:
    hits=tree(obj).overlap(base_tree)
    if not hits:continue
    contact_faces=sorted(set(j for _,j in hits));points,_=geometry(obj)
    flat_contact=min(p.z for p in points)>=info['ground']-.00001 and all(all(abs(vertices[k][2]-info['ground'])<.00001 for k in base_faces[j]) for j in contact_faces)
    (base_contacts if flat_contact else base_issues).append({'name':obj.name,'base_triangles':len(contact_faces)})
report={'source_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),'passed':not issues and ground_error<.00002 and join_error<.00002 and column_fit,'column_stop_plane_error':seat_error,'shaft_max_radius_in_socket':shaft_radius,'socket_inside_radius':.1312,'ground_plane_error':ground_error,'gasket_to_sole_error':join_error,'planes':planes,'tested_pairs':tested,'unexpected_surface_intersections':issues,'declared_seating_contacts':contacts,'scope':'New support meshes versus existing component at rest/charged, actual ground planes/gasket seats and column cavity fit. Declared pad/old-foot, axial end-cap/pin and measured column-stop contacts retained. New-to-new bolt/casting interfaces and shared base full surface scan not covered.'}
(OUT/'support_check.json').write_text(json.dumps(report,indent=2)+'\n');print('I_SUPPORT_CHECK',report['passed'],'issues',len(issues),'ground',ground_error,'first',issues[:5],flush=True)
report['shared_base_intersections']=base_issues;report['shared_base_seating']=base_contacts;report['passed']=report['passed'] and not base_issues
report['scope']=report['scope'].replace(' and shared base full surface scan','')+' Actual app shared-base triangle surface intersections checked separately; flat ground contact admitted only with no vertices below the ground plane.'
(OUT/'support_check.json').write_text(json.dumps(report,indent=2)+'\n');print('I_ACTUAL_BASE_CONTACT',base_issues,base_contacts,flush=True)
if not report['passed']:raise SystemExit(1)
