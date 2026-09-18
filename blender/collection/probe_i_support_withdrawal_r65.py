"""Validate stand separation and axial leg removal, keeping ports with shell."""
import bpy,json,hashlib,collections,sys
from pathlib import Path
from mathutils import Vector,Quaternion
from mathutils.bvhtree import BVHTree
ROOT=Path(__file__).resolve().parents[2];OUT=ROOT/'review/I_refinement/nautilus_r1/cradle_release_r65/lifted_legs_r2';OUT.mkdir(parents=True,exist_ok=True)
report=ROOT/'review/I_refinement/nautilus_r1/curved_returns_r61/build.json'
for argument in sys.argv:
    if argument.startswith('--report='):report=ROOT/argument.split('=',1)[1];OUT=report.parent/'release_probe';OUT.mkdir(parents=True,exist_ok=True)
s=json.loads(report.read_text());assert hashlib.sha256((ROOT/s['source']).read_bytes()).hexdigest()==s['source_sha256'];bpy.ops.wm.open_mainfile(filepath=str(ROOT/s['source']));bpy.context.scene.frame_set(1)
body=bpy.data.objects['IN1_BodyRoot'];mouth=bpy.data.objects['IAM_MODULE']
for row in s['form_panels']:
    o=bpy.data.objects[row['node']];o.animation_data_clear();o.location=Vector(row['pivot_blender'])+Vector(row['lift_blender']);o.rotation_quaternion=Quaternion(Vector(row['axis_blender']),row['angle'])
    if 'mechanism'in row:
        m=row['mechanism'];bpy.data.objects[m['carriage']].animation_data_clear();bpy.data.objects[m['rotor']].animation_data_clear();bpy.data.objects[m['carriage']].location=(0,0,m['stroke']);bpy.data.objects[m['rotor']].rotation_quaternion=Quaternion(Vector(m['axis_local_blender']),row['angle'])
bpy.context.view_layer.update();mount=bpy.data.objects['IC1_MouthMount'];axis=(mount.matrix_world.to_3x3()@Vector((1,0,0))).normalized()
existing=set(bpy.data.objects);bpy.ops.import_scene.gltf(filepath=str(ROOT/'app/assets/helios_model.glb'));base=next(o for o in bpy.data.objects if o not in existing and o.name.split('.')[0]=='BASE_FIXED')
def geo(objects):
    v=[];f=[];owners=[];dg=bpy.context.evaluated_depsgraph_get()
    for o in objects:
        e=o.evaluated_get(dg);m=e.to_mesh();m.calc_loop_triangles();n=len(v);v.extend(e.matrix_world@x.co for x in m.vertices);f.extend(tuple(n+i for i in t.vertices)for t in m.loop_triangles);owners.extend([o.name]*len(m.loop_triangles));e.to_mesh_clear()
    return v,f,owners
def make(v,f):return BVHTree.FromPolygons(v,f,all_triangles=True)
all_body=list(dict.fromkeys(o for root in [body,mouth]for o in root.children_recursive if o.type=='MESH'))
adapter_names={'IN1_DeckFoot','IN1_LowSaddle'}|{o.name for o in all_body if o.name.startswith(('IN1_FittedSaddleSeat_','IN1_FittedSaddleGasket_'))}
base_parts=[o for o in [base,*base.children_recursive]if o.type=='MESH']+[bpy.data.objects[n]for n in adapter_names]
groups=[]
for sign in [-1,1]:
    for side in [-1,1]:groups.append({'id':'cap_%s_%s'%(sign,side),'names':['IC1_TrunnionRetainer_%s_%s'%(sign,side)],'offset':list(axis*(side*.025)+(axis*(sign*.10)if side==sign else Vector()))})
    groups.append({'id':'pin_'+str(sign),'names':['IC1_TrunnionPin_'+str(sign)],'offset':list(axis*(sign*.10))})
for i in [1,2]:
    foot=Vector(s['metal_supports']['supports'][i-1]['foot'])
    for side in [-1,1]:
        name='IS18_Leg%02d_DeckBolt_%s'%(i,side);row=next(x for x in s['metal_supports']['deck_fasteners']if x['mesh']==name)
        away=Vector((row['xy'][0]-foot.x,row['xy'][1]-foot.y,0)).normalized()*.12
        groups.append({'id':'deck_%s_%s'%(i,side),'names':[name,'IS18_Leg%02d_DeckWasher_%s'%(i,side)],'offset':list(away+Vector((0,0,.08))),'park_direction':list(away)})
released={n for g in groups for n in g['names']}
legs=[]
for i,record in enumerate(s['metal_supports']['supports'],1):
    names=[o.name for o in all_body if o.name.startswith('IS18_Leg%02d_'%i)and 'Port'not in o.name and 'DeckBolt'not in o.name and 'DeckWasher'not in o.name]
    legs.append({'id':'leg_%02d'%i,'names':names,'offset':list((Vector(record['foot'])-Vector(record['top'])).normalized()*.25)})
