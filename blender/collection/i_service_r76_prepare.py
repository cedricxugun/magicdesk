"""Shared preparation for the R76 authored service source (not main runtime)."""
import bpy, json, hashlib
from pathlib import Path
from mathutils import Vector, Quaternion
ROOT=Path(__file__).resolve().parents[2]

def depth(o):
    n=0
    while o.parent:n+=1;o=o.parent
    return n

def prepare(spec):
    source=ROOT/spec['source']
    assert hashlib.sha256(source.read_bytes()).hexdigest()==spec['source_sha256']
    bpy.ops.wm.open_mainfile(filepath=str(source));bpy.context.scene.frame_set(1)
    for row in spec['form_panels']:
        o=bpy.data.objects[row['node']];o.animation_data_clear()
        o.location=Vector(row['pivot_blender'])+Vector(row['lift_blender'])
        o.rotation_mode='QUATERNION';o.rotation_quaternion=Quaternion(Vector(row['axis_blender']),row['angle'])
        if 'mechanism' in row:
            m=row['mechanism']
            for k in ['carriage','rotor']:bpy.data.objects[m[k]].animation_data_clear()
            bpy.data.objects[m['carriage']].location=(0,0,m['stroke'])
            r=bpy.data.objects[m['rotor']];r.rotation_mode='QUATERNION'
            r.rotation_quaternion=Quaternion(Vector(m['axis_local_blender']),row['angle'])
    bpy.context.view_layer.update()
    body=bpy.data.objects['IN1_BodyRoot'];mouth=bpy.data.objects['IAM_MODULE']
    parts=list(dict.fromkeys(o for root in [body,mouth] for o in root.children_recursive if o.type=='MESH'))
    support=json.loads((ROOT/'review/I_refinement/nautilus_r1/port_edge_r68/release_probe/probe.json').read_text())
    front=json.loads((ROOT/'review/I_refinement/nautilus_r1/service_r63/stage03_wide/plan.json').read_text())
    rear=json.loads((ROOT/'review/I_refinement/nautilus_r1/rear03_release_r70/two_stage_r5/probe.json').read_text())
    assert support['source_sha256']==rear['source_sha256']==spec['seam_fasteners']['parent_source_sha256']
    offsets={o.name:Vector() if o.name in support['fixed_adapter_names'] else Vector((0,0,.45)) for o in parts}
    for row in support['groups']+support['legs']+support['ports']:
        for name in row['names']:offsets[name]+=Vector(row['offset'])
    for row in front['groups']:
        if row['id'] in ['cover_03','pin_cap_03','pin_03']:
            for name in row['meshes']:offsets[name]+=Vector(row['offset_blender'])
    for row in rear['groups']:
        delta=Vector(rear['shell_waypoints'][2]) if row['id']=='rear_shell03' else Vector(row['normal'])*(.810 if row['id'].startswith('rear_bolt') else .8)
        for name in row['names']:offsets[name]+=delta
    homes={o.name:o.matrix_world.copy() for o in parts}
    for o in sorted(parts,key=depth):
        tr=homes[o.name].copy();tr.translation+=offsets[o.name];o.matrix_world=tr
    bpy.context.view_layer.update()
    error=max(abs(o.matrix_world[r][c]-(homes[o.name][r][c]+(offsets[o.name][r] if c==3 and r<3 else 0))) for o in parts for r in range(4) for c in range(4))
    assert error<1e-6
    # Keep exactly the one original pedestal; no second full HELIOS donor is
    # imported into this editable animation source.
    bases=[o for o in bpy.data.objects if o.name=='BASE_FIXED']
    assert len(bases)==1
    keep=set([body,*body.children_recursive,mouth,*mouth.children_recursive,bases[0],*bases[0].children_recursive])
    for o in list(bpy.data.objects):
        if o not in keep:bpy.data.objects.remove(o,do_unlink=True)
    return body,mouth,parts,{'max_preparation_scalar_error':error,'offsets_blender':{n:list(v) for n,v in offsets.items()}}
