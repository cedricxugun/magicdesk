"""Replace only F's two cube-tooth rims in a private source copy; export mesh payload."""
import bpy,sys,math,json,hashlib,array
from pathlib import Path
from mathutils import Matrix,Vector
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(Path(__file__).parent))
from f_gear_geometry import *
SOURCE=ROOT/'blender/collection/F_refinement_candidate.blend'
TARGET=ROOT/'blender/collection/F_gear_refinement.blend'
OUT=ROOT/'review/F_complete/revision_20260911/gears';OUT.mkdir(exist_ok=True)
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
source_hash=sha(SOURCE);bpy.ops.wm.open_mainfile(filepath=str(SOURCE));bpy.context.scene.frame_set(1)
names=['F2_MainGear','F2_CounterGear'];roots=[bpy.data.objects[n] for n in names]
removed={o.name for root in roots for o in root.children_recursive if 'MachinedTooth' in o.name}
assert len(removed)==58,'Unexpected source; do not delete unknown geometry'
def fingerprint():
    g=hashlib.sha256();a=hashlib.sha256()
    for o in sorted(bpy.data.objects,key=lambda x:x.name):
        if o.name in removed or o.name.startswith('F4_InvoluteRim'):continue
        g.update(str((o.name,o.parent.name if o.parent else None,tuple(v for row in o.matrix_basis for v in row))).encode())
        if o.type=='MESH':
            vals=array.array('f',[0.])*(len(o.data.vertices)*3);o.data.vertices.foreach_get('co',vals);g.update(vals.tobytes())
            ids=array.array('i',[0])*len(o.data.loops);o.data.loops.foreach_get('vertex_index',ids);g.update(ids.tobytes())
    for action in sorted(bpy.data.actions,key=lambda x:x.name):
        if action.name==bpy.data.objects['F2_P_Differential'].animation_data.action.name:continue
        a.update(action.name.encode())
        for layer in action.layers:
            for strip in layer.strips:
                for bag in strip.channelbags:
                    for c in bag.fcurves:a.update(str((c.data_path,c.array_index,[(tuple(k.co),k.interpolation) for k in c.keyframe_points])).encode())
    return {'untouched_geometry_pose':g.hexdigest(),'animation_except_differential_disassembly':a.hexdigest()}
differential=bpy.data.objects['F2_P_Differential']
route_action=differential.animation_data.action
assert not any(o!=differential and o.animation_data and o.animation_data.action==route_action for o in bpy.data.objects)
before=fingerprint()
for idx,root in enumerate(roots):
    old=[o for o in root.children_recursive if o.name in removed]
    material=old[0].material_slots[0].material
    for obj in old:bpy.data.objects.remove(obj,do_unlink=True)
    outer=outline(TEETH[idx],PHASE[idx]);n=len(outer);inner_radius=[.146*.8,.090*.8][idx]
    inner=[(inner_radius*math.cos(math.atan2(z,x)),inner_radius*math.sin(math.atan2(z,x))) for x,z in outer]
    # Teeth sit in front of the vernier; a continuous rear shoulder seats on
    # the existing steel web. Axes/hubs stay fixed and service paths stay intact.
    shoulder_radius=min(inner_radius+.004,MODULE*(TEETH[idx]/2-1.25)-.001)
    shoulder=[(shoulder_radius*math.cos(math.atan2(z,x)),shoulder_radius*math.sin(math.atan2(z,x))) for x,z in outer]
    layers=[(outer,-.036),(inner,-.036),(outer,-.024),(shoulder,-.024),(shoulder,.006),(inner,.006)]
    verts=[(x,y,z) for ring,y in layers for x,z in ring]
    faces=[]
    for i in range(n):
        j=(i+1)%n
        for a,b in [(0,1),(2,0),(3,2),(4,3),(5,4),(1,5)]:
            faces.append((a*n+i,a*n+j,b*n+j,b*n+i))
    mesh=bpy.data.meshes.new('F4_RimMesh'+str(TEETH[idx]));mesh.from_pydata(verts,[],faces);mesh.update()
    obj=bpy.data.objects.new('F4_InvoluteRim'+str(TEETH[idx]),mesh);root.users_collection[0].objects.link(obj);obj.parent=root;mesh.materials.append(material)
    uv=mesh.uv_layers.new(name='UVMap')
    for poly in mesh.polygons:
        for loop in poly.loop_indices:
            v=mesh.vertices[mesh.loops[loop].vertex_index].co;uv.data[loop].uv=(v.x/.32+.5,v.z/.32+.5)
    # Correct winding without changing positions; each rim is a closed annulus.
    bpy.context.view_layer.objects.active=obj;obj.select_set(True)
    import bmesh
    bm=bmesh.new();bm.from_mesh(mesh);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(mesh);bm.free()
    bevel=obj.modifiers.new('Machined edge break','BEVEL');bevel.width=.00022;bevel.segments=3;bevel.limit_method='ANGLE';bevel.angle_limit=.6
    bevel.harden_normals=True
    mesh.set_sharp_from_angle(angle=.6)
    obj['teeth']=TEETH[idx];obj['module']=MODULE;obj['neutral_mesh_phase']=PHASE[idx]
