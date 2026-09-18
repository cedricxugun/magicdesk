"""Split-cage motion candidate. Detailed hinge/flange fabrication is a later gate."""
import bpy,bmesh,json,hashlib,math,shutil,sys
from pathlib import Path
from mathutils import Vector,Matrix,Euler
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(Path(__file__).parent))
from geometry import C,smooth
SOURCE=ROOT/'blender/collection/I_clearance_r6.blend';TARGET=ROOT/'blender/collection/I_service_r7_motion.blend'
OUT=ROOT/'review/I_refinement/service_r7';OUT.mkdir(parents=True,exist_ok=True)
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
input_spec=json.loads((ROOT/'review/I_refinement/clearance_r6/build.json').read_text());assert sha(SOURCE)==input_spec['source_sha256']
if TARGET.exists():
    old=json.loads((OUT/'build.json').read_text());assert sha(TARGET)==old['source_sha256'],'Unrecorded R7 motion-source edits'
    backup=TARGET.parent/'checkpoints'/('I-r7-motion-'+sha(TARGET)[:12]+'.blend');backup.write_bytes(TARGET.read_bytes())
bpy.ops.wm.open_mainfile(filepath=str(SOURCE));scene=bpy.context.scene;scene.frame_set(1)
root=bpy.data.objects['IH1_MODULE'];fixed=bpy.data.objects['IH1_FixedChamber'];upper=bpy.data.objects['IH1_UPPER']
col=bpy.data.collections.new('I_SPLIT_CAGE_MOTION_R7');scene.collection.children.link(col)
groups=json.loads(json.dumps(input_spec['groups']))
P=[Vector(v) for v in [(-.38,-.53,2.25),(-.15,.62,2.10),(.45,.78,2.82),(.45,.74,3.38)]]
def center(t):return P[0]*(1-t)**3+P[1]*3*(1-t)**2*t+P[2]*3*(1-t)*t*t+P[3]*t**3
def tangent(t):return ((P[1]-P[0])*(1-t)**2+(P[2]-P[1])*2*(1-t)*t+(P[3]-P[2])*t*t).normalized()
frames=[];last=tangent(0);normal=(Vector((0,0,1))-last*last.z).normalized()
for j in range(301):
    axis=tangent(j/300);normal=last.rotation_difference(axis)@normal;normal=(normal-axis*normal.dot(axis)).normalized();frames.append((normal.copy(),axis.cross(normal).normalized()));last=axis
def signed_side(point):
    i=min(range(301),key=lambda i:(center(i/300)-point).length_squared);return (point-center(i/300)).dot(frames[i][1])
def assign(obj,parent):
    world=obj.matrix_world.copy();obj.parent=parent;obj.matrix_world=world;bpy.context.view_layer.update()
cages={}
for side in [-1,1]:
    obj=bpy.data.objects.new('IS7_CageLeft' if side<0 else 'IS7_CageRight',None);col.objects.link(obj);obj.parent=fixed;obj.location=(side*.24,.10,1.46);cages[side]=obj
    groups.append({'name':obj.name,'members':[],'route':[{'at':0.,'offset':[0,0,0],'rotation':[0,0,0]},{'at':.30,'offset':[0,0,0],'rotation':[0,0,0]},{'at':.50,'offset':[0,0,0],'rotation':[0,side*.65,0]},{'at':1.,'offset':[0,0,0],'rotation':[0,side*.65,0]}]})
bpy.context.view_layer.update();split_rows=[]
for index in range(1,15):
    name='IH1_AcousticChamberRib_'+str(194+index).zfill(4);obj=bpy.data.objects[name]
    bpy.ops.object.select_all(action='DESELECT');obj.select_set(True);bpy.context.view_layer.objects.active=obj;bpy.ops.object.convert(target='MESH');obj=bpy.context.view_layer.objects.active
    t=.05+.83*index/14;plane=center(t);normal=frames[round(t*300)][1]
    for side in [-1,1]:
        piece=obj.copy();piece.data=obj.data.copy();piece.name=name+('_L' if side<0 else '_R');col.objects.link(piece)
        bm=bmesh.new();bm.from_mesh(piece.data);bmesh.ops.remove_doubles(bm,verts=list(bm.verts),dist=.000001)
        inverse=piece.matrix_local.inverted();no=(piece.matrix_local.to_3x3().transposed()@normal).normalized();point=inverse@plane
        result=bmesh.ops.bisect_plane(bm,geom=list(bm.verts)+list(bm.edges)+list(bm.faces),dist=1e-7,plane_co=point+no*side*.0015,plane_no=no,clear_inner=side>0,clear_outer=side<0)
        cut=[e for e in result['geom_cut'] if isinstance(e,bmesh.types.BMEdge) and e.is_boundary]
        if cut:bmesh.ops.holes_fill(bm,edges=cut,sides=0)
        bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(piece.data);bm.free();bpy.context.view_layer.update();assign(piece,cages[side])
        split_rows.append({'source':name,'part':piece.name,'side':side})
    bpy.data.objects.remove(obj,do_unlink=True)
