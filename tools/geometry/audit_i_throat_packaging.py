"""Locate inner/outer cowl contacts before choosing a real throat pocket."""
import bpy,json,hashlib,sys
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree
ROOT=Path(__file__).resolve().parents[2];args=sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else []
path=ROOT/next((a.split('=',1)[1] for a in args if a.startswith('--report=')),'review/I_refinement/nautilus_r1/core_bridge_r4/build.json');spec=json.loads(path.read_text());assert hashlib.sha256((ROOT/spec['source']).read_bytes()).hexdigest()==spec['source_sha256']
bpy.ops.wm.open_mainfile(filepath=str(ROOT/spec['source']));bpy.context.scene.frame_set(1);bpy.context.view_layer.update()
def geo(o):
    o.data.calc_loop_triangles();v=[o.matrix_world@p.co for p in o.data.vertices];f=[tuple(t.vertices) for t in o.data.loop_triangles]
    return v,f,BVHTree.FromPolygons(v,f,all_triangles=True)
hardware=[o for o in bpy.data.objects if o.type=='MESH' and o.name.startswith(('IN3_','IC1_'))];geos={o.name:geo(o) for o in hardware};rows=[]
for name in ['IN1_PorcelainPanel_01','IN1_PorcelainPanel_02']:
    o=bpy.data.objects[name];v,f,tree=geo(o);attr=o.data.attributes['formed_wall_fraction'];values=[float(a.value) for a in attr.data]
    outer_faces=[face for face in f if max(values[k] for k in face)<.001]
    outer=BVHTree.FromPolygons(v,outer_faces,all_triangles=True)
    for h in hardware:
        hv,hf,ht=geos[h.name];pairs=tree.overlap(ht)
        if not pairs:continue
        kinds={'outer':0,'inner':0,'side':0};used=set()
        for i,j in pairs:
            a=[values[k] for k in f[i]]
            kinds['outer' if max(a)<.001 else 'inner' if min(a)>.999 else 'side']+=1
            used.update(hf[j])
        distances=[]
        for k in used:
            p,n,_,distance=outer.find_nearest(hv[k])
            if p is not None:distances.append({'point':list(hv[k]),'nearest':list(p),'distance':distance,'inward_signed':-(hv[k]-p).dot(n)})
        distances.sort(key=lambda d:d['inward_signed'])
        rows.append({'cowl':name,'hardware':h.name,'contacts':len(pairs),'cowl_sides':kinds,'smallest_inward_signed':distances[:3]})
outer_vertices=[];outer_triangles=[]
for o in bpy.data.objects['IN1_BodyRoot'].children_recursive:
    if o.type!='MESH' or not o.name.startswith(('IN1_PorcelainPanel_','IN1_FixedRearShell_','IN1_FixedMouthCheek')):continue
    if 'formed_wall_fraction' not in o.data.attributes:continue
    vv,ff,_=geo(o);values=[float(a.value) for a in o.data.attributes['formed_wall_fraction'].data];offset=len(outer_vertices);outer_vertices+=vv
    outer_triangles += [tuple(offset+k for k in face) for face in ff if max(values[k] for k in face)<.001]
outer_tree=BVHTree.FromPolygons(outer_vertices,outer_triangles,all_triangles=True)
placement=bpy.data.objects['IAM_MODULE'].matrix_world;origin=placement.translation;scale=placement.to_scale().x;basis=placement.to_3x3().normalized()
import math
radial_sections=[]
for depth in [.58,.608,.620,.6265,.638,.6485,.6575,.6675]:
    samples=[]
    for i in range(360):
        angle=math.tau*i/360;direction=basis@Vector((math.cos(angle),math.sin(angle),0));p=placement@Vector((0,0,depth))
        hit=outer_tree.ray_cast(p,direction,2.)
        if hit[0] is not None:samples.append({'degrees':i,'outer_radius_local':hit[3]/scale})
    samples.sort(key=lambda s:s['outer_radius_local']);radial_sections.append({'depth_local':depth,'hits':len(samples),'smallest_outer_radii':samples[:8]})
result={'source_sha256':spec['source_sha256'],'rows':rows,'radial_sections':radial_sections,'scope':'Static contact triangle side labels and nearest outer-face distances at contacted hardware vertices, plus outer-cowl radial samples. Loft-layer labels are incomplete at axial depth below .30; this diagnosis is not a wall-thickness or complete volume proof.'}
(path.parent/'throat_packaging.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps([{'cowl':r['cowl'],'hardware':r['hardware'],'sides':r['cowl_sides'],'min_inward_signed':r['smallest_inward_signed'][0]['inward_signed']} for r in rows]),flush=True)
