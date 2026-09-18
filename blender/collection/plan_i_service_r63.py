"""Source-measured service modules and tentative paths; no source overwrite."""
import bpy,json,hashlib,math,struct,collections,sys
from pathlib import Path
from mathutils import Vector,Matrix,Quaternion
from mathutils.bvhtree import BVHTree
ROOT=Path(__file__).resolve().parents[2];OUT=ROOT/'review/I_refinement/nautilus_r1/service_r63';OUT.mkdir(parents=True,exist_ok=True)
only03='--only03'in sys.argv
wide='--wide'in sys.argv
if only03:OUT=OUT/('stage03_wide'if wide else 'stage03');OUT.mkdir(parents=True,exist_ok=True)
s=json.loads((ROOT/'review/I_refinement/nautilus_r1/curved_returns_r61/build.json').read_text());sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
assert sha(ROOT/s['source'])==s['source_sha256'];bpy.ops.wm.open_mainfile(filepath=str(ROOT/s['source']));bpy.context.scene.frame_set(1);bpy.context.view_layer.update()
body=bpy.data.objects['IN1_BodyRoot'];mouth=bpy.data.objects['IAM_MODULE']
for o in [body,*body.children_recursive,mouth,*mouth.children_recursive]:
    if o.animation_data:o.animation_data_clear()
for row in s['form_panels']:
    o=bpy.data.objects[row['node']];o.location=Vector(row['pivot_blender'])+Vector(row['lift_blender']);o.rotation_quaternion=Quaternion(Vector(row['axis_blender']),row['angle'])
    if 'mechanism'in row:
        m=row['mechanism'];bpy.data.objects[m['carriage']].location=(0,0,m['stroke']);bpy.data.objects[m['rotor']].rotation_quaternion=Quaternion(Vector(m['axis_local_blender']),row['angle'])
bpy.context.view_layer.update()
defs=[{'id':'mouth','roots':[mouth.name],'stage':0,'label':'Complete acoustic mouth cassette'}]
for n in [3,4,5]:defs.append({'id':'cover_%02d'%n,'roots':['IN1_PanelPivot_%02d'%n,'IN1_FixedRearShell_%02d'%n,'IN2_Cassette%02d_Frame'%n],'stage':1,'label':'Cover, matching rear shell and entire lift cassette'})
defs[1]['roots']=['IN1_PanelPivot_03','IN2_Cassette03_Rotor']
defs[1]['label']='Front cover and bolted rotor tongue; carriage and pressure cylinder retained'
defs.extend([
    {'id':'pin_cap_03','roots':['IN2_Cassette03PinHead-1'],'stage':0,'label':'Remove negative hinge end retainer first','start':.05,'duration':.5},
    {'id':'pin_03','roots':['IN2_Cassette03CaptivePin','IN2_Cassette03PinHead1'],'stage':0,'label':'Withdraw captive hinge pin toward positive end','start':.55,'duration':.6}
])
pin_axis=(bpy.data.objects['IN2_Cassette03_Carriage'].matrix_world.to_3x3()@Vector(next(r['mechanism']['axis_local_blender']for r in s['form_panels']if r['node']=='IN1_PanelPivot_03'))).normalized()
claimed=set();groups=[];dg=bpy.context.evaluated_depsgraph_get()
def geometry(objects):
    v=[];f=[];owners=[]
    for o in objects:
        e=o.evaluated_get(dg);m=e.to_mesh();m.calc_loop_triangles();off=len(v)
        v.extend(e.matrix_world@x.co for x in m.vertices);f.extend(tuple(off+i for i in t.vertices)for t in m.loop_triangles);owners.extend([o.name]*len(m.loop_triangles));e.to_mesh_clear()
    return v,f,owners