for index,name in enumerate(input_spec['core_spines']):assign(bpy.data.objects[name],cages[1 if index<2 else -1])
for row in input_spec['frame_webs']:
    side=1 if (row.get('spine','') in input_spec['core_spines'][:2] or (row.get('rail_pair') and row['rail_pair'][0] in input_spec['core_spines'][:2])) else -1
    assign(bpy.data.objects[row['name']],cages[side])
guide_spec=json.loads((ROOT/'review/I_refinement/r1/guide_manifest.json').read_text());barrel_sides={}
for guide in guide_spec:
    obj=bpy.data.objects[guide['barrel']];t=(int(guide['panel'][-1])+.5)/6
    side=1 if (obj.location-center(t)).dot(frames[round(t*300)][1])>=0 else -1;barrel_sides[obj.name]=side;assign(obj,cages[side])
mounts=json.loads((ROOT/'review/I_refinement/assembly_r5/build.json').read_text())['guide_mounts']
for mount in mounts:
    for key in ['fused','clamp','saddle','web']:
        if key in mount:assign(bpy.data.objects[mount[key]],cages[barrel_sides[mount['barrel']]])
saddle_spec=json.loads((ROOT/'review/I_refinement/r2/build.json').read_text())['saddle_links']
for row in saddle_spec:
    obj=bpy.data.objects[row['name']];t=.05+.83*(int(row['rib'][-4:])-194)/14
    side=1 if (Vector(row['end'])-center(t)).dot(frames[round(t*300)][1])>=0 else -1;assign(obj,cages[side])
# Conductors are separated at the cage seam; connector fabrication is explicitly pending.
wire_rows=[]
for wire_index,obj in enumerate(sorted([o for o in fixed.children if o.type=='CURVE' and 'BrassReturnConductor' in o.name],key=lambda o:o.name)):
    points=[obj.matrix_local@Vector(p.co[:3]) for p in obj.data.splines[0].points];angles=[0.,math.pi*.66,math.pi*1.33]
    signs=[math.sin(angles[wire_index]+j/(len(points)-1)*math.tau*.7) for j in range(len(points))]
    segments=[];part=[points[0]];last_side=1 if signs[0]>=0 else -1
    for j,(a,b) in enumerate(zip(points,points[1:])):
        va=signs[j];vb=signs[j+1];side=1 if vb>=0 else -1
        if side!=last_side:
            cut=a.lerp(b,abs(va)/max(1e-10,abs(va)+abs(vb)));part.append(cut);segments.append((last_side,part));part=[cut]
        part.append(b);last_side=side
    segments.append((last_side,part))
    for index,(side,points_) in enumerate(segments):
        data=bpy.data.curves.new(obj.name+'_segment','CURVE');data.dimensions='3D';data.bevel_depth=obj.data.bevel_depth;data.bevel_resolution=3;data.use_fill_caps=True
        spline=data.splines.new('POLY');spline.points.add(len(points_)-1)
        for p,co in zip(spline.points,points_):p.co=(*co,1)
        for mat in obj.data.materials:data.materials.append(mat)
        wire=bpy.data.objects.new(obj.name+'_Segment'+str(index),data);col.objects.link(wire);wire.parent=fixed;bpy.context.view_layer.update();assign(wire,cages[side]);wire_rows.append({'source':obj.name,'part':wire.name,'side':side})
    bpy.data.objects.remove(obj,do_unlink=True)
def route(name,knots):
    item=next(g for g in groups if g['name']==name);item['route']=[{'at':at,'offset':list(offset)} for at,offset in knots]
