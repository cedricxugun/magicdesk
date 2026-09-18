"""Report all sampled new-hardware surface contacts, without silently allowing them."""
import bpy, json, hashlib, itertools,sys
from pathlib import Path
from mathutils.bvhtree import BVHTree
from mathutils import Vector
ROOT=Path(__file__).resolve().parents[2]
args=sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else []
OUT=ROOT/(args[0] if args else 'review/I_refinement/part_a_mouth/shutter_r2/cassettes')
spec=json.loads((OUT/'build.json').read_text());source=ROOT/spec['source']
assert hashlib.sha256(source.read_bytes()).hexdigest()==spec['source_sha256']
bpy.ops.wm.open_mainfile(filepath=str(source));scene=bpy.context.scene
new=set(spec['new_parts']);foil={n for t in spec['tongues'] for n in t['mesh_names']}
objects=[o for o in bpy.data.objects if o.type=='MESH' and o.name not in foil]
deps=bpy.context.evaluated_depsgraph_get()
def geometry(o):
    e=o.evaluated_get(deps);m=e.to_mesh();m.calc_loop_triangles()
    vertices=[e.matrix_world@v.co for v in m.vertices];triangles=[tuple(t.vertices) for t in m.loop_triangles]
    e.to_mesh_clear()
    lo=[min(v[i] for v in vertices) for i in range(3)];hi=[max(v[i] for v in vertices) for i in range(3)]
    return BVHTree.FromPolygons(vertices,triangles,all_triangles=True),lo,hi
owners={}
for group in spec['tongues']:
    carriage=bpy.data.objects[group['carriage']]
    spool=bpy.data.objects[group['spool']]
    for o in [carriage,*carriage.children_recursive]:owners[o.name]='slide_'+str(group['tongue_index'])
    for o in [spool,*spool.children_recursive]:owners[o.name]='rotor_'+str(group['tongue_index'])
    if 'guide_roll' in group:
        guide=bpy.data.objects[group['guide_roll']['rotor']]
        for o in [guide,*guide.children_recursive]:owners[o.name]='guide_'+str(group['tongue_index'])
contacts=[];clearances=[];bores=[];mounts=[]
for frame in [1,65,113,169,209,281,337,393,433]:
    scene.frame_set(frame);bpy.context.view_layer.update()
    geom={o.name:geometry(o) for o in objects}
    for a,b in itertools.combinations(objects,2):
        if a.name not in new and b.name not in new: continue
        ta,la,ha=geom[a.name];tb,lb,hb=geom[b.name]
        if any(ha[i]<lb[i] or hb[i]<la[i] for i in range(3)): continue
        overlaps=ta.overlap(tb)
        if overlaps: contacts.append({'frame':frame,'a':a.name,'b':b.name,'triangles':len(overlaps)})
    for row in spec['interfaces']:
        bearing=bpy.data.objects[row['bearing']];spindle=bpy.data.objects[row['spindle']]
        rail=bpy.data.objects[row['rail']];slide=bpy.data.objects[row['slide']]
        axis=spindle.matrix_world.to_3x3()@Vector((0,0,1))
        axis.normalize();offset=bearing.matrix_world.translation-spindle.matrix_world.translation
        spindle_error=(offset-axis*offset.dot(axis)).length
        direction=rail.matrix_world.to_3x3()@Vector((0,0,1))
        direction.normalize();offset=slide.matrix_world.translation-rail.matrix_world.translation
        rail_error=(offset-direction*offset.dot(direction)).length
        clearances.append({'frame':frame,'index':row['index'],'bearing':row['bearing'],'spindle_axis_error':spindle_error,'rail_axis_error':rail_error})
        if frame==1:
            yoke=bpy.data.objects[row['bearing'].replace('Bearing','SlidingYoke')]
            yoke_tree=geom[yoke.name][0]
            actual_radii=[]
            for along in [-.016,0,.016]:
                point=slide.matrix_world.translation+direction*along
                actual_radii.append(yoke_tree.find_nearest(point)[3])
            bores.append({'yoke':yoke.name,'measured_linear_bore_radii':actual_radii,'minimum_required':.00515,'passed':min(actual_radii)>.00515})
            foot=bpy.data.objects[row['carrier_foot']]
            contact_point=foot.matrix_world@Vector((0,-.006,0))
            distance=geom['IAM_EyelidFixedCarrier'][0].find_nearest(contact_point)[3]
            mounts.append({'foot':foot.name,'measured_contact_gap':distance,'passed':distance<1e-5})
    print('CASSETTE_HARDWARE_FRAME',frame,len(contacts),flush=True)
relative_contacts=[c for c in contacts if owners.get(c['a'],'fixed')!=owners.get(c['b'],'fixed')]
result={'source_sha256':spec['source_sha256'],'contacts':contacts,'relative_motion_contacts':relative_contacts,'rigid_group_contacts':len(contacts)-len(relative_contacts),'alignment':clearances,'linear_bores':bores,'carrier_mounts':mounts,'alignment_and_bores_passed':all(b['passed'] for b in bores) and all(m['passed'] for m in mounts) and max(max(r['spindle_axis_error'],r['rail_axis_error']) for r in clearances)<1e-5,'scope':'Nine evaluated frames. Contacts between independently moving rotor/slide/fixed groups are separated from rigid assembly contacts, all raw contacts retained. REST bores and carrier contact gaps measured on actual meshes. No volume containment or continuous-motion certificate. Not art acceptance.'}
(OUT/'hardware_check.json').write_text(json.dumps(result,indent=2)+'\n')
print('CASSETTE_HARDWARE_FINISHED',len(contacts),flush=True)
