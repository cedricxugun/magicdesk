"""R83 acoustic optics: retained functional cartridge, directional reading heads
and an upright transparent real-score carrier. Separate runtime components.
"""
import bpy,bmesh,json,math,hashlib,struct,sys
from pathlib import Path
from mathutils import Vector,Matrix
R=Path(__file__).resolve().parents[2];sys.path.insert(0,str(Path(__file__).parent))
import i_machined_geometry as P
OUT=R/'review/I_refinement/nautilus_reset_r82/music_interface_r1'
CENTERED='--reader-centered' in sys.argv
suffix='r2' if CENTERED else 'r1'
ART=R/'app/assets/collection/art/I/r82_music_interface'
if CENTERED:ART=ART/'r2'
ART.mkdir(parents=True,exist_ok=True)
SRC=R/('blender/collection/I_r82_acoustic_optics_'+suffix+'.blend')
COMP=R/('app/assets/collection/components/I_r82_acoustic_optics_'+suffix+'.glb')
assert not SRC.exists() and not COMP.exists()
seed=json.loads((OUT/'core_build.json').read_text());fit=json.loads((OUT/'fit_search.json').read_text())
old_layout=json.loads((R/'app/assets/collection/art/I/desktop_optics_r60/score_layout.json').read_text())
bpy.ops.wm.open_mainfile(filepath=str(R/seed['source']));scene=bpy.context.scene;scene.frame_set(1)
col=bpy.data.collections['MODULE_IAM'];P.configure(col);mouth=bpy.data.objects['IAM_Mouth'];root=bpy.data.objects['IAM_MODULE']
def fingerprint(o):
 h=hashlib.sha256()
 for v in o.data.vertices:h.update(struct.pack('<3f',*v.co))
 for p in o.data.polygons:h.update(struct.pack('<I',len(p.vertices)));h.update(struct.pack('<'+'I'*len(p.vertices),*p.vertices))
 for uv in o.data.uv_layers:
  h.update(uv.name.encode())
  for p in uv.data:h.update(struct.pack('<2f',*p.uv))
 if o.data.shape_keys:
  for k in o.data.shape_keys.key_blocks:
   h.update(k.name.encode())
   for v in k.data:h.update(struct.pack('<3f',*v.co))
 for row in o.matrix_world:h.update(struct.pack('<4f',*row))
 return h.hexdigest()
protected={o.name:fingerprint(o)for o in bpy.data.objects if o.type=='MESH'}
M=Matrix(fit['placement']['matrix_blender']);SCALE=.55
M=Matrix.Translation(M.translation)@M.to_3x3().normalized().to_4x4()@Matrix.Diagonal((SCALE,SCALE,SCALE,1.))
C=Vector(fit['placement']['center'])
hero_to_viewer=Vector((-4,-7,3.65))-C
reader_n=Vector((hero_to_viewer.x,hero_to_viewer.y,0)).normalized() if CENTERED else Vector((-.42,-.9075,0)).normalized()
vertical=Vector((0,0,1));horizontal=vertical.cross(reader_n).normalized()
score_center=C+hero_to_viewer.normalized()*.30 if CENTERED else C+Vector((0,-.29,.025))
score_focus=score_center+reader_n*.007
mouth_to_world=M@mouth.matrix_world;world_to_mouth=mouth_to_world.inverted()
def material(n,color,metal,rough,coat=0,trans=0):
 ma=bpy.data.materials.new('Collection_'+n);ma.use_nodes=True;b=ma.node_tree.nodes.get('Principled BSDF')
 b.inputs['Base Color'].default_value=(*color,1);b.inputs['Metallic'].default_value=metal;b.inputs['Roughness'].default_value=rough
 b.inputs['Coat Weight'].default_value=coat;b.inputs['Coat Roughness'].default_value=.08
 b.inputs['Transmission Weight'].default_value=trans;b.inputs['IOR'].default_value=1.46
 return ma
lens_mat=material('A_ReadLens',(.58,.34,.10),.02,.10,.7,.28)
head_mat=material('A_ReadHead',(.49,.43,.32),.92,.20)
def sphere(n,radii,parent,loc,ma):
 bpy.ops.mesh.primitive_uv_sphere_add(segments=48,ring_count=24,radius=1)
 o=bpy.context.object;o.scale=radii;bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
 P.finish(o,n,parent,loc,ma)
 for p in o.data.polygons:p.use_smooth=True
 return o