quarter_nodes=[];front_splits=[]
body_rig=json.loads((ROOT/'app/assets/collection/i_runtime_rig.json').read_text());body_rig['panels']=[]
for index in range(6):
    name='IS4_FrontShell'+str(index);item=next(g for g in groups if g['name']==name);old_wrapper=bpy.data.objects[name]
    panel=bpy.data.objects['IH1_FrontPanel'+str(index)];panel.animation_data_clear();old_wrapper.animation_data_clear()
    direction=Vector(panel['open_direction']);stroke=panel['stroke'];scale=next(g['scale'] for g in guide_spec if g['panel']==panel.name)
    plane=center((index+.5)/6);normal=frames[round((index+.5)/6*300)][1];quarters={}
    for side in [-1,1]:
        suffix='_L' if side<0 else '_R'
        wrapper=bpy.data.objects.new('IS7_FrontShell'+str(index)+suffix,None);col.objects.link(wrapper);wrapper.parent=old_wrapper.parent;wrapper.matrix_world=old_wrapper.matrix_world.copy();bpy.context.view_layer.update();assign(wrapper,cages[side])
        actuator=bpy.data.objects.new('IH7_FrontPanel'+str(index)+suffix,None);col.objects.link(actuator);actuator.parent=wrapper;actuator.matrix_world=panel.matrix_world.copy();actuator['open_direction']=list(direction);actuator['stroke']=stroke
        quarters[side]=actuator;quarter_nodes.append(actuator)
        body_rig['panels'].append({'name':actuator.name,'direction':list((C@direction.to_4d()).xyz),'stroke':stroke})
        clear=direction*(stroke+.09*scale)
        groups.append({'name':wrapper.name,'members':[actuator.name],'route':[{'at':0.,'offset':[0,0,0]},{'at':.18,'offset':list(clear)},{'at':1.,'offset':list(clear)}]})
    bpy.context.view_layer.update()
    for obj in list(panel.children):
        if 'FrontPorcelain' in obj.name or 'RolledPanelLip' in obj.name:
            if obj.type=='CURVE':
                obj.data.use_fill_caps=True;bpy.ops.object.select_all(action='DESELECT');obj.select_set(True);bpy.context.view_layer.objects.active=obj;bpy.ops.object.convert(target='MESH');obj=bpy.context.view_layer.objects.active
            for side in [-1,1]:
                piece=obj.copy();piece.data=obj.data.copy();piece.name=obj.name+('_L' if side<0 else '_R');col.objects.link(piece)
                local=piece.matrix_world.inverted();point=local@(fixed.matrix_world@plane);no=(piece.matrix_world.to_3x3().transposed()@(fixed.matrix_world.to_3x3()@normal)).normalized()
                bm=bmesh.new();bm.from_mesh(piece.data);bmesh.ops.remove_doubles(bm,verts=list(bm.verts),dist=1e-6)
                result=bmesh.ops.bisect_plane(bm,geom=list(bm.verts)+list(bm.edges)+list(bm.faces),dist=1e-7,plane_co=point+no*side*.0015,plane_no=no,clear_inner=side>0,clear_outer=side<0)
                edges=[e for e in result['geom_cut'] if isinstance(e,bmesh.types.BMEdge) and e.is_boundary]
                if edges:bmesh.ops.holes_fill(bm,edges=edges,sides=0)
                bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(piece.data);bm.free()
                if len(piece.data.polygons)==0:bpy.data.objects.remove(piece,do_unlink=True);continue
                bpy.context.view_layer.update();assign(piece,quarters[side]);front_splits.append({'source':obj.name,'part':piece.name,'side':side})
            bpy.data.objects.remove(obj,do_unlink=True)
        else:
            if obj.type in ['MESH','CURVE']:point=sum((obj.matrix_world@Vector(v) for v in obj.bound_box),Vector())/8
            else:point=obj.matrix_world.translation
            side=1 if ((fixed.matrix_world.inverted()@point)-plane).dot(normal)>=0 else -1;assign(obj,quarters[side])
    groups.remove(item);bpy.data.objects.remove(panel,do_unlink=True);bpy.data.objects.remove(old_wrapper,do_unlink=True)
    for suffix in ['_A','_B']:
        name='IS4_RearShell'+str(index)+suffix;item=next(g for g in groups if g['name']==name)
        offset=Vector(item['route'][2]['offset'])*.10
        node=bpy.data.objects[name];node.animation_data_clear();assign(node,cages[-1 if suffix=='_A' else 1])
        route(name,[(0,Vector()),(.06,Vector()),(.22,offset),(1,offset)])
for name,a,b,c in [('IS4_IrisCartridge',.50,.60,.68),('IS4_PerforatedCartridge',.61,.69,.77),('IS4_DiaphragmCartridge',.73,.81,.89)]:
    item=next(g for g in groups if g['name']==name);axial=Vector(item['route'][-2]['offset']);park=Vector(item['route'][-1]['offset'])
    if name=='IS4_IrisCartridge':park=bpy.data.objects['IH1_Mouth'].matrix_world.inverted()@Vector((-1.50,-1.60,1.85))
    route(name,[(0,Vector()),(a,Vector()),(b,axial),(c,park),(1,park)])
