"""Fork support R3 into grouped, reversible service anatomy; no live model replacement."""
import bpy,bmesh,json,hashlib,sys
from pathlib import Path
from mathutils import Vector,Matrix
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(Path(__file__).parent))
from geometry import C,smooth
SOURCE=ROOT/'blender/collection/I_support_r3.blend';TARGET=ROOT/'blender/collection/I_service_r4.blend'
OUT=ROOT/'review/I_refinement/service_r4';OUT.mkdir(parents=True,exist_ok=True)
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
assert sha(SOURCE)==json.loads((ROOT/'review/I_refinement/support_r3/build.json').read_text())['source_sha256']
if TARGET.exists():
    report=json.loads((OUT/'build.json').read_text());assert sha(TARGET)==report['source_sha256'],'Unrecorded service-source edit'
    backup=TARGET.parent/'checkpoints'/('I-service-'+sha(TARGET)[:12]+'.blend');backup.write_bytes(TARGET.read_bytes())
bpy.ops.wm.open_mainfile(filepath=str(SOURCE));scene=bpy.context.scene;scene.frame_set(1)
root=bpy.data.objects['IH1_MODULE'];upper=bpy.data.objects['IH1_UPPER'];fixed=bpy.data.objects['IH1_FixedChamber'];mouth=bpy.data.objects['IH1_Mouth']
original={o.name:o.matrix_world.copy() for o in [root]+list(root.children_recursive)}
col=bpy.data.collections.new('I_SERVICE_R4');scene.collection.children.link(col);groups=[]
P=[Vector(v) for v in [(-.38,-.53,2.25),(-.15,.62,2.10),(.45,.78,2.82),(.45,.74,3.38)]]
def center(t):return P[0]*(1-t)**3+P[1]*3*(1-t)**2*t+P[2]*3*(1-t)*t*t+P[3]*t**3
def tangent(t):return ((P[1]-P[0])*(1-t)**2+(P[2]-P[1])*2*(1-t)*t+(P[3]-P[2])*t*t).normalized()
frames=[];previous=tangent(0);normal=(Vector((0,0,1))-previous*previous.z).normalized()
for j in range(301):
    axis=tangent(j/300);normal=previous.rotation_difference(axis)@normal;normal=(normal-axis*normal.dot(axis)).normalized();frames.append((normal.copy(),axis.cross(normal).normalized()));previous=axis
def split_cover(obj,point,normal):
    pieces=[]
    for side in [-1,1]:
        piece=obj.copy();piece.data=obj.data.copy();piece.name=obj.name+('_A' if side<0 else '_B');col.objects.link(piece)
        inverse=piece.matrix_local.inverted();co=inverse@point;no=(piece.matrix_local.to_3x3().transposed()@normal).normalized()
        bm=bmesh.new();bm.from_mesh(piece.data)
        result=bmesh.ops.bisect_plane(bm,geom=list(bm.verts)+list(bm.edges)+list(bm.faces),dist=1e-6,plane_co=co+no*side*.0015,plane_no=no,clear_inner=side>0,clear_outer=side<0)
        edges=[e for e in result['geom_cut'] if isinstance(e,bmesh.types.BMEdge) and e.is_boundary]
        if edges:bmesh.ops.holes_fill(bm,edges=edges,sides=0)
        bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(piece.data);bm.free()
        pieces.append(piece)
    original.pop(obj.name,None);bpy.data.objects.remove(obj,do_unlink=True);return pieces
def group(name,parent,objects,route):
    obj=bpy.data.objects.new(name,None);col.objects.link(obj);obj.parent=parent
    for child in objects:
        local=child.matrix_local.copy();child.parent=obj;child.matrix_parent_inverse=Matrix.Identity(4);child.matrix_basis=local
    groups.append({'name':name,'node':obj,'members':[o.name for o in objects],'route':[{'at':at,'offset':list(offset)} for at,offset in route]});return obj