def curve(n,pts,parent,rad,ma):
 cu=bpy.data.curves.new(n+'Curve','CURVE');cu.dimensions='3D';cu.resolution_u=1;cu.bevel_depth=rad;cu.bevel_resolution=4;cu.use_fill_caps=True
 sp=cu.splines.new('POLY');sp.points.add(len(pts)-1)
 for i,(p,v)in enumerate(zip(sp.points,pts)):p.co=(*v,1);p.radius=1+.28*math.sin(math.pi*i/(len(pts)-1))
 o=bpy.data.objects.new(n,cu);col.objects.link(o);o.parent=parent;cu.materials.append(bpy.data.materials['Collection_'+ma]);return o
def bez(a,b,c,d,t):return Vector(a)*(1-t)**3+Vector(b)*3*t*(1-t)**2+Vector(c)*3*t*t*(1-t)+Vector(d)*t**3
with bpy.data.libraries.load(str(R/'blender/collection/I_scan_cap_r41.blend'),link=False)as(src,dst):dst.objects=['I_ScanCapHousing','I_ScanCapSeal']
templates=dst.objects
tips=[];physical_heads=[]
for i in range(3):
 tine=bpy.data.objects['IAM_TineRoundedAxial_'+str(i)]
 for template in templates:
  o=template.copy();o.data=template.data.copy();o.name='I83_FittedSocket_'+str(i)+'_'+template.name;col.objects.link(o);o.parent=tine;o.matrix_parent_inverse.identity();o.matrix_basis=template.matrix_basis.copy()
 spread=(i-1)*.035
 centre=Vector((0,spread,-.038));socket=Vector((0,0,-.0105))
 pts=[bez(socket,socket+Vector((0,0,-.012)),centre+Vector((0,-spread*.3,.008)),centre,k/32)for k in range(33)]
 curve('I83_OpticalNeck_'+str(i),pts,tine,.0033,'A_Nickel')
 sphere('I83_BallJoint_'+str(i),(.012,.012,.012),tine,centre,'A_ReadHead')
 head=P.empty('I83_ReadingHead_'+str(i),tine,centre);head.rotation_mode='QUATERNION'
 target=(M@tine.matrix_world).inverted()@score_focus
 head.rotation_quaternion=(target-centre).to_track_quat('-Z','Y')
 P.sleeve('I83_HeadBarrel_'+str(i),.020,.014,.018,head,(0,0,-.012),'A_ReadHead')
 P.sleeve('I83_LensRolledRim_'+str(i),.019,.0144,.004,head,(0,0,-.023),'A_Nickel')
 P.sleeve('I83_LensSeal_'+str(i),.015,.0138,.002,head,(0,0,-.024),'A_Rubber')
 lens=sphere('I83_ReadingLens_'+str(i),(.014,.014,.003),head,(0,0,-.025),'A_ReadLens')
 for side in [-1,1]:
  P.cylinder('I83_GimbalPin_'+str(i)+'_'+str(side),.0045,.005,head,(side*.021,0,-.009),'A_Bronze',(1,0,0),bevel=.0004)
 bpy.context.view_layer.update()
 lens_point=Vector((0,0,-.003));rest=mouth.matrix_world.inverted()@lens.matrix_world@lens_point
 tips.append({'node':tine.name,'lens_node':lens.name,'head_node':head.name,'head_forward_local_blender':[0,0,-1],'lens_focus_local_blender':list(lens_point),'mouth_point':list(rest),'local_point':list(lens_point),'ray':'I_TipReadingRay_'+str(i)})
 physical_heads.append({'head':head.name,'lens':lens.name,'rest_focus_mouth':list(rest),'parent_tine':tine.name})
for o in templates:bpy.data.objects.remove(o,do_unlink=True)

# Bring in the proven slit-projector hardware; change only its optical carrier.
with bpy.data.libraries.load(str(R/old_layout['source']),link=False)as(src,dst):dst.objects=[n for n in src.objects if n.startswith('I_')]
for o in dst.objects:col.objects.link(o)
optics=next(o for o in dst.objects if o.name=='I_MusicOptics');optics.parent=mouth;optics.matrix_parent_inverse.identity()
def replace_mesh(o,vs,faces,uv):
 me=bpy.data.meshes.new(o.name+'_R83');me.from_pydata(vs,[],faces);me.update()
 for ma in o.data.materials:me.materials.append(ma)
 layer=me.uv_layers.new(name='OpticalUV')
 for p in me.polygons:
  p.use_smooth=True
  for li in p.loop_indices:layer.data[li].uv=uv[me.loops[li].vertex_index]
 o.data=me
