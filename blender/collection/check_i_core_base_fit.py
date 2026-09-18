"""Check C2 feet on the one actual shared BASE_FIXED, without changing its size."""
import bpy,json,hashlib,math,sys
import numpy as np
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree
ROOT=Path(__file__).resolve().parents[2];OUT=ROOT/'review/I_refinement/part_c_core/support_c2'
argument=next((a.split('=',1)[1] for a in sys.argv if a.startswith('--report=')),None)
if argument:OUT=(ROOT/argument).parent
spec=json.loads((OUT/'build.json').read_text())
assert hashlib.sha256((ROOT/spec['source']).read_bytes()).hexdigest()==spec['source_sha256']
assert hashlib.sha256((ROOT/'app/assets/helios_model.glb').read_bytes()).hexdigest()==spec['base_sha256']
bpy.ops.wm.open_mainfile(filepath=str(ROOT/spec['source']));bpy.context.scene.frame_set(1);bpy.context.view_layer.update()
bpy.ops.import_scene.gltf(filepath=str(ROOT/'app/assets/helios_model.glb'));base=bpy.data.objects['BASE_FIXED'];bpy.context.view_layer.update()
objects=[base]+list(base.children_recursive);points=[];triangles=[]
for o in objects:
    if o.type!='MESH':continue
    m=o.data;m.calc_loop_triangles();offset=len(points);points.extend(o.matrix_world@v.co for v in m.vertices);triangles.extend(tuple(i+offset for i in t.vertices) for t in m.loop_triangles)
array=np.array(points);size=np.ptp(array,axis=0);assert abs(size[0]-2.74)<.00001
tree=BVHTree.FromPolygons(points,triangles,all_triangles=True);samples=[];unexpected=[]
for index,row in enumerate(spec['support_layout']):
    foot=Vector(row['foot']);seat=bpy.data.objects['IC2_Leg_%02d_DeckSeat'%(index+1)];vertices=[seat.matrix_world@v.co for v in seat.data.vertices];bottom=min(v.z for v in vertices)
    boundary=[v for v in vertices if abs(v.z-bottom)<.00001];center=Vector((foot.x,foot.y,bottom))
    for fraction in [0.,.5,1.]:
        for vertex in boundary[:1] if fraction==0 else boundary:
            p=center+(vertex-center)*fraction;p.z=1.;hit=tree.ray_cast(p,Vector((0,0,-1)),2.)
            assert hit[0] is not None,('Foot leaves actual deck',p)
            samples.append({'anchor':row['anchor'],'fraction':fraction,'xy':[p.x,p.y],'actual_deck_z':hit[0].z,'foot_bottom_z':bottom,'gap':bottom-hit[0].z})
for name in spec['hardware']:
    if 'Deck' in name:continue
    o=bpy.data.objects[name];m=o.data;m.calc_loop_triangles();vertices=[o.matrix_world@v.co for v in m.vertices]
    if min(v.z for v in vertices)>array[:,2].max()+.0001:continue
    surface=BVHTree.FromPolygons(vertices,[tuple(t.vertices) for t in m.loop_triangles],all_triangles=True);hits=surface.overlap(tree)
    if hits:unexpected.append({'name':name,'triangles':len(hits)})
passed=not unexpected and max(abs(s['gap']) for s in samples)<.0001
report={'source_sha256':spec['source_sha256'],'component_sha256':spec['component_sha256'],'base_sha256':spec['base_sha256'],'passed':passed,'actual_base_bounds':[array.min(axis=0).tolist(),array.max(axis=0).tolist()],'actual_base_size':size.tolist(),'deck_samples':samples,'non_deck_hardware_contacts':unexpected,'scope':'Two C2 seat contact footprints on actual unscaled BASE_FIXED, plus non-seat support/base triangle contact. Does not certify full base controls/selector sweep or mechanical load capacity.'}
(OUT/'base_fit_check.json').write_text(json.dumps(report,indent=2)+'\n');print('C2_REAL_BASE_FIT',passed,max(abs(s['gap']) for s in samples),flush=True)
