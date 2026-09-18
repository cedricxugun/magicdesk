"""Apply reviewed F finishes to isolated source, preserving geometry and animation."""
import bpy,json,hashlib,shutil,array
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
PROFILE=ROOT/'app/assets/collection/f_finish.json'
profile=json.loads(PROFILE.read_text())
source=ROOT/'blender/collection/F_refinement_candidate.blend'
original=ROOT/'blender/collection/F_complete.blend'
OUT=ROOT/'review/F_complete/revision_20260911/finish';OUT.mkdir(exist_ok=True)
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def fingerprint():
    geometry=hashlib.sha256();animation=hashlib.sha256()
    for mesh in sorted(bpy.data.meshes,key=lambda m:m.name):
        values=array.array('f',[0.0])*(len(mesh.vertices)*3);mesh.vertices.foreach_get('co',values)
        geometry.update(mesh.name.encode());geometry.update(values.tobytes())
        indices=array.array('i',[0])*len(mesh.loops);mesh.loops.foreach_get('vertex_index',indices);geometry.update(indices.tobytes())
    for obj in sorted(bpy.data.objects,key=lambda o:o.name):
        geometry.update(str((obj.name,obj.parent.name if obj.parent else None,tuple(v for row in obj.matrix_basis for v in row))).encode())
    for action in sorted(bpy.data.actions,key=lambda a:a.name):
        animation.update(action.name.encode())
        for layer in action.layers:
            for strip in layer.strips:
                for bag in strip.channelbags:
                    for curve in bag.fcurves:
                        animation.update(str((curve.data_path,curve.array_index,[(tuple(k.co),k.interpolation) for k in curve.keyframe_points])).encode())
    return {'geometry_and_pose':geometry.hexdigest(),'animation':animation.hexdigest()}
def finish_key(obj,name):
    ancestry='';node=obj
    while node:
        ancestry+='/'+node.name;node=node.parent
    for rule in profile['rules']:
        if name==rule['source'] and any(t in ancestry for t in rule['ancestors']):return rule['finish']
    return profile['defaults'].get(name)
def apply(mat,key):
    spec=profile['finishes'][key];nt=mat.node_tree;bsdf=next(n for n in nt.nodes if n.type=='BSDF_PRINCIPLED')
    for field,socket in [('metallic','Metallic'),('coat','Coat Weight'),('coat_roughness','Coat Roughness'),('anisotropy_strength','Anisotropic')]:
        if field in spec:bsdf.inputs[socket].default_value=spec[field]
    if 'roughness' in spec:
        assert not bsdf.inputs['Roughness'].is_linked,'Do not erase an authored roughness texture'
        bsdf.inputs['Roughness'].default_value=spec['roughness']
    if bsdf.inputs['Roughness'].is_linked:
        incoming=bsdf.inputs['Roughness'].links[0].from_socket
        for link in list(bsdf.inputs['Roughness'].links):nt.links.remove(link)
        for operation,value in [('MULTIPLY',spec.get('roughness_scale',1.)),('MAXIMUM',spec.get('roughness_floor',.18)),('MINIMUM',.8)]:
            node=nt.nodes.new('ShaderNodeMath');node.name='FFinish_'+operation;node.operation=operation;node.inputs[1].default_value=value;nt.links.new(incoming,node.inputs[0]);incoming=node.outputs[0]
        nt.links.new(incoming,bsdf.inputs['Roughness'])
    for node in nt.nodes:
        if node.type=='NORMAL_MAP':node.inputs['Strength'].default_value=spec.get('normal_depth',.075)
    mat['f_finish_key']=key
before_hash=sha(source);original_hash=sha(original)
backup=ROOT/'blender/collection/checkpoints'/('F-before-finish-'+before_hash[:12]+'.blend')
if not backup.exists():shutil.copy2(source,backup)
bpy.ops.wm.open_mainfile(filepath=str(source));before=fingerprint()
root=bpy.data.objects['F_UPPER'];copies={};count=0;keys=set()
for obj in root.children_recursive:
    if obj.type not in ['MESH','CURVE','FONT']:continue
    for slot in obj.material_slots:
        original_mat=slot.material
        if not original_mat:continue
        source_name=original_mat.get('f_finish_source',original_mat.name)
        key=finish_key(obj,source_name)
        if not key:continue
        assert not original_mat.get('f_finish_key'),'Already synchronized; do not add another material-node chain'
        pair=(original_mat.name,key)
        if pair not in copies:
            mat=original_mat.copy();mat.name='FFinish_'+key;mat['f_finish_source']=source_name;apply(mat,key);copies[pair]=mat
        slot.link='OBJECT';slot.material=copies[pair];count+=1;keys.add(key)
assert keys==set(profile['finishes']),(keys,set(profile['finishes']))
after=fingerprint();assert before==after,'Unexpected geometry/pose/animation edit'
bpy.ops.wm.save_as_mainfile(filepath=str(source));assert sha(original)==original_hash
report={'source_sha256':sha(source),'before_sha256':before_hash,'backup':str(backup.relative_to(ROOT)),'slots_updated':count,'finishes':sorted(keys),'profile_sha256':sha(PROFILE),'preserved':after,'original_source_preserved':True,'scope':'Material slots and static BSDF inputs only; existing texture UVs, meshes, transforms and animation curves unchanged. Not pixel-identical to Godot.'}
(OUT/'source_sync.json').write_text(json.dumps(report,indent=2)+'\n')
bake_path=ROOT/'review/F_complete/revision_20260911/full_take/candidate_bake.json';bake=json.loads(bake_path.read_text());bake['source_sha256']=report['source_sha256'];bake['finish_patch']='review/F_complete/revision_20260911/finish/source_sync.json';bake_path.write_text(json.dumps(bake,indent=2)+'\n')
print('F_FINISH_SOURCE_SYNC',json.dumps(report),flush=True)
