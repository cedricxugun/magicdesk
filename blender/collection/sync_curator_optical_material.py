"""Update only the optical material in the existing animated source.

Do not rerun the geometry generator to apply a coating adjustment: that would
discard the saved mechanical animation and any manual work in the source.
"""
import bpy,json,hashlib
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
path=ROOT/'app/assets/collection/lighting_profiles.json'
profile=json.loads(path.read_text())['profiles']['G']['optical']
source=ROOT/'blender/collection/G_optical_curator.blend'
bpy.ops.wm.open_mainfile(filepath=str(source))
mat=bpy.data.materials['GA_RecordedExpressions']
node=next(n for n in mat.node_tree.nodes if n.type=='BSDF_PRINCIPLED')
for setting,socket in [('specular','Specular IOR Level'),('coat','Coat Weight'),('roughness','Roughness')]:node.inputs[socket].default_value=profile[setting]
bpy.ops.wm.save_as_mainfile(filepath=str(source))
report={'source':'app/assets/collection/lighting_profiles.json','optical':profile,'profile_sha256':hashlib.sha256(json.dumps(profile,sort_keys=True).encode()).hexdigest(),'animation_preserved':True}
(ROOT/'review/G_optical_curator/lighting/source_optical_profile.json').write_text(json.dumps(report,indent=2)+'\n');print('CURATOR_OPTICAL_MATERIAL_SYNCED',report,flush=True)