for g in groups+legs:g['geo']=geo([bpy.data.objects[n]for n in g['names']])
leg_names={n for g in legs for n in g['names']};fixed_body=[o for o in all_body if o.name not in released|leg_names|adapter_names]
bv,bf,bo=geo(base_parts);bt=make(bv,bf);fixed_geo=geo(fixed_body)
def compare(label,v,f,owners,other_v,other_f,other_owners):
    hits=make(v,f).overlap(make(other_v,other_f))
    return {'pair':label,'count':len(hits),'owners':dict(collections.Counter(owners[a]+' / '+other_owners[b]for a,b in hits))}if hits else None
results=[]
# Release motions are checked separately. This study begins with released
# fasteners in explicit parked positions; they remain present as obstacles.
for lift in [0.,.01,.025,.05,.10,.20,.35,.45]:
    v,f,n=geo([o for o in all_body if o.name not in released|adapter_names]);delta=Vector((0,0,lift));hit=compare('upper / real_base_and_stand',[x+delta for x in v],f,n,bv,bf,bo)
    results.append({'phase':'lift','amount':lift,'contacts':[hit]if hit else []});print('R65_LIFT',lift,hit,flush=True)
lift=Vector((0,0,.45))
pv,pf,po=geo([o for o in all_body if o.name not in released|adapter_names]);pv=[x+lift for x in pv];off=len(pv);pv.extend(bv);pf.extend(tuple(off+i for i in f)for f in bf);po.extend(bo)
for amount in [0.,.1,.25,.5,.75,1.]:
    hits=[]
    for g in groups:
        if 'park_direction'not in g:continue
        v,f,n=g['geo'];d=Vector((0,0,.08))+Vector(g['park_direction'])*amount;hit=compare(g['id']+' parking',[x+lift+d for x in v],f,n,pv,pf,po)
        if hit:hits.append(hit)
    results.append({'phase':'deck_parking','amount':amount,'contacts':hits});print('R65_PARK',amount,hits,flush=True)
fv,ff,fo=fixed_geo;fv=[x+lift for x in fv];fv.extend(bv);ff=ff+[(a+len(fixed_geo[0]),b+len(fixed_geo[0]),c+len(fixed_geo[0]))for a,b,c in bf];fo=fo+bo
for g in groups:
    v,f,n=g['geo'];off=len(fv);fv.extend(x+lift+Vector(g['offset'])for x in v);ff.extend(tuple(off+i for i in tri)for tri in f);fo.extend(n)
for amount in [0.,.03,.08,.15,.25,.4,.6,.8,1.]:
    contacts=[];moved=[]
    for g in legs:
        v,f,n=g['geo'];v=[x+lift+Vector(g['offset'])*amount for x in v];hit=compare(g['id']+' / fixed',v,f,n,fv,ff,fo)
        if hit:contacts.append(hit)
        moved.append((v,f,n))
    hit=compare('leg01 / leg02',*moved[0],*moved[1])
    if hit:contacts.append(hit)
    results.append({'phase':'leg_withdrawal','amount':amount,'contacts':contacts});print('R65_LEG',amount,contacts,flush=True)
ports=[]
for i,row in enumerate(s['metal_supports']['ports'],1):
    objects=[o for o in bpy.data.objects[row['frame']].children_recursive if o.type=='MESH'];v,f,n=geo(objects)
    direction=Vector((row['matrix_blender'][0][2],row['matrix_blender'][1][2],row['matrix_blender'][2][2])).normalized()
    ports.append({'id':'port_%02d'%i,'names':[o.name for o in objects],'offset':list(direction*.22),'geo':(v,f,n)})
port_names={n for g in ports for n in g['names']}
pv,pf,po=geo([o for o in fixed_body if o.name not in port_names]);pv=[x+lift for x in pv]
for v,f,n in [(bv,bf,bo)]+[([x+lift+Vector(g['offset'])for x in g['geo'][0]],g['geo'][1],g['geo'][2])for g in groups+legs]:
    off=len(pv);pv.extend(v);pf.extend(tuple(off+i for i in t)for t in f);po.extend(n)
for amount in [0.,.025,.05,.1,.2,.35,.5,.7,1.]:
    contacts=[];moved=[]
    for g in ports:
        v,f,n=g['geo'];v=[x+lift+Vector(g['offset'])*amount for x in v];hit=compare(g['id']+' / fixed',v,f,n,pv,pf,po)
        if hit:contacts.append(hit)
        moved.append((v,f,n))
    hit=compare('port01 / port02',*moved[0],*moved[1])
    if hit:contacts.append(hit)
    results.append({'phase':'port_withdrawal','amount':amount,'contacts':contacts});print('R65_PORT',amount,contacts,flush=True)
for g in groups+legs+ports:g.pop('geo')
(OUT/'probe.json').write_text(json.dumps({'source_sha256':s['source_sha256'],'fixed_adapter_names':sorted(adapter_names),'groups':groups,'legs':legs,'ports':ports,'results':results,'scope':'Read-only source geometry. Whole stand/seat/gasket remains on real base, upper lifts .45; released deck bolts park outward before legs withdraw, then ports withdraw along their real axes. Every contact retained; parked fastener pairwise/lift sweeps are not complete, not a passed full sequence or animation.'},indent=2)+'\n')
