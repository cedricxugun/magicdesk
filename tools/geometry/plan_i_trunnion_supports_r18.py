"""Plan real-size support envelopes in each existing trunnion's hinge plane."""
import bpy,json,hashlib,math,itertools,sys
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree
ROOT=Path(__file__).resolve().parents[2];report=ROOT/'review/I_refinement/nautilus_r1/chamber04_r15/build.json';s=json.loads(report.read_text());assert hashlib.sha256((ROOT/s['source']).read_bytes()).hexdigest()==s['source_sha256'];bpy.ops.wm.open_mainfile(filepath=str(ROOT/s['source']));scene=bpy.context.scene;scene.frame_set(1);bpy.context.view_layer.update();body=bpy.data.objects['IN1_BodyRoot']
deck=bpy.data.objects['IN1_DeckFoot'];center=deck.matrix_world.translation.copy();deck_top=max((deck.matrix_world@v.co).z for v in deck.data.vertices);foot_z=deck_top+.060
def geometry(o):
    o.data.calc_loop_triangles();v=[o.matrix_world@p.co for p in o.data.vertices];f=[tuple(t.vertices) for t in o.data.loop_triangles if min(v[i].z for i in t.vertices)<1.75 and max(v[i].z for i in t.vertices)>.64]
    return BVHTree.FromPolygons(v,f,all_triangles=True) if f else None
fixed_skins={r['mesh'] for r in s['form_panels'] if not r['active']}|{o.name for o in body.children_recursive if o.name.startswith('IN1_FixedRearShell_')}|{'IN1_FixedMouthCheek05'}
obstacles={o.name:geometry(o) for o in body.children_recursive if o.type=='MESH'};obstacles={n:t for n,t in obstacles.items() if t};mouth={}
for frame in [1,181]:
    scene.frame_set(frame);bpy.context.view_layer.update();mouth[frame]={o.name:geometry(o) for o in bpy.data.objects if o.type=='MESH' and o.name.startswith('IAM_')};mouth[frame]={n:t for n,t in mouth[frame].items() if t}
scene.frame_set(1);bpy.context.view_layer.update()
def basis(axis):
    n=Vector(axis).normalized();u=n.cross(Vector((0,0,1)))
    if u.length<.1:u=n.cross(Vector((1,0,0)))
    u.normalize();return u,n.cross(u),n
def cylinder(a,b,r0,r1=None):
    a,b=Vector(a),Vector(b);u,v,n=basis(b-a);count=32;r1=r0 if r1 is None else r1;points=[];faces=[]
    for origin,r in [(a,r0),(b,r1)]:points.extend(origin+(u*math.cos(k*math.tau/count)+v*math.sin(k*math.tau/count))*r for k in range(count))
    faces=[(k,(k+1)%count,count+(k+1)%count,count+k) for k in range(count)];faces.extend([tuple(range(count-1,-1,-1)),tuple(range(count,count*2))]);return points,faces
def sleeve(origin,axis,outer,inner,depth):
    u,v,n=basis(axis);count=32;points=[];faces=[]
    for r,z in [(outer,-depth/2),(outer,depth/2),(inner,depth/2),(inner,-depth/2)]:points.extend(origin+n*z+(u*math.cos(k*math.tau/count)+v*math.sin(k*math.tau/count))*r for k in range(count))
    for j in range(4):faces.extend((j*count+k,j*count+(k+1)%count,((j+1)%4)*count+(k+1)%count,((j+1)%4)*count+k) for k in range(count))
    return points,faces
def envelope(top,foot,axis):
    delta=foot-top;direction=delta.normalized();pieces=[sleeve(top,axis,.0145,.00435,.0184),cylinder(top+direction*.0105,top+direction*.038,.0098),cylinder(top+direction*.038,top+direction*.080,.0098,.028),cylinder(top+direction*.078,foot-direction*.046,.028),cylinder(foot-direction*.062,foot-direction*.013,.028,.015),sleeve(foot,axis,.024,.0061,.030),cylinder(foot-Vector((0,0,.045)),foot,.026)]
    radial=Vector((foot.x-center.x,foot.y-center.y,0)).normalized();tangent=Vector((-radial.y,radial.x,0));points=[];count=48
    for z in [deck_top+.0002,deck_top+.0182]:points.extend(Vector((foot.x,foot.y,z))+radial*(.038*math.cos(k*math.tau/count))+tangent*(.068*math.sin(k*math.tau/count)) for k in range(count))
    faces=[(k,(k+1)%count,count+(k+1)%count,count+k) for k in range(count)];faces.extend([tuple(range(count-1,-1,-1)),tuple(range(count,count*2))]);pieces.append((points,faces));vertices=[];polygons=[]
    for p,f in pieces:
        offset=len(vertices);vertices.extend(p);polygons.extend(tuple(i+offset for i in face) for face in f)
    return BVHTree.FromPolygons(vertices,polygons),vertices,polygons
