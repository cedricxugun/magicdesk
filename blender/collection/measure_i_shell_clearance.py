"""Conservative radial clearance by axial slabs for the current A assembly."""
import bpy,json,hashlib
import numpy as np
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];OUT=ROOT/'review/I_refinement/part_b_shell/form_b1'
spec=json.loads((ROOT/'review/I_refinement/part_a_mouth/shutter_r2/collar_clamps/build.json').read_text())
assert hashlib.sha256((ROOT/spec['source']).read_bytes()).hexdigest()==spec['source_sha256']
bpy.ops.wm.open_mainfile(filepath=str(ROOT/spec['source']));scene=bpy.context.scene;scene.frame_set(1);bpy.context.view_layer.update()
mouth=bpy.data.objects['IAM_Mouth'];inv=mouth.matrix_world.inverted()
layout=json.loads((ROOT/'app'/spec['music_optics_layout'].removeprefix('res://')).read_text())
with bpy.data.libraries.load(str(ROOT/layout['source']),link=False) as (src,dst):dst.objects=[n for n in src.objects if n.startswith('I_')]
loaded=[o for o in dst.objects if o is not None]
for o in loaded:bpy.context.collection.objects.link(o)
next(o for o in loaded if o.name=='I_MusicOptics').parent=mouth
objects=[o for o in bpy.data.objects if o.type=='MESH' and o.name!=layout['sheet']]
scale=.85;edges=np.arange(-.40,.651,.05);maxima=np.zeros(len(edges)-1)
for frame in [1,49,103,145,181,217,265,337,433]:
    scene.frame_set(frame);bpy.context.view_layer.update();deps=bpy.context.evaluated_depsgraph_get()
    for o in objects:
        e=o.evaluated_get(deps);m=e.to_mesh();m.calc_loop_triangles();p=np.array([tuple(inv@e.matrix_world@v.co) for v in m.vertices])*scale
        tri=np.array([tuple(t.vertices) for t in m.loop_triangles]);e.to_mesh_clear()
        zmin=p[tri,2].min(axis=1);zmax=p[tri,2].max(axis=1);rmax=np.linalg.norm(p[tri,:2],axis=2).max(axis=1)
        for i,(a,b) in enumerate(zip(edges,edges[1:])):
            selected=(zmin<=b)&(zmax>=a)
            if selected.any():maxima[i]=max(maxima[i],float(rmax[selected].max()))
    print('A_CLEARANCE_FRAME',frame,flush=True)
profile=[]
for i,z in enumerate(edges):
    neighbours=maxima[max(0,i-1):min(len(maxima),i+1)]
    profile.append([float(z),float(max(.10,neighbours.max())+.008)])
(OUT/'mouth_clearance_profile.json').write_text(json.dumps({'source_sha256':spec['source_sha256'],'component_sha256':spec['component_sha256'],'uniform_scale':scale,'profile':profile,'slab_maximum_radius':maxima.tolist(),'margin':.008,'scope':'Nine current A source poses plus physical optics. Each slab uses full-triangle maximum radius conservatively, with adjacent maxima at profile knots. Not a continuous sweep or a shell wall-thickness specification.'},indent=2)+'\n');print('A_CLEARANCE_PROFILE_READY',flush=True)
