"""Read-only checks of the isolated conch's real guide meshes and shell topology."""
import bpy,json,hashlib
from pathlib import Path
from mathutils import Vector
ROOT=Path(__file__).resolve().parents[2];OUT=ROOT/'review/I_refinement/r1';source=ROOT/'blender/collection/I_helix_r1.blend'
bpy.ops.wm.open_mainfile(filepath=str(source));bpy.context.scene.frame_set(1)
guides=json.loads((OUT/'guide_manifest.json').read_text());upper=bpy.data.objects['IH1_UPPER']
def vertices(obj):
    ev=obj.evaluated_get(bpy.context.evaluated_depsgraph_get());m=ev.to_mesh();points=[v.co.copy() for v in m.vertices];ev.to_mesh_clear();return points
local={name:vertices(bpy.data.objects[name]) for g in guides for name in [g['barrel'],g['rod']]}
minimum=100.;rows=[]
for fraction in [0.,.25,.5,.75,1.]:
    for g in guides:
        panel=bpy.data.objects[g['panel']];panel.animation_data_clear();panel.location=Vector(panel['open_direction'])*panel['stroke']*fraction
    bpy.context.view_layer.update()
    for g in guides:
        axis=(upper.matrix_world.to_3x3()@Vector(g['axis'])).normalized();ranges=[]
        for name in [g['barrel'],g['rod']]:
            obj=bpy.data.objects[name];values=[axis.dot(obj.matrix_world@v) for v in local[name]];ranges.append((min(values),max(values)))
        overlap=min(ranges[0][1],ranges[1][1])-max(ranges[0][0],ranges[1][0]);minimum=min(minimum,overlap)
        rows.append({'fraction':fraction,'barrel':g['barrel'],'engagement':overlap})
topology=[]
for obj in upper.children_recursive:
    if obj.type!='MESH' or not any(token in obj.name for token in ['FrontPorcelain','RearPorcelain','HollowAcousticDuct']):continue
    incidence={}
    for p in obj.data.polygons:
        for edge in p.edge_keys:incidence[edge]=incidence.get(edge,0)+1
    topology.append({'object':obj.name,'nonmanifold_edges':sum(v!=2 for v in incidence.values())})
missing=[i.filepath for i in bpy.data.images if i.source=='FILE' and i.filepath and not i.packed_file and not Path(bpy.path.abspath(i.filepath)).exists()]
report={'source_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),'guide_samples':len(rows),'minimum_guide_mesh_engagement':minimum,'guide_rows':rows,'closed_shell_mesh_topology':topology,'missing_textures':missing,'passed':minimum>.008 and all(t['nonmanifold_edges']==0 for t in topology) and not missing,'scope':'Mesh-projected piston engagement at5 openings, wall edge incidence and resource paths. Not full collision or iris cam closure certification.'}
(OUT/'structure_check.json').write_text(json.dumps(report,indent=2)+'\n');print('I_STRUCTURE_CHECK',report['passed'],minimum,'missing',missing,flush=True)
if not report['passed']:raise SystemExit(1)