take=json.loads((ROOT/'review/F_complete/revision_20260911/full_take/physical_take.json').read_text())
for axis in range(3):
    curve=route_action.fcurve_ensure_for_datablock(differential,'location',index=axis)
    curve.keyframe_points.clear();curve.keyframe_points.add(len(take['samples']));values=[]
    for sample in take['samples']:
        x,y,z=disassembly_offset(sample['explosion']);values.extend([sample['frame'],(x,-z,y)[axis]])
    curve.keyframe_points.foreach_set('co',values)
    for point in curve.keyframe_points:point.interpolation='LINEAR'
    curve.update()
bpy.context.scene.frame_set(1)
bpy.context.view_layer.update();after=fingerprint();assert before==after,'Non-tooth geometry or animation changed'
bpy.ops.wm.save_as_mainfile(filepath=str(TARGET));assert sha(SOURCE)==source_hash

# Export evaluated geometry in each existing gear root's local coordinate frame.
# Keeping the old GLB node graph/materials later avoids re-exporting unrelated parts.
C=Matrix(((1,0,0),(0,0,1),(0,-1,0)))
payload={}
for root in roots:
    groups={}
    for obj in root.children_recursive:
        if obj.type!='MESH':continue
        ev=obj.evaluated_get(bpy.context.evaluated_depsgraph_get());me=ev.to_mesh();me.calc_loop_triangles()
        matrix=root.matrix_world.inverted()@obj.matrix_world;normal_matrix=matrix.to_3x3().inverted().transposed()
        uv=me.uv_layers.active
        has_tangents=False
        if uv:
            try:me.calc_tangents(uvmap=uv.name);has_tangents=True
            except RuntimeError:pass
        for tri in me.loop_triangles:
            mat=obj.material_slots[tri.material_index].material
            name=mat.get('f_finish_source',mat.name)
            group=groups.setdefault(name,{'positions':[],'normals':[],'uv':[],'tangents':[],'indices':[],'lookup':{}})
            for li in tri.loops:
                loop=me.loops[li];point=C@(matrix@me.vertices[loop.vertex_index].co);normal=(C@(normal_matrix@me.corner_normals[li].vector)).normalized()
                tex=tuple(uv.data[li].uv) if uv else (0.,0.)
                tangent=(C@(matrix.to_3x3()@loop.tangent)).normalized() if has_tangents else normal.cross(Vector((0,1,0))).normalized()
                if tangent.length<.5:tangent=Vector((1,0,0))
                values=tuple(point)+tuple(normal)+(tex[0],1.-tex[1])+tuple(tangent)+(-loop.bitangent_sign if has_tangents else 1.,)
                index=group['lookup'].get(values)
                if index is None:
                    index=len(group['positions'])//3;group['lookup'][values]=index
                    group['positions'].extend(values[:3]);group['normals'].extend(values[3:6]);group['uv'].extend(values[6:8]);group['tangents'].extend(values[8:12])
                group['indices'].append(index)
        ev.to_mesh_clear()
    for group in groups.values():group.pop('lookup')
    payload[root.name+'_RenderSurface']=groups
(OUT/'mesh_payload.json').write_text(json.dumps(payload,separators=(',',':')))
report={'source_input_sha256':source_hash,'source_candidate_sha256':sha(TARGET),'source_candidate':str(TARGET.relative_to(ROOT)),'removed_teeth':len(removed),'teeth':TEETH,'module':MODULE,'distance':DISTANCE,'phase':PHASE,'backlash_per_tooth':BACKLASH,'tooth_plane_axial_offset':-.030,'tooth_width':.012,'continuous_shoulder_rear_y':.006,'preserved':after,'disassembly_route':DISASSEMBLY_ROUTE,'scope':'Two tooth rims and differential disassembly location track only; other geometry/animation and original source preserved. Engagement/adjacent clearance needs matching reports.'}
(OUT/'build.json').write_text(json.dumps(report,indent=2)+'\n');print('F_GEAR_BUILD',json.dumps(report),flush=True)
