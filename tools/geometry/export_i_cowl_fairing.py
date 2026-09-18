"""Export a constrained surface-fairing problem from the current source."""
import bpy,bmesh,json,hashlib,math
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree
ROOT=Path(__file__).resolve().parents[2];OUT=ROOT/'review/I_refinement/nautilus_r1/cowl_fairing_r22';OUT.mkdir(parents=True,exist_ok=True)
s=json.loads((ROOT/'review/I_refinement/nautilus_r1/mouth_finish_r21/build.json').read_text());assert hashlib.sha256((ROOT/s['source']).read_bytes()).hexdigest()==s['source_sha256']
bpy.ops.wm.open_mainfile(filepath=str(ROOT/s['source']));bpy.context.scene.frame_set(1);bpy.context.view_layer.update()
mi=bpy.data.objects['IAM_MODULE'].matrix_world.inverted();mrot=bpy.data.objects['IAM_MODULE'].matrix_world.to_3x3();C=Vector((.12,.16,1.96));R=Vector((1.01,.67,1.10))
hardware=[o for o in bpy.data.objects if o.type=='MESH' and (('IS18_'in o.name and 'PortLiner'in o.name)or(o.name.startswith('IN2_')and any(t in o.name for t in ['BodyShoe','RotatingTongue','BackBlock'])))]
hv=[];hf=[]
for o in hardware:
    o.data.calc_loop_triangles();offset=len(hv);hv.extend(o.matrix_world@v.co for v in o.data.vertices);hf.extend(tuple(offset+i for i in t.vertices)for t in o.data.loop_triangles)
hardware_tree=BVHTree.FromPolygons(hv,hf,all_triangles=True)
rows=[]
for number in [1,5,6]:
    o=bpy.data.objects['IN1_PorcelainPanel_%02d'%number];bm=bmesh.new();bm.from_mesh(o.data);bm.normal_update();bm.verts.ensure_lookup_table();bm.verts.index_update()
    normal_matrix=o.matrix_world.to_3x3().inverted().transposed();pinned=set()
    for f in bm.faces:
        world=o.matrix_world@f.calc_center_median();p=mi@world
        a=Vector(((world[i]-C[i])/(R[i]*R[i])for i in range(3))).normalized();radial=(mrot@Vector((p.x,p.y,0))).normalized();blend=max(0.,min(1.,(.70-p.z)/.30))*max(0.,min(1.,(1.4-math.hypot(p.x,p.y))/.4));n=a.lerp(radial,blend).normalized()
        if abs((normal_matrix@f.normal).normalized().dot(n))<.30:pinned.update(v.index for v in f.verts)
    # Pin one extra graph ring around free edges/bores to retain local tangency.
    pinned |= {e.other_vert(bm.verts[i]).index for i in list(pinned)for e in bm.verts[i].link_edges}
    vertices=[o.matrix_world@v.co for v in bm.verts];free=[];hardware_pins=0
    for i,world in enumerate(vertices):
        p=mi@world;eligible=-.025<p.z<.72 and math.hypot(p.x,p.y)<1.28 and i not in pinned
        if eligible:
            hit=hardware_tree.find_nearest(world,.035)
            if hit[0]is not None:eligible=False;hardware_pins+=1
        free.append(eligible)
    o.data.calc_loop_triangles()
    outer=[]
    for v,world in zip(bm.verts,vertices):
        p=mi@world;radial=(mrot@Vector((p.x,p.y,0))).normalized();outer.append((normal_matrix@v.normal).normalized().dot(radial)>0)
    rows.append({'mesh':o.name,'vertices':[list(p)for p in vertices],'edges':[[e.verts[0].index,e.verts[1].index]for e in bm.edges],'triangles':[list(t.vertices)for t in o.data.loop_triangles],'free':free,'outer_radial_surface':outer,'free_count':sum(free),'hardware_pins':hardware_pins});bm.free()
d={'source':s['source'],'source_sha256':s['source_sha256'],'mouth_matrix_blender':[list(r)for r in bpy.data.objects['IAM_MODULE'].matrix_world],'meshes':rows,'scope':'Fixed existing outlet/seam/cap edges and a 0.035-world neighborhood of actual mounting hardware; free transition surfaces only. Solver output requires collision, thickness and visual review.'}
(OUT/'problem.json').write_text(json.dumps(d,separators=(',',':'))+'\n')
for r in rows:print(r['mesh'],r['free_count'],'free;',r['hardware_pins'],'hardware pins')
