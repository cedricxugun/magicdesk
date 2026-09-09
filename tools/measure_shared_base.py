#!/usr/bin/env python3
"""Read the authoritative GLB vertices; do not alter the model."""
import hashlib
import json
from pathlib import Path
import struct

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "app/assets/helios_model.glb"
data = SOURCE.read_bytes()
size, kind = struct.unpack_from("<II", data, 12)
gltf = json.loads(data[20:20 + size])
bin_start = 20 + size + 8
blob = memoryview(data)[bin_start:]
identity = [[int(i == j) for j in range(4)] for i in range(4)]

def multiply(a, b):
    return [[sum(a[i][k] * b[k][j] for k in range(4)) for j in range(4)] for i in range(4)]

def transform(node):
    if "matrix" in node:
        return [[node["matrix"][j * 4 + i] for j in range(4)] for i in range(4)]
    x, y, z, w = node.get("rotation", [0, 0, 0, 1])
    s = node.get("scale", [1, 1, 1])
    t = node.get("translation", [0, 0, 0])
    r = [[1-2*y*y-2*z*z, 2*x*y-2*z*w, 2*x*z+2*y*w],
         [2*x*y+2*z*w, 1-2*x*x-2*z*z, 2*y*z-2*x*w],
         [2*x*z-2*y*w, 2*y*z+2*x*w, 1-2*x*x-2*y*y]]
    return [[r[i][j] * s[j] for j in range(3)] + [t[i]] for i in range(3)] + [[0, 0, 0, 1]]

def measure(root_name, exclude_children=False):
    low, high, count = [float("inf")]*3, [-float("inf")]*3, 0
    nodes = gltf["nodes"]
    root_index = next(i for i, n in enumerate(nodes) if n.get("name") == root_name)
    def visit(index, parent):
        nonlocal count
        node = nodes[index]
        world = multiply(parent, transform(node))
        if "mesh" in node:
            for primitive in gltf["meshes"][node["mesh"]]["primitives"]:
                accessor = gltf["accessors"][primitive["attributes"]["POSITION"]]
                assert accessor["componentType"] == 5126 and accessor["type"] == "VEC3"
                view = gltf["bufferViews"][accessor["bufferView"]]
                offset = view.get("byteOffset", 0) + accessor.get("byteOffset", 0)
                stride = view.get("byteStride", 12)
                for i in range(accessor["count"]):
                    p = struct.unpack_from("<fff", blob, offset + i*stride)
                    for j in range(3):
                        value = sum(world[j][k]*p[k] for k in range(3)) + world[j][3]
                        low[j], high[j] = min(low[j], value), max(high[j], value)
                    count += 1
        if not exclude_children:
            for child in node.get("children", []):
                visit(child, world)
    visit(root_index, identity)
    return {"node": root_name, "min": low, "max": high, "size": [b-a for a,b in zip(low,high)], "vertices_measured": count}

base = measure("BASE_FIXED")
body = measure("BASE_FIXED_DisplayMesh")
whole = measure("HELIOS_ROOT")
report = {"source": str(SOURCE.relative_to(ROOT)), "source_sha256": hashlib.sha256(data).hexdigest(),
          "method": "Actual float32 POSITION vertices transformed through the GLB node hierarchy; static imported pose.",
          "axes": "x horizontal, y up, z depth; authored scene units, not a physical manufacturing specification",
          "fixed_base_including_controls": base, "base_body": body, "helios_closed_static": whole,
          "normalized_base_diameter_D": body["size"][0],
          "diameter_definition": "Lateral shell diameter; forward-facing fascia and controls project beyond the circular rim in z.",
          "internal_free_volume_verified": False}
target = ROOT / "concepts/shared_base/base_measurements.json"
target.write_text(json.dumps(report, ensure_ascii=False, indent=2)+"\n")
print(json.dumps(report, ensure_ascii=False, indent=2))
