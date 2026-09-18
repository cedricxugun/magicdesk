"""Feature edges extracted from final geometry, in each curiosity's coordinates."""
import bpy,bmesh,math
from mathutils import Vector
from geometry import C

def extract(root,limit=2200):
    bpy.context.view_layer.update();deps=bpy.context.evaluated_depsgraph_get();edges={}
    inverse=root.matrix_world.inverted()
    for obj in root.children_recursive:
        if obj.type not in ['MESH','CURVE','FONT']:continue
        ev=obj.evaluated_get(deps);mesh=ev.to_mesh()
        if not mesh:continue
        bm=bmesh.new();bm.from_mesh(mesh);matrix=inverse@obj.matrix_world
        for edge in bm.edges:
            if len(edge.link_faces)==2 and edge.calc_face_angle(0)<math.radians(32):continue
            a,b=[matrix@v.co for v in edge.verts]
            if (a-b).length<.010:continue
            aa=tuple(round(x,5) for x in (C@a.to_4d()).xyz);bb=tuple(round(x,5) for x in (C@b.to_4d()).xyz)
            edges[tuple(sorted((aa,bb)))]=(list(aa),list(bb))
        bm.free();ev.to_mesh_clear()
    values=list(edges.values())
    if len(values)>limit:values=[values[int(i*len(values)/limit)] for i in range(limit)]
    return values
