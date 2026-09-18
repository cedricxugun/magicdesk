"""Author actual chamber-edge emission coordinates without changing geometry."""
import bpy,json,hashlib,struct,math
from pathlib import Path
from mathutils import Vector
ROOT=Path(__file__).resolve().parents[2];OUT=ROOT/'review/I_refinement/nautilus_r1/chamber_response_r35';OUT.mkdir(parents=True,exist_ok=True);ART=ROOT/'app/assets/collection/art/I/chamber_response_r35';s=json.loads((ROOT/'review/I_refinement/nautilus_r1/uniform_precision_r29/build.json').read_text());sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();assert sha(ROOT/s['source'])==s['source_sha256'];bpy.ops.wm.open_mainfile(filepath=str(ROOT/s['source']));bpy.context.scene.frame_set(1);bpy.context.view_layer.update();body=bpy.data.objects['IN1_BodyRoot'];C=Vector((.12,.16,1.96));R=Vector((1.01,.67,1.10));rows=[]
def signature(o):
    h=hashlib.sha256();m=o.data;m.calc_loop_triangles()
    for v in m.vertices:h.update(struct.pack('<3f',*v.co))
    for t in m.loop_triangles:h.update(struct.pack('<3I',*t.vertices))
    for n in m.corner_normals:h.update(struct.pack('<3f',*n.vector))
    return [h.hexdigest(),[list(r)for r in o.matrix_world],[mat.name if mat else None for mat in m.materials]]
protected={o.name:signature(o)for o in bpy.data.objects if o.type=='MESH'}
for index,row in enumerate(s['acoustic_cells']):
    o=bpy.data.objects[row['frame']];m=o.data;assert len(m.uv_layers)==1;uv=m.uv_layers.new(name='ChamberConductorUV');coords=[];a,b=row['theta'];middle=(a+b)/2
    for v in m.vertices:
        p=o.matrix_world@v.co-C;phi=math.acos(max(-1.,min(1.,-p.y/(R.y-.052))));angle=math.atan2(p.z/(R.z-.052),p.x/(R.x-.052));theta=angle-1.12*math.cos(phi)
        for _ in range(8):theta=angle-1.12*math.cos(phi)-.10*math.sin(phi)**2*math.sin(theta+1.)
        theta=middle+(theta-middle+math.pi)%math.tau-math.pi;q=(theta-a)/(b-a)
        coords.append((phi/math.pi,q))
    for face in m.polygons:
        for li in face.loop_indices:uv.data[li].uv=coords[m.loops[li].vertex_index]
    # Put spill lights just outside the front-facing upper rim, where the
    # sampled curve has real geometry. Their shadows stay enabled at runtime.
    p=Vector(((R.x-.052)*math.sin(.8)*math.cos(middle+1.12*math.cos(.8)+.10*math.sin(.8)**2*math.sin(middle+1)),-(R.y-.052)*math.cos(.8),(R.z-.052)*math.sin(.8)*math.sin(middle+1.12*math.cos(.8)+.10*math.sin(.8)**2*math.sin(middle+1))))+C
    row_out={'frame':row['frame'],'diaphragm':row['diaphragm'],'cell_index':index,'uv2_layer':'ChamberConductorUV','band':index%3,'phase_offset':index/12.,'light_position_godot':[p.x,p.z,-p.y+.035],'light_enabled':index in [1,3,9],'samples':[{'vertex':i,'uv2':coords[i]}for i in range(0,len(coords),max(1,len(coords)//12))]};rows.append(row_out)
assert all(signature(bpy.data.objects[n])==value for n,value in protected.items())
source=ROOT/'blender/collection/I_nautilus_chamber_response_r35.blend';component=ROOT/'app/assets/collection/components/I_nautilus_chamber_response_r35.glb';assert not source.exists();bpy.ops.wm.save_as_mainfile(filepath=str(source),compress=True);bpy.ops.object.select_all(action='DESELECT')
for o in [body,*body.children_recursive]:o.select_set(True)
bpy.context.view_layer.objects.active=body;bpy.ops.export_scene.gltf(filepath=str(component),export_format='GLB',use_selection=True,export_animations=False,export_morph=False,export_extras=True)
layout={'source_sha256':sha(source),'component_sha256':sha(component),'mask':'res://assets/collection/art/I/chamber_response_r35/conductor_mask.png','mask_sha256':sha(ART/'conductor_mask.png'),'cells':rows,'scope':'Authored UV2 on existing chamber frames. Positions, render triangles, materials, source corner normals and transforms unchanged. Recording-band-driven material emission with three bounded shadowed spill lights; no new diaphragm deformation yet.'};(ART/'layout.json').write_text(json.dumps(layout,indent=2)+'\n')
d={**s,'source':str(source.relative_to(ROOT)),'source_sha256':sha(source),'component':str(component.relative_to(ROOT)),'component_sha256':sha(component),'parent_source_sha256':s['source_sha256'],'chamber_response_layout':'res://assets/collection/art/I/chamber_response_r35/layout.json','music_manifest':'res://assets/collection/art/I/chamber_response_r35/music_manifest.json','music_optics_layout':'res://assets/collection/art/I/moonlight_candidate/oblique_score_r34/layout.json','status':'authored_chamber_emission_candidate_runtime_review_pending'};(OUT/'build.json').write_text(json.dumps(d,indent=2)+'\n');(OUT/'protected_geometry.json').write_text(json.dumps({'source_sha256':d['source_sha256'],'passed':True,'protected_mesh_count':len(protected),'scope':'Source coordinates, actual triangles, material slots, corner normals and transforms remain equal; only extra UV2 is authored.'},indent=2)+'\n');print('CHAMBER_RESPONSE_SOURCE',d['source_sha256'],flush=True)
