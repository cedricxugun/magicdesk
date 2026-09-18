"""Report actual rear-fixture contacts separately from unfinished chamber seats."""
import bpy,json,hashlib,sys,math
from pathlib import Path
from mathutils.bvhtree import BVHTree
ROOT=Path(__file__).resolve().parents[2];args=sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else []
path=ROOT/next((a.split('=',1)[1] for a in args if a.startswith('--report=')),'review/I_refinement/nautilus_r1/core_bridge_r4/build.json');spec=json.loads(path.read_text());assert hashlib.sha256((ROOT/spec['source']).read_bytes()).hexdigest()==spec['source_sha256']
bpy.ops.wm.open_mainfile(filepath=str(ROOT/spec['source']));scene=bpy.context.scene;scene.frame_set(1);bpy.context.view_layer.update();deps=bpy.context.evaluated_depsgraph_get()
def geometry(objects):
    v=[];f=[]
    for o in objects:
        e=o.evaluated_get(deps);m=e.to_mesh();m.calc_loop_triangles();offset=len(v);v.extend(e.matrix_world@p.co for p in m.vertices);f.extend(tuple(offset+k for k in t.vertices) for t in m.loop_triangles);e.to_mesh_clear()
    return {'v':v,'f':f,'tree':BVHTree.FromPolygons(v,f,all_triangles=True),'min':[min(p[i] for p in v) for i in range(3)],'max':[max(p[i] for p in v) for i in range(3)]}
def contact(a,b):
    if any(a['max'][i]<b['min'][i] or b['max'][i]<a['min'][i] for i in range(3)):return None
    pairs=a['tree'].overlap(b['tree'])
    if not pairs:return None
    points=[]
    for i,j in pairs:
        points.extend(a['v'][k] for k in a['f'][i]);points.extend(b['v'][k] for k in b['f'][j])
    return {'triangle_pairs':len(pairs),'bounds':{'min':[min(p[i] for p in points) for i in range(3)],'max':[max(p[i] for p in points) for i in range(3)]}}
fixture=[o for o in bpy.data.objects if o.type=='MESH' and o.name.startswith(('IN3_','IC1_'))];geo={o.name:geometry([o]) for o in fixture}
mouth=[o for o in bpy.data.objects if o.type=='MESH' and o.name.startswith('IAM_')];mouth_contacts=[]
for frame in [1,181]:
    scene.frame_set(frame);bpy.context.view_layer.update();a=geometry(mouth)
    for o in fixture:
        hit=contact(geo[o.name],a)
        if hit:mouth_contacts.append({'frame':frame,'part':o.name,**hit})
scene.frame_set(1);bpy.context.view_layer.update();mount_contacts=[];mating_contacts=[]
to_mouth=bpy.data.objects['IAM_MODULE'].matrix_world.inverted()
def seam_seat(pin,washer):
    sign=int(pin.rsplit('_',1)[1]);sides=washer.rsplit('_',2)
    if int(sides[-2])!=sign:return None
    side=int(sides[-1]);vv=[to_mouth@p for p in geo[washer]['v']];ax=[side*p.y for p in vv];lo,hi=min(ax),max(ax)
    radial=lambda p:math.hypot(p.x-sign*.601,p.z-.590)
    bore=min(radial(p) for p in vv);pv=[to_mouth@p for p in geo[pin]['v']];eps=.000002;clipped=[]
    def clip(points,value,greater):
        output=[]
        for a,b in zip(points,points[1:]+points[:1]):
            da=side*a.y-value;db=side*b.y-value;ia=da>=0 if greater else da<=0;ib=db>=0 if greater else db<=0
            if ia:output.append(a)
            if ia!=ib:output.append(a+(b-a)*(da/(da-db)))
        return output
    for f in geo[pin]['f']:
        points=[pv[k] for k in f]
        if max(side*p.y for p in points)<lo+eps or min(side*p.y for p in points)>hi-eps:continue
        points=clip(points,lo+eps,True)
        if points:points=clip(points,hi-eps,False)
        clipped.extend(points)
    max_radius=max((radial(p) for p in clipped),default=0.)
    head=[side*p.y for p in pv if radial(p)>bore and lo-.002<side*p.y<hi+.01]
    gap=min(head)-hi if head else None
    passed=bool(clipped) and gap is not None and abs(gap)<eps*2 and max_radius<bore-.00001
    return {'pin':pin,'washer':washer,'passed':passed,'washer_slab_mouth_local':[lo,hi],'bore_radius':bore,'max_pin_radius_in_washer_slab':max_radius,'head_seat_gap':gap,'scope':'Pin triangles clipped to the actual washer thickness excluding only 2e-6 face tolerance; all material inside the slab fits inside the actual bore, and head/washer seat planes agree.'}
seats=[];seat_lookup={}
for pin in fixture:
    if not pin.name.startswith('IC1_SeamCrossBolt_'):continue
    for washer in fixture:
        if not washer.name.startswith('IC1_SeamWasher_'):continue
        proof=seam_seat(pin.name,washer.name)
        if proof:seats.append(proof);seat_lookup[frozenset([pin.name,washer.name])]=proof
changed=lambda name:name.startswith('IN3_') or name in spec['core_bridge']['new_hardware']
for i,a in enumerate(fixture):
    for b in fixture[i+1:]:
        if not (changed(a.name) or changed(b.name)):continue
        hit=contact(geo[a.name],geo[b.name])
        if hit:
            proof=seat_lookup.get(frozenset([a.name,b.name]))
            if proof and proof['passed']:mating_contacts.append({'a':a.name,'b':b.name,**hit,'proof':proof})
            else:mount_contacts.append({'a':a.name,'b':b.name,**hit})
chambers=[o for o in bpy.data.objects['IN1_BodyRoot'].children_recursive if o.type=='MESH' and o.name.startswith(('IN1_Cell','IN1_ChamberRib_'))];attachment_contacts=[]
for old in chambers:
    other=geometry([old])
    for o in fixture:
        hit=contact(geo[o.name],other)
        if hit:attachment_contacts.append({'fixture':o.name,'chamber':old.name,**hit})
seat_failures=[p for p in seats if not p['passed']]
result={'source_sha256':spec['source_sha256'],'passed':not(mouth_contacts or mount_contacts or attachment_contacts or seat_failures),'mouth_and_fastener_clear':not(mouth_contacts or mount_contacts or seat_failures),'mouth_contacts':mouth_contacts,'mount_contacts':mount_contacts,'verified_mating_contacts':mating_contacts,'seam_seat_contracts':seats,'unfinished_attachment_contacts':attachment_contacts,'scope':'New rear fixture versus A at two source frames; pairs involving changed parts; fixture versus old chambers. Only seam head/washer face contacts with independently clipped-mesh bore/seat proof are classified as mating. Inherited unmodified C1 fastener pairs, containment, continuous motion, base, optical or native behavior are not covered.'}
(path.parent/'core_contacts.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps({'mouth_contacts':[(r['frame'],r['part'],r['triangle_pairs']) for r in mouth_contacts],'mount_contacts':[(r['a'],r['b'],r['triangle_pairs']) for r in mount_contacts],'attachment_pairs':len(attachment_contacts)}),flush=True)
