"""List actual internal cassette contacts; seating is not silently whitelisted."""
import bpy,json,sys,hashlib
from pathlib import Path
from mathutils import Vector,Quaternion
from mathutils.bvhtree import BVHTree
ROOT=Path(__file__).resolve().parents[2];args=sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else []
report=ROOT/next((a.split('=',1)[1] for a in args if a.startswith('--report=')),'review/I_refinement/nautilus_r1/hinge_r1/build.json');OUT=report.parent;spec=json.loads(report.read_text())
assert hashlib.sha256((ROOT/spec['source']).read_bytes()).hexdigest()==spec['source_sha256']
bpy.ops.wm.open_mainfile(filepath=str(ROOT/spec['source']));bpy.context.scene.frame_set(181)
for r in spec['form_panels']:
    bpy.data.objects[r['node']].animation_data_clear()
    if 'mechanism' in r:
        for k in ['carriage','rotor']:bpy.data.objects[r['mechanism'][k]].animation_data_clear()
parts=[o for o in bpy.data.objects if o.type=='MESH' and o.name.startswith('IN2_')]
shells=[o for o in bpy.data.objects['IN1_BodyRoot'].children_recursive if o.type=='MESH' and o not in parts]
def geom(o):
    e=o.evaluated_get(bpy.context.evaluated_depsgraph_get());m=e.to_mesh();m.calc_loop_triangles();v=[e.matrix_world@p.co for p in m.vertices];t=[tuple(p.vertices) for p in m.loop_triangles];e.to_mesh_clear()
    return BVHTree.FromPolygons(v,t,all_triangles=True),[min(p[i] for p in v) for i in range(3)],[max(p[i] for p in v) for i in range(3)],v
contacts=[]
for p in [0.,.2,.35,.5,.65,.8,1.]:
    for r in spec['form_panels']:
        f=r['lift_fraction'];clear=min(1.,p/max(f,.000001));turn=max(0.,(p-f)/max(1.-f,.000001))
        o=bpy.data.objects[r['node']];o.location=Vector(r['pivot_blender'])+Vector(r['lift_blender'])*clear;o.rotation_quaternion=Quaternion(Vector(r['axis_blender']),r['angle']*turn)
        if 'mechanism' in r:
            m=r['mechanism'];bpy.data.objects[m['carriage']].location=(0,0,m['stroke']*clear);bpy.data.objects[m['rotor']].rotation_quaternion=Quaternion(Vector(m['axis_local_blender']),r['angle']*turn)
    bpy.context.view_layer.update();all_parts=parts+shells;trees={o.name:geom(o) for o in all_parts}
    for i,o in enumerate(parts):
        a,lo,hi,av=trees[o.name]
        for other in all_parts[i+1:]:
            b,ll,hh,bv=trees[other.name]
            if any(hi[k]<ll[k] or hh[k]<lo[k] for k in range(3)):continue
            hits=a.overlap(b)
            if hits:
                record={'opening':p,'a':o.name,'b':other.name,'triangle_pairs':len(hits),'kind':'unresolved_surface_contact'}
                for m in spec.get('real_cassettes',[]):
                    prefix=m['frame'].removesuffix('_Frame');pin=prefix+'CaptivePin';heads=[prefix+'PinHead-1',prefix+'PinHead1']
                    if pin in [o.name,other.name] and any(h in [o.name,other.name] for h in heads):
                        head=other.name if o.name==pin else o.name;axis=(bpy.data.objects[m['carriage']].matrix_world.to_3x3()@Vector(m['axis_local_blender'])).normalized()
                        if head.endswith('-1'):axis=-axis
                        pin_values=[v.dot(axis) for v in (av if o.name==pin else bv)];head_values=[v.dot(axis) for v in (bv if o.name==pin else av)]
                        gap=min(head_values)-max(pin_values)
                        record['measured_axial_gap']=gap
                        if abs(gap)<=2e-6:record['kind']='verified_planar_pin_end_seat'
                contacts.append(record)
    print('CASSETTE_CONTACT_AUDIT',p,len(contacts),flush=True)
pairs={}
for r in contacts:pairs.setdefault(r['a']+' / '+r['b'],[]).append(r['opening'])
unresolved=[r for r in contacts if r['kind']=='unresolved_surface_contact']
result={'source_sha256':spec['source_sha256'],'component_sha256':spec['component_sha256'],'passed':not unresolved,'status':'scoped_contacts_classified' if not unresolved else 'contacts_require_seating_vs_interference_review','contacts':contacts,'pairs':pairs,'unresolved_contacts':unresolved,'scope':'Actual IN2 part pairs, cross-cassette pairs and every body-root mesh, including collar/core/supports, at seven poses. Only captive pin end seats may be classified using actual vertex axis bounds within 2e-6. Not all-A/optics/base/containment, fine threads, power drive or final acceptance.'}
(OUT/'internal_contacts.json').write_text(json.dumps(result,indent=2)+'\n');print('CASSETTE_CONTACT_PAIRS',json.dumps(pairs),flush=True)