zero=Vector()
panels=[bpy.data.objects['IH1_FrontPanel'+str(i)] for i in range(6)]
for i,panel in enumerate(panels):
    direction=Vector(panel['open_direction']);stroke=panel['stroke'];start=.015*i
    outward=direction*stroke
    parked=direction*stroke*3.8+Vector((-.05*i,0,.045*i))
    group('IS4_FrontShell'+str(i),upper,[panel],[(0,zero),(.14,outward),(.60,outward),(.80,parked),(1,parked)])
    rear=next(o for o in fixed.children if 'RearPorcelain'+str(i)+'_' in o.name)
    t=(i+.5)/6;n,v=frames[round(t*300)];halves=split_cover(rear,center(t),v)
    if i==0:
        hood=next(o for o in fixed.children if 'RearPorcelainHood' in o.name)
        hood_halves=split_cover(hood,mouth.location,-mouth.matrix_local.to_3x3().col[0])
        struts=[o for o in fixed.children if 'HoodAttachmentStrut' in o.name]
    for side in [-1,1]:
        members=[halves[0 if side<0 else 1]]
        if i==0:
            members.append(hood_halves[0 if side<0 else 1])
            members += [o for o in struts if ((o.location-mouth.location).dot(v)<0)==(side<0)]
        n0,v0=frames[0];radial=(-n0*.10+v0*side*.995).normalized()
        outward=radial*.42
        parked=radial*.95+Vector((0,0,.38))
        group('IS4_RearShell'+str(i)+('_A' if side<0 else '_B'),fixed,members,[(0,zero),(.06,zero),(.28,outward),(.49,parked),(1,parked)])
direct=list(mouth.children)
plate=[o for o in direct if 'Perforated' in o.name]
membrane=[o for o in direct if any(s in o.name for s in ['Diaphragm','SpringSeat','CupMountFlange','PressureUnion'])]
# These front hub/calibration parts travel with the iris cartridge, clearing the plate.
iris=[o for o in direct if o not in plate+membrane and 'ShellSeatSeal' not in o.name]
assert len(plate)==2 and membrane and iris
def mouth_target(point):return mouth.matrix_world.inverted()@Vector(point)
iris_park=mouth_target((-1.50,-.55,1.85))
plate_park=mouth_target((2.02,-1.4,1.80))-Vector((0,0,.10))
diaphragm_park=mouth_target((-1.1,-1.5,3.4))-Vector((0,0,.28))
group('IS4_IrisCartridge',mouth,iris,[(0,zero),(.32,zero),(.60,Vector((0,0,-1.10))),(1,iris_park)])
group('IS4_PerforatedCartridge',mouth,plate,[(0,zero),(.62,zero),(.82,Vector((0,0,-.55))),(1,plate_park)])
group('IS4_DiaphragmCartridge',mouth,membrane,[(0,zero),(.76,zero),(.90,Vector((0,0,-.38))),(1,diaphragm_park)])
bell=bpy.data.objects['IH1_Bellows'];axis=bell.matrix_local.to_3x3()@Vector((0,0,1))
bell_park=fixed.matrix_world.inverted()@Vector((1.30,-1.1,3.45))-bell.location
group('IS4_ReservoirCartridge',fixed,[bell],[(0,zero),(.76,zero),(.90,axis*.60),(1,bell_park)])
bpy.context.view_layer.update()
home_error=max(max(abs(a-b) for row_a,row_b in zip(matrix,bpy.data.objects[name].matrix_world) for a,b in zip(row_a,row_b)) for name,matrix in original.items())
assert home_error<.00001,home_error
take=json.loads((OUT/'take.json').read_text());rig=json.loads((ROOT/'app/assets/collection/i_runtime_rig.json').read_text())
dia=bpy.data.objects['IH1_Diaphragm'];cam=bpy.data.objects[rig['cam']];front=bpy.data.objects[rig['front']];relief=bpy.data.objects[rig['relief']]
leaves=[bpy.data.objects[n] for n in rig['leaves']];wall=bpy.data.objects[rig['wall']]
travel=[bpy.data.objects[n] for n in [rig['surround']]+rig['springs']]
for node in panels+leaves+[dia,cam,front,relief]:node.animation_data_clear()
for obj in [wall]+travel:obj.data.shape_keys.animation_data_clear()
def offset(route,amount):
    for a,b in zip(route,route[1:]):
        if amount<=b['at']:
            t=smooth((amount-a['at'])/(b['at']-a['at']));return Vector(a['offset']).lerp(Vector(b['offset']),t)
    return Vector(route[-1]['offset'])
