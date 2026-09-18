"""Conservative support envelopes at existing shoe centers; never a final support asset."""
import bpy,bmesh,json,hashlib,sys,math
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT/'blender/collection'));import i_fitted_surface as fitted
report=ROOT/'review/I_refinement/nautilus_r1/throat_sockets_r13/build.json';s=json.loads(report.read_text());assert hashlib.sha256((ROOT/s['source']).read_bytes()).hexdigest()==s['source_sha256'];bpy.ops.wm.open_mainfile(filepath=str(ROOT/s['source']));scene=bpy.context.scene;scene.frame_set(1);bpy.context.view_layer.update()
body=bpy.data.objects['IN1_BodyRoot'];core=bpy.data.objects['IN3_ContinuousThroat'];saddle=bpy.data.objects['IN1_LowSaddle'];saddle_top=max((saddle.matrix_world@v.co).z for v in saddle.data.vertices)
def geometry(o):
    o.data.calc_loop_triangles();return BVHTree.FromPolygons([o.matrix_world@v.co for v in o.data.vertices],[tuple(t.vertices) for t in o.data.loop_triangles],all_triangles=True)
parts=[o for o in body.children_recursive if o.type=='MESH'];trees={o.name:geometry(o) for o in parts};rows=[]
for index,(x,y) in enumerate([(-.18,.10),(.18,.04),(.17,.34),(-.20,.32)]):
    outline=[(x+.05*math.cos(k*math.tau/48),y+.05*math.sin(k*math.tau/48)) for k in range(48)]
    try:
        surface=fitted.clipped_surface([core],outline,from_positive=False,z_limit=1.4)
        vs,fs=fitted.extruded_patch(*surface,top_offset=-.0002,bottom_z=saddle_top+.0002);m=bpy.data.meshes.new('TemporarySupportEnvelope');m.from_pydata(vs,[],fs);m.update();m.calc_loop_triangles();envelope=BVHTree.FromPolygons(vs,[tuple(t.vertices) for t in m.loop_triangles],all_triangles=True)
        contacts=[]
        for o in parts:
            hits=envelope.overlap(trees[o.name])
            if hits:
                role='replace_existing_shoe' if o.name in ['IN1_FittedSaddleSeat_%d'%(index+1),'IN1_FittedSaddleGasket_%d'%(index+1)] else 'requires_concealed_port' if o.name.startswith(('IN1_PorcelainPanel_','IN1_FixedRearShell_')) or o.name=='IN1_FixedMouthCheek05' else 'inspect_or_route_around'
                contacts.append({'mesh':o.name,'triangle_pairs':len(hits),'role':role})
        mouth=[]
        for frame in [1,181]:
            scene.frame_set(frame);bpy.context.view_layer.update()
            for o in bpy.data.objects:
                if o.type=='MESH' and o.name.startswith('IAM_'):
                    hits=envelope.overlap(geometry(o))
                    if hits:mouth.append({'frame':frame,'mesh':o.name,'triangle_pairs':len(hits)})
        scene.frame_set(1);bpy.context.view_layer.update();bpy.data.meshes.remove(m)
        rows.append({'foot':index+1,'center':[x,y],'radius':.05,'saddle_top_z':saddle_top,'core_shoe_z_range':[min(v.z for v in surface[0]),max(v.z for v in surface[0])],'envelope_contacts':contacts,'mouth_contacts':mouth})
    except AssertionError as error:rows.append({'foot':index+1,'center':[x,y],'failure':str(error)})
OUT=ROOT/'review/I_refinement/nautilus_r1/core_saddle_r14';OUT.mkdir(parents=True,exist_ok=True);(OUT/'support_envelope_plan.json').write_text(json.dumps({'source_sha256':s['source_sha256'],'rows':rows,'scope':'Read-only full-radius conservative columns between actual core underside and existing saddle. Lists surface-overlap candidates, not exact final contact or containment proof. No final tapered supports, fasteners or porcelain ports built.'},indent=2)+'\n');print(json.dumps(rows,indent=2),flush=True)
