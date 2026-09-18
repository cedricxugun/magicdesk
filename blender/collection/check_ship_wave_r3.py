"""R3 independent mesh inspection: closure, gears and cross-group collisions."""
import bpy,sys,math,json,hashlib,collections
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(Path(__file__).parent))
from ship_wave_kinematics import *
source=ROOT/'blender/collection/G_ship_r3.blend';bpy.ops.wm.open_mainfile(filepath=str(source));scene=bpy.context.scene
root=bpy.data.objects['GS2_Ship'];meta=json.loads((ROOT/'app/assets/collection/components/G_ship_r3.json').read_text());rig=meta['rig']
names=[rig['pitch'],rig['roll']]+rig['sails']+rig['waves']+[rig['shaft'],rig['pinion']]+rig['rockers']+rig['rods']+rig['rollers']+[s['node'] for s in meta.get('springs',[])]
groups={n:[] for n in names};groups['fixed']=[]
for obj in root.children_recursive:
    if obj.type not in ['MESH','CURVE'] or 'ReferenceOriginalDisc' in obj.name:continue
    ancestor=obj if 'AnchoredTorsionSpring' in obj.name else obj.parent
    while ancestor and ancestor.name not in names:ancestor=ancestor.parent
    groups[ancestor.name if ancestor else 'fixed'].append(obj)
scene.frame_set(1);deps=bpy.context.evaluated_depsgraph_get();cache={}
for objs in groups.values():
    for obj in objs:
        ev=obj.evaluated_get(deps);me=ev.to_mesh();me.calc_loop_triangles()
        cache[obj.name]=([v.co.copy() for v in me.vertices],[tuple(p.vertices) for p in me.loop_triangles]);ev.to_mesh_clear()
def tree(objs):
    vs=[];fs=[];owners=[]
    for o in objs:
        pts,faces=cache[o.name]
        if 'WorkingSheet' in o.name or 'AnchoredTorsionSpring' in o.name:
            ev=o.evaluated_get(bpy.context.evaluated_depsgraph_get());me=ev.to_mesh();me.calc_loop_triangles()
            pts=[v.co.copy() for v in me.vertices];faces=[tuple(p.vertices) for p in me.loop_triangles];ev.to_mesh_clear()
        offset=len(vs);vs.extend(o.matrix_world@p for p in pts);fs.extend(tuple(offset+j for j in f) for f in faces);owners.extend([o.name]*len(faces))
    return BVHTree.FromPolygons(vs,fs,all_triangles=True),owners
frames=list(range(1,452,30 if '--quick' in sys.argv else 5));issues={};errors={'cam_contact':0.,'rod_closure':0.,'gear_ratio':0.};guide=[];wave_ranges=[[],[],[]]
for frame in frames:
    scene.frame_set(frame);bpy.context.view_layer.update();phase=-bpy.data.objects[rig['shaft']].rotation_euler.y
    expected=-(GEAR_ANGLE+math.pi+math.pi/18-2*phase)
    errors['gear_ratio']=max(errors['gear_ratio'],abs(bpy.data.objects[rig['pinion']].rotation_euler.y-expected))
    for i in range(3):
        cam=bpy.data.objects[rig['cams'][i]];roller=bpy.data.objects[rig['rollers'][i]];rod=bpy.data.objects[rig['rods'][i]];wave=bpy.data.objects[rig['waves'][i]];rocker=bpy.data.objects[rig['rockers'][i]]
        center=cam.matrix_world@Vector((ECCENTRIC,0,0));c=roller.matrix_world.translation
        errors['cam_contact']=max(errors['cam_contact'],abs(Vector((center.x,center.z)).__sub__(Vector((c.x,c.z))).length-.030))
        start=rocker.matrix_world@Vector((-OUTPUT,.010,0));end=wave.matrix_world@Vector((.088,.020,-.015))
        errors['rod_closure']=max(errors['rod_closure'],(rod.matrix_world@Vector((0,0,0))-start).length,(rod.matrix_world@Vector((ROD_LENGTH,0,0))-end).length)
        wave_ranges[i].append(wave.location.z)
        if wave.location.z-.011<.148 or wave.location.z+.001>.222:guide.append(frame)
    trees={n:tree(objs) for n,objs in groups.items()}
    for i,name in enumerate(names):
        for other in ['fixed']+names[i+1:]:
            ta,oa=trees[name];tb,ob=trees[other]
            pairs=collections.Counter((oa[a],ob[b]) for a,b in ta.overlap(tb))
            for pair,count in pairs.items():
                key=' | '.join(pair)
                if key not in issues:issues[key]={'objects':pair,'groups':[name,other],'frames':[],'triangles':0}
                issues[key]['frames'].append(frame);issues[key]['triangles']=max(count,issues[key]['triangles'])
report={'source_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),'frames':frames,'errors':errors,'guide_errors':guide,'wave_ranges':[[min(v),max(v)] for v in wave_ranges],'intersections':list(issues.values()),'passed':not issues and not guide and max(errors.values())<1e-5,'scope':'Cross-moving-group mesh surface intersections and exact joint closure at source keyed samples; not containment, continuous sweep or external player clearance.'}
(ROOT/'review/G_optical_curator/ship_r3/mechanism_check.json').write_text(json.dumps(report,indent=2)+'\n')
print('R3_CHECK',json.dumps({'frames':len(frames),'errors':errors,'pairs':len(issues),'first':list(issues.values())[:8]}),flush=True)
