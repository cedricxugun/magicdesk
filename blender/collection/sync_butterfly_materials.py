"""Synchronize G1's finish profile without rebuilding geometry or animation."""
import bpy,json,hashlib,shutil,array
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
PROFILE=ROOT/'app/assets/collection/butterfly_materials.json'
specs=json.loads(PROFILE.read_text())['materials']
OUT=ROOT/'review/G_optical_curator/butterfly_r2/materials'

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

def apply(mat,key):
    spec=specs[key];nt=mat.node_tree;bsdf=next(n for n in nt.nodes if n.type=='BSDF_PRINCIPLED')
    # Keep recorded formation/mix nodes and their keyed values untouched.
    for socket in ['Base Color','Roughness','Normal']:
        for link in list(bsdf.inputs[socket].links):nt.links.remove(link)
    for node in list(nt.nodes):
        if node.name.startswith('ButterflyFinish_'):nt.nodes.remove(node)
    for socket,value in [('Base Color',(*spec['color'],1)),('Metallic',spec['metallic']),('Roughness',spec['roughness']),('Coat Weight',spec['coat']),('Coat Roughness',spec['coat_roughness']),('Specular IOR Level',spec['specular_strength']),('Anisotropic',spec['anisotropy_strength'])]:bsdf.inputs[socket].default_value=value
    def node(kind,name):
        n=nt.nodes.new(kind);n.name='ButterflyFinish_'+name;return n
    def texture(path,name):
        n=node('ShaderNodeTexImage',name);n.image=bpy.data.images.load(str(ROOT/'app'/path.removeprefix('res://')),check_existing=True);n.image.colorspace_settings.name='Non-Color';return n
    if 'roughness_map' in spec:
        tex=texture(spec['roughness_map'],'Roughness');channels=node('ShaderNodeSeparateColor','LinearChannels');nt.links.new(tex.outputs['Color'],channels.inputs['Color'])
        math=node('ShaderNodeMath','RoughnessRange');math.operation='MULTIPLY_ADD';math.inputs[1].default_value=spec['roughness_scale'];math.inputs[2].default_value=spec['roughness_offset'];nt.links.new(channels.outputs['Green'],math.inputs[0]);nt.links.new(math.outputs[0],bsdf.inputs['Roughness'])
    if 'normal_map' in spec:
        tex=texture(spec['normal_map'],'NormalTexture');normal=node('ShaderNodeNormalMap','Normal');normal.inputs['Strength'].default_value=spec['normal_depth'];nt.links.new(tex.outputs['Color'],normal.inputs['Color']);nt.links.new(normal.outputs['Normal'],bsdf.inputs['Normal'])
    mat['butterfly_material_key']=key

reports=[]
for stem in ['G_butterfly_r2','G_butterfly_runtime_candidate']:
    path=ROOT/f'blender/collection/{stem}.blend';backup=ROOT/'blender/collection/checkpoints'/f'{stem}-before-finish-{hashlib.sha256(path.read_bytes()).hexdigest()[:12]}.blend'
    if not backup.exists():shutil.copy2(path,backup)
    bpy.ops.wm.open_mainfile(filepath=str(path));before=fingerprint()
    root=bpy.data.objects['GB2_Butterfly'];materials={};count=0
    for obj in root.children_recursive:
        if obj.type not in ['MESH','CURVE','FONT']:continue
        for slot in obj.material_slots:
            source=slot.material
            if not source:continue
            key=source.get('butterfly_material_key') or next((k for k in specs if ('Collection_'+k) in source.name),None)
            if not key:continue
            # Object-linked copies cannot recolor external users of mesh data.
            if source.name not in materials:
                mat=source.copy();mat.name='Collection_'+key;apply(mat,key);materials[source.name]=mat
            slot.link='OBJECT';slot.material=materials[source.name];count+=1
    after=fingerprint();assert before==after,(stem,'Unexpected geometry/animation change')
    assert {m['butterfly_material_key'] for m in materials.values()}==set(specs),'Incomplete finish coverage'
    bpy.ops.file.make_paths_relative();bpy.ops.wm.save_as_mainfile(filepath=str(path))
    reports.append({'source':str(path.relative_to(ROOT)),'backup':str(backup.relative_to(ROOT)),'material_families':len(set(m['butterfly_material_key'] for m in materials.values())),'slots_updated':count,'unchanged':after})
report={'profile_sha256':hashlib.sha256(PROFILE.read_bytes()).hexdigest(),'sources':reports,'scope':'Only G1 material slots; geometry, pose and animation hashes unchanged. Runtime still consumes the separate finish profile; GLB unchanged.'}
(OUT/'source_finish_sync.json').write_text(json.dumps(report,indent=2)+'\n');print('BUTTERFLY_FINISH_SYNC',json.dumps(report),flush=True)

# Atlas and candidate bind to the same editable source revision. Geometry and
# animation fingerprints above must match before changing this provenance.
candidate=ROOT/'app/assets/collection/models/G_optical_curator_butterfly_candidate.json'
data=json.loads(candidate.read_text());data['g_archive']['contents'][1]['butterfly']['source_sha256']=hashlib.sha256((ROOT/'blender/collection/G_butterfly_r2.blend').read_bytes()).hexdigest();data['g_archive']['contents'][1]['butterfly']['finish_profile']='res://assets/collection/butterfly_materials.json';candidate.write_text(json.dumps(data,separators=(',',':'))+'\n')