bell=bpy.data.objects['IH1_Bellows'];axis=bell.matrix_local.to_3x3()@Vector((0,0,1))
park=fixed.matrix_world.inverted()@Vector((.0,-.4,3.80))-bell.location
route('IS4_ReservoirCartridge',[(0,Vector()),(.86,Vector()),(.91,axis*.065),(1,park)])
for side,node in cages.items():next(g for g in groups if g['name']==node.name)['members']=[c.name for c in node.children]
take=json.loads((ROOT/'review/I_refinement/clearance_r6/take.json').read_text())
for item in groups:bpy.data.objects[item['name']].animation_data_clear()
def at(route_,amount):
    for a,b in zip(route_,route_[1:]):
        if amount<=b['at']:
            t=smooth((amount-a['at'])/max(1e-9,b['at']-a['at']));return Vector(a['offset']).lerp(Vector(b['offset']),t),Vector(a.get('rotation',[0,0,0])).lerp(Vector(b.get('rotation',[0,0,0])),t)
    return Vector(route_[-1]['offset']),Vector(route_[-1].get('rotation',[0,0,0]))
homes={g['name']:bpy.data.objects[g['name']].location.copy() for g in groups}
for sample in take['samples']:
    for panel in quarter_nodes:
        panel.location=Vector(panel['open_direction'])*panel['stroke']*sample['opening'];panel.keyframe_insert('location',frame=sample['frame'])
    for item in groups:
        node=bpy.data.objects[item['name']];off,rot=at(item['route'],sample['service']['amount']);node.location=homes[node.name]+off;node.rotation_mode='XYZ';node.rotation_euler=rot
        node.keyframe_insert('location',frame=sample['frame']);node.keyframe_insert('rotation_euler',frame=sample['frame'])
scene.frame_set(1);scene.frame_end=1000
for image in bpy.data.images:
    if image.source=='FILE' and image.filepath and not image.packed_file:image.filepath=bpy.path.relpath(bpy.path.abspath(image.filepath),start=str(TARGET.parent))
bpy.ops.wm.save_as_mainfile(filepath=str(TARGET))
bpy.ops.object.select_all(action='DESELECT')
for obj in [root]+list(root.children_recursive):obj.select_set(True)
bpy.context.view_layer.objects.active=root;component=ROOT/'app/assets/collection/components/I_service_r7_motion.glb'
bpy.ops.export_scene.gltf(filepath=str(component),export_format='GLB',use_selection=True,export_apply=False,export_animations=False,export_morph=True,export_extras=True)
runtime=[]
for item in groups:
    rows=[]
    for k in item['route']:
        q=(C@Euler(k.get('rotation',[0,0,0])).to_matrix().to_4x4()@C.inverted()).to_quaternion()
        rows.append({'at':k['at'],'offset':list((C@Vector(k['offset']).to_4d()).xyz),'rotation':[q.x,q.y,q.z,q.w]})
    runtime.append({'name':item['name'],'route':rows})
shutil.copy2(ROOT/'review/I_refinement/clearance_r6/take.json',OUT/'take.json')
result={'source':str(TARGET.relative_to(ROOT)),'source_sha256':sha(TARGET),'input_source_sha256':sha(SOURCE),'component':str(component.relative_to(ROOT)),'component_sha256':sha(component),'groups':groups,'split_ribs':split_rows,'front_splits':front_splits,'conductor_segments':wire_rows,'barrel_cages':barrel_sides,'scope':'Split-cage motion prototype following built-in storyboard. Detailed rotating bearings, flange fasteners, wire contacts, saddle release and all-geometry/native validation are unfinished. Not main App or final art.'}
(OUT/'build.json').write_text(json.dumps(result,indent=2)+'\n')
(ROOT/'app/assets/collection/i_service_rig_r7.json').write_text(json.dumps({'source_sha256':sha(TARGET),'groups':runtime},indent=2)+'\n')
body_rig['source_sha256']=sha(TARGET);body_rig['component']='res://'+str(component.relative_to(ROOT/'app'));body_rig['component_sha256']=sha(component)
(ROOT/'app/assets/collection/i_runtime_rig_r7.json').write_text(json.dumps(body_rig,indent=2)+'\n')
print('I_SERVICE_R7_MOTION',len(groups),'groups',len(split_rows),'half ribs',flush=True)
