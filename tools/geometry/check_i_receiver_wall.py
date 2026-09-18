"""Sample actual receiver inner faces against the unchanged outer face mesh."""
import bpy,json,hashlib,sys
from pathlib import Path
from mathutils.bvhtree import BVHTree
ROOT=Path(__file__).resolve().parents[2];args=sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else []
path=ROOT/next((a.split('=',1)[1] for a in args if a.startswith('--report=')),'review/I_refinement/nautilus_r1/core_bridge_r4/build.json');spec=json.loads(path.read_text());assert hashlib.sha256((ROOT/spec['source']).read_bytes()).hexdigest()==spec['source_sha256']
bpy.ops.wm.open_mainfile(filepath=str(ROOT/spec['source']));bpy.context.scene.frame_set(1);bpy.context.view_layer.update()
o=bpy.data.objects['IN1_PorcelainPanel_02'];o.data.calc_loop_triangles();values=[a.value for a in o.data.attributes['formed_wall_fraction'].data];v=[o.matrix_world@p.co for p in o.data.vertices];faces=[tuple(t.vertices) for t in o.data.loop_triangles]
outer=[f for f in faces if max(values[k] for k in f)<.001];tree=BVHTree.FromPolygons(v,outer,all_triangles=True);to_mouth=bpy.data.objects['IAM_MODULE'].matrix_world.inverted();samples=[]
region=[a.value for a in o.data.attributes['IN3_receiver_region'].data] if 'IN3_receiver_region' in o.data.attributes else None
for i,f in enumerate(faces):
    if min(values[k] for k in f)<.999:continue
    points=[v[k] for k in f];center=(points[0]+points[1]+points[2])/3.;local=to_mouth@center
    if region is not None:
        if max(region[k] for k in f)<.5:continue
    elif not (.530<local.z<.720 and .45<(local.x**2+local.y**2)**.5<.80):continue
    for kind,p in [('center',center),('edge01',(points[0]+points[1])/2),('edge12',(points[1]+points[2])/2),('edge20',(points[2]+points[0])/2)]:
        near,n,index,distance=tree.find_nearest(p)
        samples.append({'triangle':i,'sample':kind,'distance':distance,'point':list(p),'outer_point':list(near)})
samples.sort(key=lambda r:r['distance']);minimum=.006
result={'source_sha256':spec['source_sha256'],'minimum_requested_scene_units':minimum,'passed':bool(samples) and samples[0]['distance']>=minimum,'samples':len(samples),'minimum':samples[0] if samples else None,'below_minimum':sum(r['distance']<minimum for r in samples),'worst':samples[:15],'scope':'Actual inner-triangle centers and edge midpoints in the receiver region to nearest actual outer-face mesh. Scene units, not millimeters. Does not prove continuous minimum thickness, loads or all shell regions.'}
(path.parent/'receiver_wall_check.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({k:result[k] for k in ['passed','samples','minimum','below_minimum']}),flush=True)
