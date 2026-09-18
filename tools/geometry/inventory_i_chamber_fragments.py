"""Measure actual throat-side frame and membrane fragments before reconnecting."""
import bpy,bmesh,json,hashlib
from pathlib import Path
from mathutils import Vector
ROOT=Path(__file__).resolve().parents[2];source=ROOT/'review/I_refinement/nautilus_r1/chamber_seats_r9/build.json';spec=json.loads(source.read_text());assert hashlib.sha256((ROOT/spec['source']).read_bytes()).hexdigest()==spec['source_sha256'];bpy.ops.wm.open_mainfile(filepath=str(ROOT/spec['source']));bpy.context.scene.frame_set(1);bpy.context.view_layer.update();mouth_inverse=bpy.data.objects['IAM_MODULE'].matrix_world.inverted();rows=[]
for cell in range(4,10):
    for kind in ['Frame','Diaphragm']:
        name='IN1_Cell%s_%02d'%(kind,cell);o=bpy.data.objects[name];bm=bmesh.new();bm.from_mesh(o.data);bm.verts.ensure_lookup_table();bm.verts.index_update();unseen=set(bm.verts);parts=[]
        while unseen:
            stack=[unseen.pop()];vertices=set()
            while stack:
                v=stack.pop();vertices.add(v)
                for e in v.link_edges:
                    other=e.other_vert(v)
                    if other in unseen:unseen.remove(other);stack.append(other)
            faces={f for v in vertices for f in v.link_faces};points=[o.matrix_world@v.co for v in vertices];center=sum(points,Vector())/len(points);volume=0.
            for f in faces:
                p=[o.matrix_world@v.co-center for v in f.verts]
                for k in range(1,len(p)-1):volume+=p[0].dot(p[k].cross(p[k+1]))/6.
            local=[mouth_inverse@p for p in points]
            parts.append({'vertices':len(vertices),'faces':len(faces),'signed_volume_world':volume,'center':list(center),'bounds':{'min':[min(p[i] for p in points) for i in range(3)],'max':[max(p[i] for p in points) for i in range(3)]},'mouth_axial_range':[min(p.z for p in local),max(p.z for p in local)],'source_vertex_indices':sorted(v.index for v in vertices)})
        bm.free();parts.sort(key=lambda r:r['vertices'],reverse=True);rows.append({'cell':cell,'name':name,'parts':parts})
out=ROOT/'review/I_refinement/nautilus_r1/throat_chambers_r11';out.mkdir(parents=True,exist_ok=True);(out/'fragment_inventory.json').write_text(json.dumps({'source_sha256':spec['source_sha256'],'rows':rows,'scope':'Measured source components only; no parts removed and no connections declared complete.'},indent=2)+'\n');print(json.dumps([{'name':r['name'],'parts':[(p['vertices'],p['signed_volume_world'],p['center']) for p in r['parts']]} for r in rows]),flush=True)
