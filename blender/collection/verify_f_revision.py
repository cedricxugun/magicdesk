"""Check the isolated saved F source against independent recorded runtime data."""
import bpy,json,hashlib,math
from pathlib import Path
from mathutils import Matrix,Vector,Quaternion
ROOT=Path(__file__).resolve().parents[2];OUT=ROOT/'review/F_complete/revision_20260911/full_take'
source=ROOT/'blender/collection/F_refinement_candidate.blend'
take=json.loads((OUT/'physical_take.json').read_text());bake=json.loads((OUT/'candidate_bake.json').read_text())
assert hashlib.sha256(source.read_bytes()).hexdigest()==bake['source_sha256']
for path,key in [('models/F_complete.glb','model_sha256'),('models/F_complete.json','metadata_sha256'),('f_refined_controls.glb','controls_sha256')]:
    assert hashlib.sha256((ROOT/'app/assets/collection'/path).read_bytes()).hexdigest()==take[key]==bake[key]
bpy.ops.wm.open_mainfile(filepath=str(source));scene=bpy.context.scene
C=Matrix(((1,0,0,0),(0,0,1,0),(0,-1,0,0),(0,0,0,1)));CI=C.inverted()
def pose(p):return CI@Matrix.LocRotScale(Vector(p['p']),Quaternion((p['q'][3],*p['q'][:3])),Vector(p['s']))@C
def error(a,b):return max(abs(a[i][j]-b[i][j]) for i in range(4) for j in range(4))
errors={'local':0.,'world':0.,'widgets':0.,'field':0.,'gain':0.,'engraving':0.};worst={};counts={'transforms':0,'field':0,'glyph_vertices':0};visibility=[]
def measure(kind,value,label):
    if value>errors[kind]:errors[kind]=value;worst[kind]=label
frames=set(range(0,len(take['samples']),29));frames.update([0,len(take['samples'])-1])
for i in range(1,len(take['samples'])):
    if take['samples'][i]['state']['stage']!=take['samples'][i-1]['state']['stage']:frames.update([i-1,i])
for index in sorted(frames):
    sample=take['samples'][index];scene.frame_set(sample['frame']);bpy.context.view_layer.update()
    for name,p in sample['poses'].items():
        obj=bpy.data.objects[name];measure('local',error(obj.matrix_basis,pose(p)),[sample['frame'],name]);counts['transforms']+=1
        if name in sample['world_poses']:measure('world',error(obj.matrix_world,pose(sample['world_poses'][name])),[sample['frame'],name])
    for widget in sample['widgets']:
        node=bpy.data.objects['FCTRL_'+widget['gesture']];measure('widgets',error(node.matrix_world,pose(widget['pose'])),[sample['frame'],node.name])
        moving={o.name.replace('.','_'):o for o in node.children}
        for name,p in zip(widget['moving_names'],widget['moving']):measure('widgets',error(moving[name].matrix_basis,pose(p)),[sample['frame'],name])
    fx=sample.get('fx')
    if not fx:continue
    entries=[]
    for i,item in enumerate(fx['shards']):entries.append(('FRevision_Solid_%03d'%i,item,item['glow'],fx['visible']))
    for i,item in enumerate(fx['glints']):entries.append(('FRevision_Glint_%03d'%i,item['pose'],item['gain'],item['visible']))
    for j,items in enumerate(fx['ribbons']):
        for i,item in enumerate(items):entries.append(('FRevision_Ribbon_%d_%02d'%(j,i),item['pose'],item['gain'],item['visible']))
    for name,item in [('FRevision_PlumbFilament',fx['filament']),('FRevision_Writeback',fx['seed'])]+[('FRevision_ReceiverWave_'+str(i),x) for i,x in enumerate(fx['waves'])]:entries.append((name,item['pose'],item['gain'],item['visible']))
    for name,p,gain,shown in entries:
        obj=bpy.data.objects[name];assert obj.parent is None
        # Blender defers matrix_world for viewport-disabled objects; their
        # unparented basis is the actual authored world transform.
        measure('field',error(obj.matrix_basis,pose(p)),[sample['frame'],name])
        if not obj.hide_viewport:measure('field',error(obj.matrix_world,pose(p)),[sample['frame'],name])
        measure('gain',abs(obj.color[0]*8-gain),[sample['frame'],name]);counts['field']+=1
        if obj.hide_render==shown:visibility.append([sample['frame'],name])
scene.frame_set(take['samples'][-1]['frame'])
for name,surfaces in take['console_projection']['meshes'].items():
    expected=[CI.to_3x3()@Vector(p) for surface in surfaces for p in surface['vertices']];obj=bpy.data.objects[name]
    assert len(obj.data.vertices)==len(expected)
    for vertex,p in zip(obj.data.vertices,expected):measure('engraving',(vertex.co-p).length,name);counts['glyph_vertices']+=1
missing_textures=[img.filepath for img in bpy.data.images if img.source=='FILE' and not img.packed_file and img.filepath and not Path(bpy.path.abspath(img.filepath)).exists()]
original_hash=hashlib.sha256((ROOT/'blender/collection/F_complete.blend').read_bytes()).hexdigest()
report={'passed':max(errors.values())<1e-5 and not visibility and not missing_textures and original_hash==bake['original_source_sha256'],'sampled_frames':len(frames),'errors':errors,'worst':worst,'counts':counts,'hidden_field_evaluation':'Unparented basis checked for all fields; evaluated world also checked when visible. Blender skips matrix_world refresh for viewport-disabled objects.','visibility_mismatches':visibility,'missing_textures':missing_textures,'source_sha256':bake['source_sha256'],'original_preserved':original_hash==bake['original_source_sha256'],'scope':'Saved local AND world mechanical poses, physical widgets, captured optical planes/solid field transforms and gains at recorded samples, plus all fitted glyph vertices. Does not certify between-sample optics, all geometry clearance, pixel-equivalent shaders/lighting or native input.'}
(OUT/'source_verification.json').write_text(json.dumps(report,indent=2)+'\n');print('F_REVISION_VERIFIED',json.dumps(report),flush=True)
if not report['passed']:raise SystemExit(1)
