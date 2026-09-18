"""Read-only release probe for the source-defined front support/cradle assembly."""
import bpy,json,hashlib,collections,math,sys
from pathlib import Path
from mathutils import Vector,Matrix,Quaternion
from mathutils.bvhtree import BVHTree
ROOT=Path(__file__).resolve().parents[2];OUT=ROOT/'review/I_refinement/nautilus_r1/cradle_release_r65';OUT.mkdir(parents=True,exist_ok=True)
s=json.loads((ROOT/'review/I_refinement/nautilus_r1/curved_returns_r61/build.json').read_text());assert hashlib.sha256((ROOT/s['source']).read_bytes()).hexdigest()==s['source_sha256']
bpy.ops.wm.open_mainfile(filepath=str(ROOT/s['source']));bpy.context.scene.frame_set(1)
for row in s['form_panels']:
    o=bpy.data.objects[row['node']];o.animation_data_clear();o.location=Vector(row['pivot_blender'])+Vector(row['lift_blender']);o.rotation_quaternion=Quaternion(Vector(row['axis_blender']),row['angle'])
    if 'mechanism'in row:
        m=row['mechanism'];bpy.data.objects[m['carriage']].animation_data_clear();bpy.data.objects[m['rotor']].animation_data_clear();bpy.data.objects[m['carriage']].location=(0,0,m['stroke']);bpy.data.objects[m['rotor']].rotation_quaternion=Quaternion(Vector(m['axis_local_blender']),row['angle'])
bpy.context.view_layer.update();body=bpy.data.objects['IN1_BodyRoot'];mount=bpy.data.objects['IC1_MouthMount'];axis=(mount.matrix_world.to_3x3()@Vector((1,0,0))).normalized()
groups=[]
for sign in [-1,1]:
    for side in [-1,1]:groups.append({'id':'top_retainer_%s_%s'%(sign,side),'names':['IC1_TrunnionRetainer_%s_%s'%(sign,side)],'offset':list(axis*(side*.025)),'start':0.,'duration':.7})
    groups.append({'id':'top_pin_'+str(sign),'names':['IC1_TrunnionPin_'+str(sign)],'offset':list(axis*(sign*.10)),'start':.8,'duration':.8})
for index in [1,2]:
    for side in [-1,1]:groups.append({'id':'deck_bolt_%s_%s'%(index,side),'names':['IS18_Leg%02d_DeckBolt_%s'%(index,side)],'offset':[0,0,.08],'start':0.,'duration':.9})
moving_names={n for g in groups for n in g['names']}
for g in groups:
    if g['id'].startswith('top_retainer_'):
        a,b=[int(v)for v in g['id'].removeprefix('top_retainer_').split('_')]
        if a==b:g['follow_pin_offset']=list(axis*(a*.10))
cradle=[]
for name in ['IN1_PanelPivot_01','IN1_PanelPivot_02','IS18_TrunnionSupports']:
    cradle.extend(o for o in [bpy.data.objects[name],*bpy.data.objects[name].children_recursive]if o.type=='MESH'and o.name not in moving_names)
moving_names.update(o.name for o in cradle)
groups.append({'id':'front_cradle','names':[o.name for o in cradle],'offset':[0,0,0],'start':1.8,'duration':2.7})
pivot=sum((Vector(r['top'])for r in s['metal_supports']['supports']),Vector())/2
forward=-mount.matrix_world.to_3x3().col[2].normalized()
def geo(objects):
    vertices=[];faces=[];owners=[];dg=bpy.context.evaluated_depsgraph_get()
    for o in objects:
        e=o.evaluated_get(dg);mesh=e.to_mesh();mesh.calc_loop_triangles();off=len(vertices);vertices.extend(e.matrix_world@v.co for v in mesh.vertices);faces.extend(tuple(off+i for i in t.vertices)for t in mesh.loop_triangles);owners.extend([o.name]*len(mesh.loop_triangles));e.to_mesh_clear()
    return vertices,faces,owners
fixed=[o for root in [body,bpy.data.objects['IAM_MODULE']]for o in root.children_recursive if o.type=='MESH'and o.name not in moving_names]
existing=set(bpy.data.objects);bpy.ops.import_scene.gltf(filepath=str(ROOT/'app/assets/helios_model.glb'))
base=next(o for o in bpy.data.objects if o not in existing and o.name.split('.')[0]=='BASE_FIXED')
fixed.extend(o for o in [base,*base.children_recursive]if o.type=='MESH');fixed=list(dict.fromkeys(fixed));fv,ff,fo=geo(fixed);ft=BVHTree.FromPolygons(fv,ff,all_triangles=True)
prepared=[]
for g in groups:v,f,n=geo([bpy.data.objects[x]for x in g['names']]);prepared.append((g,v,f,n))
def smooth(x):x=max(0,min(1,x));return x*x*(3-2*x)
def cradle_pose(t):
    u=smooth((t-1.8)/1.2);v=smooth((t-3.)/1.5)
    return Matrix.Translation(Vector((0,0,.03))*u+(forward*.75+Vector((0,0,.08)))*v)@Matrix.Translation(pivot)@Matrix.Rotation(-.45*u,4,axis)@Matrix.Translation(-pivot)
samples=[]
for time in [0.,.05,.12,.25,.45,.7,.8,.9,1.,1.2,1.4,1.6,1.8,1.9,2.,2.2,2.4,2.7,3.,3.2,3.5,3.8,4.2,4.5]:
    trees=[];contacts=[]
    for g,v,f,n in prepared:
        u=smooth((time-g['start'])/g['duration']);d=Vector(g['offset'])*u
        if g.get('follow_pin_offset'):d+=Vector(g['follow_pin_offset'])*smooth((time-.8)/.8)
        transformed=[x+d for x in v]
        if g['id']=='front_cradle' or g['id'].startswith('deck_bolt_'):transformed=[cradle_pose(time)@x for x in transformed]
        trees.append((g,BVHTree.FromPolygons(transformed,f,all_triangles=True),n))
    for i,(g,t,n)in enumerate(trees):
        hits=t.overlap(ft)
        if hits:contacts.append({'group':g['id'],'against':'fixed','pairs':len(hits),'owners':dict(collections.Counter(n[a]+' / '+fo[b]for a,b in hits))})
        for other,tree,_ in trees[i+1:]:
            hits=t.overlap(tree)
            if hits:contacts.append({'group':g['id'],'against':other['id'],'pairs':len(hits)})
    samples.append({'time':time,'contacts':contacts});print('R65_FASTENERS',time,contacts,flush=True)
result={'source_sha256':s['source_sha256'],'base_sha256':hashlib.sha256((ROOT/'app/assets/helios_model.glb').read_bytes()).hexdigest(),'groups':groups,'samples':samples,'cradle_pivot':list(pivot),'cradle_axis':list(axis),'cradle_roots':['IN1_PanelPivot_01','IN1_PanelPivot_02','IS18_TrunnionSupports'],'scope':'Source-connected shell01/02, ports and supports carried together after top pins and deck bolts release. Real master base included. All contacts recorded, not waived; no continuous collision, physical load or final art claim.'}
(OUT/'cradle_probe.json').write_text(json.dumps(result,indent=2)+'\n')
