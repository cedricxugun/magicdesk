"""Read-only localization of the R73 collar defects and coupling bore walls."""
import bpy, bmesh, json, math, hashlib, sys
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'tools/geometry'))
from i_triangle_separation import separation
OUT = ROOT / 'review/I_refinement/nautilus_r1/coupling_repair_r76'
OUT.mkdir(parents=True, exist_ok=True)
source = ROOT / 'blender/collection/I_nautilus_seam_release_r73.blend'
bpy.ops.wm.open_mainfile(filepath=str(source))
bpy.context.scene.frame_set(1)
bpy.context.view_layer.update()
mount = bpy.data.objects['IC1_MouthMount']
inv = mount.matrix_world.inverted()
centers = [Vector((.502 * math.cos(math.pi/6+i*math.tau/6),
                   .502 * math.sin(math.pi/6+i*math.tau/6), 0)) for i in range(6)]
report = {'source_sha256': hashlib.sha256(source.read_bytes()).hexdigest(), 'collars': []}
for name in ['IC1_CollarUpper', 'IC1_CollarLower']:
    o = bpy.data.objects[name]
    m = o.data
    m.calc_loop_triangles()
    f = [tuple(t.vertices) for t in m.loop_triangles]
    local = [v.co.copy() for v in m.vertices]
    parent = [inv @ o.matrix_world @ v for v in local]
    world = [o.matrix_world @ v for v in local]
    row = {'name': name, 'vertices': len(local), 'triangles': len(f), 'spaces': {}, 'bores': []}
    for key, vertices in [('mesh', local), ('mount', parent), ('world', world)]:
        tree = BVHTree.FromPolygons(vertices, f, all_triangles=True)
        pairs = sorted((a,b) for a,b in tree.overlap(tree) if a<b and not set(f[a]) & set(f[b]))
        row['spaces'][key] = {'count': len(pairs), 'pairs': [
            {'triangles': [a,b], 'polygons': [m.loop_triangles[a].polygon_index, m.loop_triangles[b].polygon_index],
             'indices': [f[a], f[b]], 'parent_points': [[list(parent[k]) for k in f[t]] for t in (a,b)]}
            for a,b in pairs[:30]]}
        for item, (a,b) in zip(row['spaces'][key]['pairs'], pairs):
            item['same_space_double_separation'] = separation([tuple(vertices[k]) for k in f[a]],
                                                             [tuple(vertices[k]) for k in f[b]], 1e-12)
            item['source_double_separation'] = separation([tuple(local[k]) for k in f[a]],
                                                         [tuple(local[k]) for k in f[b]], 1e-12)
            item['source_polygons'] = [{'id':m.loop_triangles[t].polygon_index,
                'vertices':list(m.polygons[m.loop_triangles[t].polygon_index].vertices),
                'triangles':[list(tr.vertices) for tr in m.loop_triangles if tr.polygon_index==m.loop_triangles[t].polygon_index],
                'parent_points':[list(parent[k]) for k in m.polygons[m.loop_triangles[t].polygon_index].vertices]}
                for t in (a,b)]
    for index, c in enumerate(centers):
        if (name.endswith('Upper')) != (index < 3):
            continue
        close = [(i, p, math.hypot(p.x-c.x,p.y-c.y)) for i,p in enumerate(parent)
                 if math.hypot(p.x-c.x,p.y-c.y)<.0043 and .62<p.z<.642]
        ids = {i for i,_,_ in close}
        faces = [p for p in m.polygons if set(p.vertices).issubset(ids)]
        near = [p for p in m.polygons if set(p.vertices) & ids]
        row['bores'].append({'index': index, 'center': list(c), 'vertices': len(close),
            'z_stations': sorted(set(round(p.z,8) for _,p,_ in close)),
            'radii': sorted(set(round(r,8) for _,_,r in close)),
            'wall_faces': [{'id':p.index,'vertices':list(p.vertices), 'normal':list(p.normal)} for p in faces],
            'adjacent_faces': len(near),
            'points': [{'i':i, 'p':list(p), 'r':r} for i,p,r in close]})
    report['collars'].append(row)
    print('COLLAR', name, {k:v['count'] for k,v in row['spaces'].items()},
          [(b['index'],b['vertices'],len(b['wall_faces']),b['z_stations'],b['radii']) for b in row['bores']], flush=True)
(OUT/'source_diagnostic.json').write_text(json.dumps(report, indent=2)+'\n')
# Analyze the old station generator without changing it or using its failed output.
cut=.6352; tip=.628
stations=[cut+(tip-cut)*i/144 for i in range(1,145)]
female=sorted({.628,.6345}|{z for z in stations if .628<z<.6345},reverse=True)
print('NEAR_STATIONS', [(a,b,a-b) for a,b in zip(female,female[1:]) if a-b<1e-8], flush=True)
