"""Find actual large outer skin/cap perimeter chains, keeping bore loops separate."""
import bpy,bmesh,json,math,sys,hashlib
from pathlib import Path
from mathutils import Vector
ROOT=Path(__file__).resolve().parents[2];args=sys.argv[sys.argv.index('--')+1:]if '--'in sys.argv else [];report=ROOT/next((a.split('=',1)[1]for a in args if a.startswith('--report=')),'review/I_refinement/nautilus_r1/mouth_finish_r21/build.json');OUT=report.parent if args else ROOT/'review/I_refinement/nautilus_r1/cowl_normals_r22';s=json.loads(report.read_text());assert hashlib.sha256((ROOT/s['source']).read_bytes()).hexdigest()==s['source_sha256']
bpy.ops.wm.open_mainfile(filepath=str(ROOT/s['source']));bpy.context.scene.frame_set(1);bpy.context.view_layer.update()
mouth=bpy.data.objects['IAM_MODULE'].matrix_world;mi=mouth.inverted();center=Vector((.12,.16,1.96));radii=Vector((1.01,.67,1.10));rows=[]
def outward(world):
    p=mi@world;radial=mouth.to_3x3()@Vector((p.x,p.y,0));radial.normalize()
    ellipsoid=Vector(((world[i]-center[i])/(radii[i]*radii[i])for i in range(3))).normalized()
    f=max(0.,min(1.,(.70-p.z)/.30))*max(0.,min(1.,(1.4-math.hypot(p.x,p.y))/.4))
    return ellipsoid.lerp(radial,f).normalized()
for number in [3,4,5]:
    o=bpy.data.objects['IN1_PorcelainPanel_%02d'%number];bm=bmesh.new();bm.from_mesh(o.data);bm.normal_update();bm.verts.ensure_lookup_table();bm.verts.index_update();bm.edges.index_update()
    normal_matrix=o.matrix_world.to_3x3().inverted().transposed();selected=[]
    for e in bm.edges:
        if not e.is_manifold or e.calc_face_angle()<.5:continue
        direction=outward(o.matrix_world@((e.verts[0].co+e.verts[1].co)*.5));dots=[(normal_matrix@f.normal).normalized().dot(direction)for f in e.link_faces]
        if max(dots)>.45 and min(dots)<.25:selected.append(e)
    unseen=set(selected);chains=[]
    while unseen:
        seed=unseen.pop();component={seed};pending=[seed]
        while pending:
            for v in pending.pop().verts:
                for edge in v.link_edges:
                    if edge in unseen:unseen.remove(edge);component.add(edge);pending.append(edge)
        points={v for e in component for v in e.verts};degrees={v:sum(e in component for e in v.link_edges)for v in points};length=sum((o.matrix_world.to_3x3()@(e.verts[1].co-e.verts[0].co)).length for e in component)
        if length<.20:continue
        chains.append({'edges':len(component),'length':length,'minimum_edge_length':min(e.calc_length()for e in component),'closed':all(v==2 for v in degrees.values()),'degree_histogram':{str(d):list(degrees.values()).count(d)for d in set(degrees.values())},'segments_blender':[[list(o.matrix_world@v.co)for v in e.verts]for e in sorted(component,key=lambda e:e.index)],'source_edges':[e.index for e in sorted(component,key=lambda e:e.index)]})
    rows.append({'mesh':o.name,'chains':chains});bm.free()
(OUT/'perimeter_probe.json').write_text(json.dumps({'source_sha256':s['source_sha256'],'rows':rows,'scope':'Geometry feature-chain diagnosis only; fragmented chains are not full production rims.'},indent=2)+'\n')
for r in rows:print(r['mesh'],[{k:v for k,v in c.items()if k not in ['segments_blender','source_edges']}for c in r['chains']])
