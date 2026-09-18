"""Machined Blender part helpers; configuration has no scene clearing or saving side effects."""
import bpy,bmesh,math
from mathutils import Vector
col=None
parts=[]
def configure(collection):
    global col
    col=collection
    parts.clear()

def empty(name, parent, loc=(0, 0, 0)):
    o = bpy.data.objects.new(name, None)
    col.objects.link(o)
    o.parent = parent
    o.location = loc
    return o

def finish(o, name, parent, loc, material, bevel=0):
    o.name = name
    for c in list(o.users_collection): c.objects.unlink(o)
    col.objects.link(o)
    o.parent = parent
    o.location = loc
    o.data.materials.clear()
    o.data.materials.append(bpy.data.materials['Collection_' + material])
    if bevel:
        m = o.modifiers.new('Machined edge', 'BEVEL')
        m.width = bevel; m.segments = 3
        bpy.context.view_layer.objects.active = o
        bpy.ops.object.modifier_apply(modifier=m.name)
    bm = bmesh.new(); bm.from_mesh(o.data)
    bmesh.ops.recalc_face_normals(bm, faces=list(bm.faces)); bm.to_mesh(o.data); bm.free()
    parts.append(o.name)
    return o

def box(name, dims, parent, loc, material='A_Dark', bevel=.0015):
    bpy.ops.mesh.primitive_cube_add(size=1)
    o = bpy.context.object; o.scale = dims
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    return finish(o, name, parent, loc, material, bevel)

def cylinder(name, radius, depth, parent, loc, material='A_Nickel', axis=(0,0,1), bevel=.0005):
    bpy.ops.mesh.primitive_cylinder_add(vertices=64, radius=radius, depth=depth)
    o = finish(bpy.context.object, name, parent, loc, material, bevel)
    o.rotation_mode = 'QUATERNION'; o.rotation_quaternion = Vector(axis).to_track_quat('Z','Y')
    for p in o.data.polygons: p.use_smooth = abs(p.normal.z) < .99
    return o

def drill(o, radius, depth, parent, loc, axis=(0,0,1),solver='EXACT'):
    tool = cylinder('CassetteDrill', radius, depth, parent, loc, axis=axis, bevel=0)
    bpy.context.view_layer.update(); bpy.context.view_layer.objects.active = o
    m = o.modifiers.new('Actual machined bore', 'BOOLEAN'); m.operation='DIFFERENCE'; m.solver=solver; m.object=tool
    bpy.ops.object.modifier_apply(modifier=m.name)
    parts.remove(tool.name); bpy.data.objects.remove(tool, do_unlink=True)

def sleeve(name, outer, inner, depth, parent, loc, material='A_Bronze', axis=(0,0,1)):
    # Explicit closed lathe profile avoids coincident Boolean seams in the bearing.
    n=64; verts=[]; faces=[]
    for r,z in [(outer,-depth/2),(outer,depth/2),(inner,depth/2),(inner,-depth/2)]:
        verts.extend((r*math.cos(i*math.tau/n),r*math.sin(i*math.tau/n),z) for i in range(n))
    for k in range(4):
        for i in range(n): faces.append((k*n+i,k*n+(i+1)%n,((k+1)%4)*n+(i+1)%n,((k+1)%4)*n+i))
    mesh=bpy.data.meshes.new(name+'Mesh'); mesh.from_pydata(verts,[],faces); mesh.update()
    uv=mesh.uv_layers.new(name='MachinedCylindricalUV')
    for face in mesh.polygons:
        angles=[(mesh.loops[li].vertex_index%n)/n for li in face.loop_indices]
        seam=max(angles)-min(angles)>.5
        for li,u in zip(face.loop_indices,angles):
            vi=mesh.loops[li].vertex_index
            uv.data[li].uv=(u+1 if seam and u<.5 else u,verts[vi][2]/depth+.5)
    o=bpy.data.objects.new(name,mesh); col.objects.link(o)
    finish(o,name,parent,loc,material)
    o.rotation_mode='QUATERNION'; o.rotation_quaternion=Vector(axis).to_track_quat('Z','Y')
    for p in mesh.polygons: p.use_smooth=p.index//n in [0,2]
    return o

def screw(name,parent,loc,r=.005,axis=(0,0,1)):
    head=cylinder(name,r,.004,parent,loc,'A_Nickel',axis)
    # Real hex socket recess; not a dark rectangle on a round head.
    bpy.ops.mesh.primitive_cylinder_add(vertices=6,radius=r*.49,depth=.003)
    tool=finish(bpy.context.object,'HexSocketTool',parent,Vector(loc)+Vector(axis)*.0016,'A_Dark')
    tool.rotation_mode='QUATERNION'; tool.rotation_quaternion=Vector(axis).to_track_quat('Z','Y')
    bpy.context.view_layer.update(); bpy.context.view_layer.objects.active=head
    m=head.modifiers.new('Recessed hex', 'BOOLEAN'); m.operation='DIFFERENCE'; m.solver='EXACT'; m.object=tool
    bpy.ops.object.modifier_apply(modifier=m.name); parts.remove(tool.name); bpy.data.objects.remove(tool,do_unlink=True)
    return head