for sample in take['samples']:
    frame=sample['frame'];state=sample['state'];amount=sample['service']['amount'];d=max(-.014,min(.014,state['diaphragm']*40.))
    for item in groups:
        item['node'].location=offset(item['route'],amount);item['node'].keyframe_insert('location',frame=frame)
    for panel in panels:panel.location=Vector(panel['open_direction'])*panel['stroke']*sample['opening'];panel.keyframe_insert('location',frame=frame)
    for leaf in leaves:leaf.rotation_euler.z=leaf['home_angle']-1.05*state['iris'];leaf.keyframe_insert('rotation_euler',frame=frame)
    cam.rotation_euler.z=-.30*state['iris'];cam.keyframe_insert('rotation_euler',frame=frame)
    dia.location.z=.235-d;dia.keyframe_insert('location',frame=frame)
    front.location.z=-.23+.132*state['compression'];front.keyframe_insert('location',frame=frame)
    relief.location.z=.293+.012*(1. if state['stage'] in ['rest','recover'] else max(0.,min(1.,(1.-state['pressure'])*12.)));relief.keyframe_insert('location',frame=frame)
    wall.data.shape_keys.key_blocks['Compression'].value=state['compression'];wall.data.shape_keys.key_blocks['Compression'].keyframe_insert('value',frame=frame)
    for obj in travel:obj.data.shape_keys.key_blocks['Travel'].value=d/.014;obj.data.shape_keys.key_blocks['Travel'].keyframe_insert('value',frame=frame)
scene.render.fps=30;scene.frame_end=len(take['samples']);scene.frame_set(1)
for image in bpy.data.images:
    if image.source=='FILE' and image.filepath and not image.packed_file:image.filepath=bpy.path.relpath(bpy.path.abspath(image.filepath),start=str(TARGET.parent))
bpy.ops.wm.save_as_mainfile(filepath=str(TARGET))
bpy.ops.object.select_all(action='DESELECT')
for obj in [root]+list(root.children_recursive):obj.select_set(True)
bpy.context.view_layer.objects.active=root;component=ROOT/'app/assets/collection/components/I_service_r4.glb'
bpy.ops.export_scene.gltf(filepath=str(component),export_format='GLB',use_selection=True,export_apply=False,export_animations=False,export_morph=True,export_extras=True)
serial=[{k:v for k,v in g.items() if k!='node'} for g in groups]
runtime=[{'name':g['name'],'route':[{'at':r['at'],'offset':list((C@Vector(r['offset']).to_4d()).xyz)} for r in g['route']]} for g in serial]
result={'source':str(TARGET.relative_to(ROOT)),'source_sha256':sha(TARGET),'input_source_sha256':sha(SOURCE),'component':str(component.relative_to(ROOT)),'component_sha256':sha(component),'groups':serial,'original_home_matrix_error':home_error,'scope':'First service-route candidate; home transforms retained, includes pressure recovery and interrupted/reversed source take. Collision, readable layout, runtime replay and main App integration pending.'}
(OUT/'build.json').write_text(json.dumps(result,indent=2)+'\n')
(ROOT/'app/assets/collection/i_service_rig.json').write_text(json.dumps({'source_sha256':sha(TARGET),'groups':runtime},indent=2)+'\n')
print('I_SERVICE_R4',len(groups),'groups','home_error',home_error,flush=True)
