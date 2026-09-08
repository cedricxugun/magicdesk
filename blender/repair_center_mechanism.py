"""Local repair only: compact low terminals and registered, ordered center extraction.
Does not rebuild the model, regenerate textures, or change control/button names.
"""
import bpy,bmesh,json,math,pathlib
from mathutils import Matrix,Vector,Quaternion
ROOT=pathlib.Path(__file__).resolve().parents[1];S=bpy.context.scene;S.frame_set(1)
M=json.loads((ROOT/'app/assets/mechanism.json').read_text(encoding='utf8'))
C=Matrix(((1,0,0,0),(0,0,1,0),(0,-1,0,0),(0,0,0,1)))
def tr(d):
 q=d['q'];return C.inverted()@Matrix.LocRotScale(Vector(d['p']),Quaternion((q[3],q[0],q[1],q[2])),Vector(d['s']))@C
def sm(t):t=max(0,min(1,t));return t*t*(3-2*t)
def path(*values):return [{'at':float(t),'offset':list(p)}for t,p in values]
M['gyro_align']={k:[0,0,0,1]for k in ['outer','middle','inner','core']}
M['explosion_choreography']={'align_end':.18,'description':'Register gimbals; lift core carrier; withdraw nested rings along their common normal; retain crystal inside its complete cage.'}
central=['P_Gimbal_0_Ring','P_Gimbal_1_Ring','P_Gimbal_2_Ring','P_Middle_Trunnions','P_Inner_Trunnions','P_Solar_Crystal','P_Solar_Lattice','P_Core_Bottom_Bearing']
normal={'P_Gimbal_0_Ring':0,'P_Middle_Trunnions':0,'P_Core_Bottom_Bearing':0,'P_Gimbal_1_Ring':.30,'P_Inner_Trunnions':.30,'P_Gimbal_2_Ring':.60,'P_Solar_Crystal':1.0,'P_Solar_Lattice':1.0}
for p in M['parts']:
 if p['name']in central:
  z=normal[p['name']]
  p['explode_path']=path((0,(0,0,0)),(.18,(0,0,0)),(.36,(0,.52,0)),(.72,(0,.52,z)),(1,(-.48,.52,z)))
  p['explode_spin']=0.0
 elif p['name']=='P_Core_Support_Post':
  p['explode_path']=path((0,(0,0,0)),(.38,(0,0,0)),(.55,(0,.14,0)),(.84,(.85,.14,-.35)),(1,(.85,.14,-.35)));p['explode_spin']=0.0
 elif p['name']=='P_Socket_Crown':
  p['explode_path']=path((0,(0,0,0)),(.56,(0,0,0)),(.68,(0,.14,0)),(1,(.75,.14,.38)));p['explode_spin']=0.0
 elif p['name']=='P_Lower_Stator':
  p['explode_path']=path((0,(0,0,0)),(.72,(0,0,0)),(1,(0,.05,-.62)));p['explode_spin']=0.0
fixes=[]
M['electrical_contacts']={'Thermal_Valve_Frame':[0,.59,0],'Thermal_Valve_Frame.001':[0,.27,0],'Thermal_Valve_Frame.002':[0,.27,0]}
for j in [1,2]:
 parent=bpy.data.objects['P_Thermal_Valve_%d'%j]
 if parent.get('clearance_revision')==3:continue
 frame=bpy.data.objects['Thermal_Valve_Frame'+('.001'if j==1 else'.002')]
 old=frame.location.copy();rad=Vector((old.x,old.y,0)).normalized();base=rad*.22+Vector((0,0,1.20))
 existing=next(ob for ob in parent.children if ob.type=='MESH')
 vertices=[];faces=[];material_ids=[];uvs=[]
 keys=['Ivory_Enamel','Dark_Brushed_Steel','Polished_Nickel','Warm_Nickel','Black_Polymer']
 def cylinder(radius,depth,z,matindex,segments=64):
  bevel=min(.003,depth*.15);profile=[(radius-bevel,z-depth*.5),(radius,z-depth*.5+bevel),(radius,z+depth*.5-bevel),(radius-bevel,z+depth*.5)]
  start=len(vertices)
  for r,zz in profile:
   for k in range(segments):
    aa=k*math.tau/segments;vertices.append(tuple(base+Vector((r*math.cos(aa),r*math.sin(aa),zz))));uvs.append((k/segments,(zz-z)/max(depth,.001)+.5))
  for row in range(3):
   for k in range(segments):faces.append((start+row*segments+k,start+row*segments+(k+1)%segments,start+(row+1)*segments+(k+1)%segments,start+(row+1)*segments+k));material_ids.append(matindex)
  faces.append(tuple(start+k for k in range(segments-1,-1,-1)));material_ids.append(matindex)
  faces.append(tuple(start+segments*3+k for k in range(segments)));material_ids.append(matindex)
 cylinder(.077,.028,.0,1)
 cylinder(.056,.177,.092,2)
 for zz in [.031,.078,.125,.172]:cylinder(.09,.026,zz,0)
 cylinder(.065,.010,.196,3)
 cylinder(.054,.035,.216,1)
 cylinder(.049,.017,.242,2)
 cylinder(.012,.025,.2575,2)
 me=bpy.data.meshes.new(existing.data.name+'_CompactFeedthrough');me.from_pydata(vertices,[],faces)
 for key in keys:me.materials.append(bpy.data.materials[key])
 layer=me.uv_layers.new(name='UVMap')
 for poly,matid in zip(me.polygons,material_ids):
  poly.material_index=matid;poly.use_smooth=len(poly.vertices)==4
  for li in poly.loop_indices:layer.data[li].uv=uvs[me.loops[li].vertex_index]
 color=me.color_attributes.new(name='CavityAO',type='FLOAT_COLOR',domain='CORNER')
 for item in color.data:item.color=(1,1,1,1)
 me.color_attributes.active_color_index=0;me.color_attributes.render_color_index=0
 existing.data=me;existing.matrix_basis=Matrix.Identity(4)
 frame.location=base;frame.scale=(1,1,1);parent['clearance_revision']=3
 fixes.append({'name':parent.name,'new_blender':list(base),'disc_radius':.09,'disc_thickness':.026,'disc_centers':[1.231,1.278,1.325,1.372],'anode_top':1.47})