for d in defs:
    roots=[bpy.data.objects[n]for n in d['roots']];objects=[]
    for root in roots:
        objects.extend(o for o in [root,*root.children_recursive]if o.type=='MESH')
    assert not claimed.intersection(objects);claimed.update(objects)
    v,f,owners=geometry(objects);lo=Vector(min(p[k]for p in v)for k in range(3));hi=Vector(max(p[k]for p in v)for k in range(3));center=(lo+hi)*.5
    if d['id']=='mouth':offset=-mouth.matrix_world.to_3x3().col[2].normalized()*1.05
    elif d['id']=='pin_cap_03':offset=-pin_axis*.12
    elif d['id']=='pin_03':offset=pin_axis*.18
    else:
        direction=Vector((center.x-.12,0,center.z-1.96)).normalized();offset=direction*.80
        if d['id']=='cover_03':offset=Vector((1.0 if wide else .2,-.9,.18))
        if d['id']=='cover_05':offset=Vector((.05,.15,1.))
    d.update(meshes=[o.name for o in objects],mesh_count=len(objects),bounds_blender=[list(lo),list(hi)],offset_blender=list(offset),duration=d.get('duration',1.6),start=d.get('start',.25 if d['id']=='mouth' else 1.65))
    if d['id']=='cover_03':d['release_offset_blender']=list(-bpy.data.objects['IN2_Cassette03_Carriage'].matrix_world.to_3x3().col[1].normalized()*.12)
    groups.append((d,v,f,owners));print('SERVICE_GROUP',d['id'],len(objects),tuple(lo),tuple(hi),tuple(offset),flush=True)
fixed=[o for o in body.children_recursive if o.type=='MESH'and o not in claimed]
fv,ff,fowners=geometry(fixed);fixed_tree=BVHTree.FromPolygons(fv,ff,all_triangles=True)
def shifted(v,offset):return [p+offset for p in v]
def smooth(x):x=max(0,min(1,x));return x*x*(3-2*x)
def displacement(d,t):
    if only03 and d['id']not in ['cover_03','pin_cap_03','pin_03']:return Vector()
    u=max(0,min(1,(t-d['start'])/d['duration']))
    if 'release_offset_blender'in d:
        a=Vector(d['release_offset_blender'])
        return a*smooth(u/.25) if u<=.25 else a+(Vector(d['offset_blender'])-a)*smooth((u-.25)/.75)
    return Vector(d['offset_blender'])*smooth(u)
samples=[];baseline=set();new_contacts=[]
for t in [0.,.1,.15,.25,.45,.55,.7,.8,1.,1.15,1.4,1.65,1.7,1.75,1.8,1.9,2.,2.05,2.1,2.25,2.5,2.8,3.25,3.5]:
    trees=[]
    for d,v,f,owners in groups:
        delta=displacement(d,t);vertices=shifted(v,delta);tree=BVHTree.FromPolygons(vertices,f,all_triangles=True);trees.append((d,tree,delta,owners))
    row=[]
    for i,(d,tree,delta,owners)in enumerate(trees):
        hits=tree.overlap(fixed_tree);count=len(hits)
        if count:row.append({'a':d['id'],'b':'fixed_body','triangle_pairs':count,'owners':dict(collections.Counter(owners[a]+' / '+fowners[b]for a,b in hits))})
        for other,other_tree,_,_ in trees[i+1:]:
            count=len(tree.overlap(other_tree))
            if count:row.append({'a':d['id'],'b':other['id'],'triangle_pairs':count})
    if t==0.:baseline={(x['a'],x['b'])for x in row}
    for hit in row:
        if (hit['a'],hit['b'])not in baseline:new_contacts.append({'time':t,**hit})
    samples.append({'time':t,'contacts':row,'offsets':{d['id']:list(delta)for d,_,delta,_ in trees}});print('SERVICE_SAMPLE',t,row,flush=True)
result={'source_sha256':s['source_sha256'],'component_sha256':s['component_sha256'],'prepared_opening':1.,'groups':defs,'fixed_meshes':[o.name for o in fixed],'fixed_mesh_count':len(fixed),'total_claimed_meshes':len(claimed),'samples':samples,'new_contact_pairs':new_contacts,'baseline_pairs':[list(p)for p in baseline],'status':'tentative_paths_require_contact_review','scope':'Real source rigid service assemblies AFTER normal guided opening. Original source file unchanged. Triangle intersections sampled; baseline contacts are recorded, NOT accepted or waived. No continuous collision, containment, unfastening, actual animation asset or final art acceptance.'}
(OUT/'plan.json').write_text(json.dumps(result,indent=2)+'\n')
if only03:
    result['active_groups']=['cover_03','pin_cap_03','pin_03']
    result['scope']+=' This run keeps mouth and other service modules stationary, checking only stage03 withdrawal.'
    (OUT/'plan.json').write_text(json.dumps(result,indent=2)+'\n')
