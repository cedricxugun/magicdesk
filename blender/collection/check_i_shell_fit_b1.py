"""Check the static form around actual placed A, not a final panel sweep."""
import bpy,json,hashlib
from pathlib import Path
from mathutils.bvhtree import BVHTree
ROOT=Path(__file__).resolve().parents[2];OUT=ROOT/'review/I_refinement/part_b_shell/form_b1'
spec=json.loads((OUT/'build.json').read_text());source=ROOT/spec['source'];assert hashlib.sha256(source.read_bytes()).hexdigest()==spec['source_sha256']
mouth_spec=json.loads((ROOT/spec['mouth_report']).read_text())
bpy.ops.wm.open_mainfile(filepath=str(source));scene=bpy.context.scene;scene.frame_set(1);bpy.context.view_layer.update()
mouth=bpy.data.objects['IAM_Mouth'];existing=[o for o in bpy.data.collections['MODULE_IAM'].all_objects if o.type=='MESH']
layout=json.loads((ROOT/'app'/mouth_spec['music_optics_layout'].removeprefix('res://')).read_text())
assert hashlib.sha256((ROOT/layout['source']).read_bytes()).hexdigest()==layout['source_sha256']
with bpy.data.libraries.load(str(ROOT/layout['source']),link=False) as (src,dst):dst.objects=[name for name in src.objects if name.startswith('I_')]
loaded=[o for o in dst.objects if o is not None]
for o in loaded:bpy.context.collection.objects.link(o)
next(o for o in loaded if o.name=='I_MusicOptics').parent=mouth
existing.extend(o for o in loaded if o.type=='MESH' and o.name!=layout['sheet'])
def surface(o):
    e=o.evaluated_get(bpy.context.evaluated_depsgraph_get());m=e.to_mesh();m.calc_loop_triangles();p=[e.matrix_world@v.co for v in m.vertices]
    t=BVHTree.FromPolygons(p,[tuple(f.vertices) for f in m.loop_triangles],all_triangles=True);e.to_mesh_clear();return t
bpy.context.view_layer.update();body=surface(bpy.data.objects['IB1_OuterForm']);contacts=[]
for frame in [1,49,103,145,181,217,265,337,433]:
    scene.frame_set(frame);bpy.context.view_layer.update()
    for o in existing:
        overlap=body.overlap(surface(o))
        if overlap:contacts.append({'frame':frame,'part':o.name,'triangles':len(overlap),'interface_candidate':any(token in o.name for token in ['PorcelainUpper','PorcelainLower','EyelidFixedCarrier'])})
    print('B_FORM_FIT',frame,len(contacts),flush=True)
intrusions=[c for c in contacts if not c['interface_candidate']]
(OUT/'fit_check.json').write_text(json.dumps({'source_sha256':spec['source_sha256'],'component_sha256':spec['component_sha256'],'mouth_component_sha256':spec['mouth_component_sha256'],'moving_and_internal_surface_clear':not intrusions,'contacts':contacts,'intrusions':intrusions,'scope':'Static B form versus current A and physical optics in nine source poses. Fixed rim/carrier contacts are only marked as interface candidates, not accepted. Shell inner walls, panel opening, support/base and whole swept containment are not covered.'},indent=2)+'\n');print('I_B_FORM_FIT_CHECK',not intrusions,flush=True)
