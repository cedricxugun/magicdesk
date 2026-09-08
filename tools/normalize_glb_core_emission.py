"""Restore the static GLB's authored core intensity without touching mesh buffers.

Blender's frame-one material animation is intentionally darker than the runtime
reference. The interactive core overrides this material, but other GLB viewers
should receive the original .8 emissive reference instead of the .05 startup key.
"""
import json
import struct
from pathlib import Path

target = Path(__file__).resolve().parents[1] / 'app/assets/helios_model.glb'
blob = target.read_bytes()
json_size, chunk_type = struct.unpack_from('<II', blob, 12)
assert chunk_type == 0x4E4F534A
document = json.loads(blob[20:20 + json_size])
core = next(m for m in document['materials'] if m.get('name') == 'Solar_Core_Emission')
strength = core.get('extensions', {}).get('KHR_materials_emissive_strength', {}).get('emissiveStrength', 1.0)
factor = core.get('emissiveFactor', [0, 0, 0])
assert factor[0] > 0
gain = .8 / (factor[0] * strength)
core['emissiveFactor'] = [v * gain for v in factor]
encoded = json.dumps(document, separators=(',', ':'), ensure_ascii=False).encode('utf-8')
encoded += b' ' * (-len(encoded) % 4)
tail = blob[20 + json_size:]
result = struct.pack('<III', 0x46546C67, 2, 20 + len(encoded) + len(tail))
result += struct.pack('<II', len(encoded), 0x4E4F534A) + encoded + tail
assert result[20 + len(encoded):] == tail
target.write_bytes(result)
print(json.dumps({'static_core_emission': core['emissiveFactor'][0] * strength, 'mesh_and_image_buffers_unchanged': True}))