def path_offset(p,ex):
 if 'explode_path'not in p:
  return Vector(p['offset'])*sm((ex-p['stage'])/.7),p['spin']*sm((ex-p['stage'])/.7)
 rows=p['explode_path']
 for a,b in zip(rows,rows[1:]):
  if ex<=b['at']:return Vector(a['offset']).lerp(Vector(b['offset']),sm((ex-a['at'])/(b['at']-a['at']))),p.get('explode_spin',0)*ex
 return Vector(rows[-1]['offset']),p.get('explode_spin',0)*ex
def pose(op,phase,ex):
 for c in M['controls']:
  pos=max(0,min(100,op*100));a=tr(c['samples'][int(pos)]);b=tr(c['samples'][min(100,int(pos)+1)]);p0,q0,s0=a.decompose();p1,q1,s1=b.decompose();bpy.data.objects[c['name']].matrix_basis=Matrix.LocRotScale(p0.lerp(p1,pos%1),q0.slerp(q1,pos%1),s0.lerp(s1,pos%1))
 turn=bpy.data.objects['TURNTABLE'];turn.rotation_euler=(0,0,0)
 align=sm(ex/.18)
 for key,ang,axis in [('outer',.2+phase*.65,(0,0,1)),('middle',.6+math.sin(phase*.55)*.9,(1,0,0)),('inner',.7+phase,(0,0,1)),('core',phase*.8,(1,0,0))]:
  ob=bpy.data.objects[M['gyro'][key]];ob.rotation_mode='QUATERNION';ob.rotation_quaternion=Quaternion(axis,ang).slerp(Quaternion((1,0,0,0)),align)
 for p in M['parts']:bpy.data.objects[p['name']].matrix_basis=tr(p['home'])
 bpy.context.view_layer.update()
 for p in M['parts']:
  delta,spin=path_offset(p,ex);ob=bpy.data.objects[p['name']];loc,rot,sc=tr(p['home']).decompose()
  ob.location=loc+ob.parent.matrix_world.to_3x3().inverted()@C.inverted().to_3x3()@delta;ob.rotation_mode='QUATERNION';ob.rotation_quaternion=rot@Quaternion((0,0,1),spin);ob.scale=sc
 bpy.context.view_layer.update()
if '--apply' in __import__('sys').argv:
 # Change only the extraction/assembly segment. Existing synchronized bloom,
 # actuators, button presses, material animation and camera settings remain intact.
 anim=[bpy.data.objects[M['gyro'][key]]for key in M['gyro']]+[bpy.data.objects[p['name']]for p in M['parts'] if 'explode_path'in p]
 # Quaternion registration needs quaternion channels. Capture the previous
 # gimbal orientations outside extraction first, preserving the exact old motion.
 previous_gyro_keys={name:[]for name in M['gyro'].values()}
 for f in range(1,601):
  if 250<=f<=465:continue
  S.frame_set(f)
  for name in previous_gyro_keys:previous_gyro_keys[name].append((f,bpy.data.objects[name].matrix_basis.to_quaternion().copy()))
 for name,keys in previous_gyro_keys.items():
  ob=bpy.data.objects[name];ob.rotation_mode='QUATERNION'
  for f,q in keys:ob.rotation_quaternion=q;ob.keyframe_insert('rotation_quaternion',frame=f)
 for f in range(250,466):
  S.frame_set(f)
  if f<320:op=1-sm((f-260)/36);ph=18.125;ex=1-(1-max(0,min(1,(f-260)/45)))**3
  elif f<375:op=0;ph=18.125;ex=1
  else:op=0;ph=18.125;ex=1-sm((f-375)/75)
  # Read the original controller pose; pose() is used transiently for the repair.
  control_matrices={c['name']:bpy.data.objects[c['name']].matrix_basis.copy()for c in M['controls']}
  pose(op,ph,ex)
  for ob in anim:
   for channel in ['location','scale','rotation_quaternion']:ob.keyframe_insert(channel,frame=f)
  for name,matrix in control_matrices.items():bpy.data.objects[name].matrix_basis=matrix
 S.frame_set(1);bpy.data.objects['TURNTABLE'].rotation_euler=(0,0,0)
 (ROOT/'app/assets/mechanism.json').write_text(json.dumps(M,ensure_ascii=False,separators=(',',':')),encoding='utf8')
 bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'blender/Helios_Incubator.blend'),compress=True)
 core_tree=bpy.data.materials['Solar_Core_Emission'].node_tree
 if core_tree.animation_data:core_tree.animation_data.action=None
 core_tree.nodes.get('Principled BSDF').inputs['Emission Strength'].default_value=.8
 bpy.ops.object.select_all(action='DESELECT')
 for ob in bpy.data.collections['HELIOS_ASSET'].objects:ob.select_set(True)
 bpy.context.view_layer.objects.active=bpy.data.objects['HELIOS_ROOT']
 bpy.ops.export_scene.gltf(filepath=str(ROOT/'app/assets/helios_model.glb'),export_format='GLB',use_selection=True,export_animations=False,export_extras=True,export_apply=True,export_vertex_color='ACTIVE',export_all_vertex_colors=True)
 print('LOCAL_CENTER_REPAIR_EXPORTED',fixes,flush=True)