W=.84;H=.504;vs=[];faces=[];uv=[];N=64
for j in [0,1]:
 for k in range(N+1):
  u=k/N;v=j;x=(u-.5)*W;y=(.5-v)*H
  wp=score_center+horizontal*x+vertical*y+reader_n*(.007*(1-(2*x/W)**2))
  vs.append(world_to_mouth@wp);uv.append((u,v))
for k in range(N):faces.append((k,k+1,N+k+2,N+k+1))
sheet=bpy.data.objects['I_MoonlightStaff'];replace_mesh(sheet,vs,faces,uv)
# Glass apertures stay inside their original physical slots, with readable width.
for suffix in ['L','R']:
 ob=bpy.data.objects['I_StaffProjectorGlass'+suffix]
 for v in ob.data.vertices:v.co.x*=2
 ob.data.update()
focus_local=world_to_mouth@score_focus
def ribbon(o,world_start,world_end,width):
 direction=(world_end-world_start).normalized();side=direction.cross(reader_n).normalized()
 if side.length<.1:side=horizontal
 pts=[world_start-side*width/2,world_start+side*width/2,world_end+side*width/2,world_end-side*width/2]
 replace_mesh(o,[world_to_mouth@p for p in pts],[(0,1,2,3)],[(0,0),(1,0),(1,1),(0,1)])
line=bpy.data.objects['I_CentralReadingLine']
ribbon(line,score_focus-vertical*H/2,score_focus+vertical*H/2,.003)
for tip in tips:
 start=mouth_to_world@Vector(tip['mouth_point'])
 ribbon(bpy.data.objects[tip['ray']],start,score_focus,.0022)
# Static source preview uses real engraving with truly transparent blank space.
preview=bpy.data.materials.new('I83_RealScorePreview');preview.use_nodes=True;nodes=preview.node_tree.nodes;nodes.clear();links=preview.node_tree.links
out=nodes.new('ShaderNodeOutputMaterial');mix=nodes.new('ShaderNodeMixShader');transparent=nodes.new('ShaderNodeBsdfTransparent');em=nodes.new('ShaderNodeEmission');em.inputs[0].default_value=(.95,.82,.54,1);em.inputs[1].default_value=1.6
tex=nodes.new('ShaderNodeTexImage');tex.image=bpy.data.images.load(str(R/'app/assets/collection/art/I/moonlight_candidate/score/m1.0/000.png'));tex.image.pack()
coord=nodes.new('ShaderNodeTexCoord');flip=nodes.new('ShaderNodeVectorMath');flip.operation='MULTIPLY_ADD';flip.inputs[1].default_value=(1,-1,1);flip.inputs[2].default_value=(0,1,0)
links.new(coord.outputs['UV'],flip.inputs[0]);links.new(flip.outputs['Vector'],tex.inputs['Vector'])
links.new(tex.outputs['Alpha'],mix.inputs[0]);links.new(transparent.outputs[0],mix.inputs[1]);links.new(em.outputs[0],mix.inputs[2]);links.new(mix.outputs[0],out.inputs[0])
sheet.data.materials.clear();sheet.data.materials.append(preview)
glow=material('A_ScanPreview',(1,.42,.04),0,.2)
p=glow.node_tree.nodes.get('Principled BSDF');p.inputs['Emission Color'].default_value=(1,.40,.04,1);p.inputs['Emission Strength'].default_value=2.
for ob in [line]+[bpy.data.objects[t['ray']]for t in tips]:ob.data.materials.clear();ob.data.materials.append(glow)
bpy.context.view_layer.update()
assert all(fingerprint(bpy.data.objects[n])==h for n,h in protected.items())
scene.frame_set(1);bpy.ops.wm.save_as_mainfile(filepath=str(SRC),compress=True)
# Export copies use field textures for the foil deformation, preserving diaphragm morphs.
for group in seed['tongues']:
 for n in group['mesh_names']:bpy.data.objects[n].shape_key_clear()
curves=[o for o in root.children_recursive if o.type=='CURVE']
if curves:
 bpy.ops.object.select_all(action='DESELECT')
 for o in curves:o.select_set(True)
 bpy.context.view_layer.objects.active=curves[0];bpy.ops.object.convert(target='MESH')