choices=[];trials=[]
for sign in [-1,1]:
    anchor=bpy.data.objects['IC1_TrunnionPin_'+str(sign)];top=anchor.matrix_world.translation.copy();axis=(anchor.matrix_world.to_3x3()@Vector((0,0,1))).normalized();a=Vector((axis.x,axis.y,0));norm=a.length;a/=norm;distance=(axis.dot(top)-axis.z*foot_z-axis.x*center.x-axis.y*center.y)/norm;closest=Vector((center.x,center.y,foot_z))+a*distance;tangent=Vector((-a.y,a.x,0));candidates=[]
    for radius in [.525,.54,.555,.57]:
        if abs(distance)>=radius:continue
        reach=math.sqrt(radius*radius-distance*distance)
        for side in [-1,1]:
            foot=closest+tangent*(side*reach);assert abs((foot-top).dot(axis))<1e-6
            tree,vertices,polygons=envelope(top,foot,axis);blocked=[];ports=[];a_contacts=[]
            for name,obstacle in obstacles.items():
                hits=tree.overlap(obstacle)
                if hits:(ports if name in fixed_skins else blocked).append({'mesh':name,'triangle_pairs':len(hits)})
            for frame,parts in mouth.items():
                for name,obstacle in parts.items():
                    hits=tree.overlap(obstacle)
                    if hits:a_contacts.append({'frame':frame,'mesh':name,'triangle_pairs':len(hits)})
            row={'anchor':anchor.name,'top':list(top),'foot':list(foot),'pin_axis':list(axis),'radius_on_existing_deck':radius,'hinge_plane_error':abs((foot-top).dot(axis)),'length':(foot-top).length,'blocked':blocked,'mouth_contacts':a_contacts,'required_fixed_shell_ports':ports,'score':(foot-top).length+.0001*sum(r['triangle_pairs'] for r in ports)};trials.append(row)
            if not blocked and not a_contacts:candidates.append((row,tree,vertices,polygons))
    choices.append(candidates);print('TRUNNION_SUPPORT_CANDIDATES',sign,len(candidates),flush=True)
selected=[];selected_meshes=[]
for first,second in sorted(itertools.product(*choices),key=lambda pair:sum(c[0]['score'] for c in pair)):
    if first[1].overlap(second[1]):continue
    selected=[first[0],second[0]];selected_meshes=[{'anchor':c[0]['anchor'],'vertices':[list(p) for p in c[2]],'faces':c[3]} for c in [first,second]];break
args=sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else [];OUT=ROOT/next((a.split('=',1)[1] for a in args if a.startswith('--out=')),'review/I_refinement/nautilus_r1/trunnion_support_r18/route_r2');OUT.mkdir(parents=True,exist_ok=True);result={'source_sha256':s['source_sha256'],'base_sha256':s['base_sha256'],'existing_deck':deck.name,'deck_top_z':deck_top,'complete_route_candidate':bool(selected),'selected':selected,'trials':trials,'lower_neck_included':True,'scope':'Conservative closed eye/neck/barrel/lower-neck/foot envelopes in the exact existing trunnion hinge planes, using the existing wider device deck annulus. Surface-overlap plan only; final formed joints, fitted shoe undersides, ports, containment, continuous motion and art/native checks remain pending.'};(OUT/'route_plan.json').write_text(json.dumps(result,indent=2)+'\n');(OUT/'selected_envelopes.json').write_text(json.dumps({'source_sha256':s['source_sha256'],'envelopes':selected_meshes},indent=2)+'\n');print(json.dumps({'complete':bool(selected),'selected':selected,'rejected':[(r['anchor'],r['radius_on_existing_deck'],[b['mesh'] for b in r['blocked']],len(r['mouth_contacts'])) for r in trials if r['blocked'] or r['mouth_contacts']]}),flush=True)
