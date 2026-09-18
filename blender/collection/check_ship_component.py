"""Inspect evaluated saved G2 geometry and keyed source anchors, without changing the source."""
import bpy, sys, json, math, hashlib
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree
ROOT=Path(__file__).resolve().parents[2]
source=ROOT/'blender/collection/G_ship_r2.blend'
bpy.ops.wm.open_mainfile(filepath=str(source))
scene=bpy.context.scene;root=bpy.data.objects['GS2_Ship'];carrier=bpy.data.objects['GS2_HullCarrier']
def find(text, children=None):
    return next(o for o in (children if children is not None else root.children_recursive) if text in o.name)
def bvh(obj):
    e=obj.evaluated_get(bpy.context.evaluated_depsgraph_get());m=e.to_mesh()
    tree=BVHTree.FromPolygons([e.matrix_world@v.co for v in m.vertices],[list(p.vertices) for p in m.polygons])
    e.to_mesh_clear();return tree
cloth=[find('MainTailoredCloth'),find('JibTailoredCloth')]
shrouds=[o for o in root.children_recursive if 'FixedShroud' in o.name]
hull=find('LoftedPorcelainHull');cam_error=0.;sheet_error=0.;collisions=[];guide_errors=[]
frames=list(range(1,452,5))+[451]
for frame in frames:
    scene.frame_set(frame);bpy.context.view_layer.update()
    for i in range(3):
        cam=bpy.data.objects['GS2_Cam'+str(i)];wave=bpy.data.objects['GS2_Wave'+str(i)]
        disk=find('EccentricCam',cam.children_recursive);roller=find('CamFollowerRoller',wave.children_recursive)
        cam_error=max(cam_error,abs((disk.matrix_world.translation-roller.matrix_world.translation).length-.023))
        for sleeve in [o for o in wave.children_recursive if 'GuideSleeve' in o.name]:
            lo=sleeve.matrix_world.translation.z-.007;hi=sleeve.matrix_world.translation.z+.007
            if lo<.104 or hi>.162:guide_errors.append({'frame':frame,'node':sleeve.name,'z':[lo,hi]})
    for label in ['Main','Jib']:
        sail=bpy.data.objects['GS2_'+label+'Boom'];rope=bpy.data.objects[sail['sheet_name']]
        tip=sail.matrix_world@Vector((sail['side']*(sail['length']+.020),0,.028))
        x=.16 if sail['side']>0 else -.18
        cap=min([o for o in carrier.children_recursive if 'WinchCap' in o.name],key=lambda o:abs(o.location.x-x)+abs(o.location.y+.04))
        end=carrier.matrix_world@Vector((x+.008,-.04,.189+cap.location.z-.194))
        for j,target in [(0,tip),(33,end)]:
            actual=rope.matrix_world@rope.data.splines[0].points[j].co.xyz
            sheet_error=max(sheet_error,(actual-target).length)
    trees={o.name:bvh(o) for o in cloth+shrouds+[hull]}
    pairs=[(cloth[0],cloth[1])]+[(c,o) for c in cloth for o in shrouds+[hull]]
    for a,b in pairs:
        if trees[a.name].overlap(trees[b.name]):collisions.append({'frame':frame,'pair':[a.name,b.name]})
scene.frame_set(1);bpy.context.view_layer.update()
points=[]
for obj in root.children_recursive:
    if obj.type not in ['MESH','CURVE']:continue
    e=obj.evaluated_get(bpy.context.evaluated_depsgraph_get());m=e.to_mesh()
    points.extend(e.matrix_world@v.co for v in m.vertices);e.to_mesh_clear()
low=[min(v[i] for v in points) for i in range(3)];high=[max(v[i] for v in points) for i in range(3)]
cover=find('FittedEnamelAccessCover');deck_tree=bvh(find('FittedDeck'));seating=[]
for vertex in cover.data.vertices:
    point=cover.matrix_world@vertex.co
    hit,_,_,_=deck_tree.ray_cast(point+Vector((0,0,.02)),Vector((0,0,-1)))
    assert hit is not None, 'Cover extends outside actual deck'
    seating.append(point.z-hit.z)
assert min(seating)>.0018 and max(seating)<.0022,seating
report={'passed':not collisions and not guide_errors and sheet_error<1e-6 and cam_error<1e-6,
    'source_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),'sampled_frames':len(frames),
    'cam_roller_contact_max_error':cam_error,'sheet_anchor_max_error':sheet_error,
    'guide_travel_errors':guide_errors,'sail_surface_collisions':collisions,
    'cover_top_to_deck_gap':[min(seating),max(seating)],'rest_bounds':{'min':low,'max':high,'size':[high[i]-low[i] for i in range(3)]},
    'scope':'Evaluated source sail-vs-sail/shrouds/hull surfaces, actual cam/roller centers, keyed sheet endpoints and guide travel. Does not certify all hardware, hull internal fitting or player transfer clearances; no app acceptance.'}
out=ROOT/'review/G_optical_curator/ship_r2/source_check.json';out.write_text(json.dumps(report,indent=2)+'\n')
print('SHIP_SOURCE_CHECK',json.dumps(report),flush=True)
if not report['passed']:sys.exit(1)