optical_set=set([optics,*optics.children_recursive])
bpy.ops.object.select_all(action='DESELECT')
for o in [root,*root.children_recursive]:
 if o not in optical_set:o.select_set(True)
bpy.context.view_layer.objects.active=root
bpy.ops.export_scene.gltf(filepath=str(COMP),export_format='GLB',use_selection=True,export_animations=False,export_morph=True,export_morph_normal=True,export_apply=False,export_extras=True,export_tangents=CENTERED)
optics.parent=None;optics.matrix_world=Matrix.Identity(4)
OPT=ART/'optics.glb';bpy.ops.object.select_all(action='DESELECT')
for o in [optics,*optics.children_recursive]:o.select_set(True)
bpy.context.view_layer.objects.active=optics
bpy.ops.export_scene.gltf(filepath=str(OPT),export_format='GLB',use_selection=True,export_animations=False,export_morph=False,export_apply=False,export_extras=True,export_tangents=CENTERED)
sha=lambda path:hashlib.sha256(path.read_bytes()).hexdigest()
core={**seed,'source':SRC.relative_to(R).as_posix(),'source_sha256':sha(SRC),'component':COMP.relative_to(R).as_posix(),'component_sha256':sha(COMP),'parent_core_sha256':seed['component_sha256'],'physical_heads':physical_heads,'retained_functional_geometry_count':len(protected),'scope':'373 functional meshes including their UVs/morphs/transforms preserved; added three socket-fitted directional reading heads. Separate optics component. Full fit/clearance/runtime checks pending.'}
profile=json.loads((R/'app/assets/collection/art/I/collar_clamps/aperture_profile.json').read_text());profile.update({'source_sha256':core['source_sha256'],'component_sha256':core['component_sha256'],'measurement_parent_component_sha256':seed['parent_component_sha256'],'reuse_basis':'All six foil meshes, UV row encoding, shape keys and transforms preserved. Same foil-only projected-path metric; this is not total conductance including new lenses or grille.'})
aperture=ART/'aperture_profile.json';aperture.write_text(json.dumps(profile,indent=2)+'\n')
core['aperture_profile']='res://'+aperture.relative_to(R/'app').as_posix()
normal_local=(world_to_mouth.to_3x3()@reader_n).normalized();reveal_axis=(world_to_mouth.to_3x3()@vertical).normalized()
layout={**old_layout,'source':SRC.relative_to(R).as_posix(),'source_sha256':sha(SRC),'component':OPT.relative_to(R).as_posix(),'component_sha256':sha(OPT),'mouth_source_sha256':core['source_sha256'],'mouth_component_sha256':core['component_sha256'],'width':W/SCALE,'height':H/SCALE,'center_y':0.,'world_width':W,'world_height':H,'optical_backing':0.,'oriented_reveal':True,'reveal_center_blender':list(focus_local),'reveal_axis_blender':list(reveal_axis),'reading_normal_blender':list(normal_local),'scanner':{k:v for k,v in old_layout['scanner'].items()if k!='cap_manifest'},'scope':'Upright authored optical carrier centered on mouth, original world-readable area, real score alpha only. New glass heads are in the physical core component; emitter fixtures retained. Not runtime acceptance.'}
layout['scanner'].update({'tips':tips,'focus':list(focus_local),'line_end':list(world_to_mouth@(score_focus-vertical*H/2))})
(ART/'layout.json').write_text(json.dumps(layout,indent=2)+'\n');core['music_optics_layout']='res://'+(ART/'layout.json').relative_to(R/'app').as_posix();core['music_manifest']='res://assets/collection/art/I/chamber_response_r35/music_manifest.json'
report_suffix='_r2' if CENTERED else ''
(OUT/('optical_core_build'+report_suffix+'.json')).write_text(json.dumps(core,indent=2)+'\n')
(OUT/('optical_layout'+report_suffix+'.json')).write_text(json.dumps(layout,indent=2)+'\n')
(OUT/('optical_placement'+report_suffix+'.json')).write_text(json.dumps({'matrix_blender':[list(v)for v in M],'scale':SCALE,'score_center_world':list(score_center),'score_focus_world':list(score_focus),'world_width':W,'world_height':H,'reader_normal_world':list(reader_n),'reason':'Separate physical core diameter from original score legibility. Uniform cartridge scale includes installation wall allowance; projection keeps .84 x .504 world area. The centered variant offsets toward the actual hero camera to avoid perspective drift.'},indent=2)+'\n')
print('R83_OPTICS_BUILT',core['source_sha256'],flush=True)
