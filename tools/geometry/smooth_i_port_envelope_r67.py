"""Raise a candidate flange return above exact projected source triangles.

Only a geometric candidate. The resulting source still needs topology, assembled
clearance, withdrawal and visual review; an envelope solve is not acceptance.
"""
import json
from pathlib import Path
import numpy as np
from shapely.geometry import Polygon
from shapely.strtree import STRtree

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'review/I_refinement/nautilus_r1/port_envelope_r67/smooth_r2'
OUT.mkdir(parents=True,exist_ok=True)
data = json.loads((OUT.parent / 'height_source.json').read_text())
points = np.array(data['vertices'], dtype=np.float64)
original = points.copy()
triangles = data['triangles']
skin_points, skin_polys = [], []
for skin in data['skins']:
    for tri in skin['triangles']:
        p = np.array(tri, dtype=np.float64)
        poly = Polygon(p[:, :2])
        if poly.area > 1e-15:
            skin_points.append(p)
            skin_polys.append(poly)
tree = STRtree(skin_polys)
constraints = []
clearance = .0004
for tri in triangles:
    # Return annulus only: outer ring 12 through inner ring 19.
    if min(tri) < 12 * 192 or max(tri) >= 20 * 192:
        continue
    p = points[tri]
    poly = Polygon(p[:, :2])
    if poly.area < 1e-15:
        continue
    matrix = np.vstack([p[:, 0], p[:, 1], np.ones(3)])
    for index in tree.query(poly, predicate='intersects'):
        overlap = poly.intersection(skin_polys[index])
        if overlap.is_empty or overlap.area < 1e-16:
            continue
        source = skin_points[index]
        plane = np.linalg.solve(np.column_stack([source[:, :2], np.ones(3)]), source[:, 2])
        for xy in list(overlap.exterior.coords)[:-1]:
            q = np.array([*xy, 1.])
            weights = np.linalg.solve(matrix, q)
            assert min(weights) > -1e-7
            weights = np.maximum(weights, 0.)
            weights /= weights.sum()
            constraints.append((tri, weights, float(q @ plane + clearance)))

# Each correction is nonnegative, so satisfying later constraints cannot break
# earlier ones. Use the largest weight to avoid inflating almost unrelated nodes.
for tri, weights, required in constraints:
    gap = required - float(weights @ points[tri, 2])
    if gap > 0.:
        selected = int(np.argmax(weights))
        points[tri[selected], 2] += (gap + 2e-7) / weights[selected]

assert constraints
residual = min(float(weights @ points[tri, 2]) - required for tri, weights, required in constraints)
assert residual >= -1e-10
for front_ring in range(4, 12):
    back_ring = 23 - front_ring
    for angle in range(192):
        top, bottom = front_ring * 192 + angle, back_ring * 192 + angle
        points[top, 2] = max(points[top, 2], points[bottom, 2] + .0038)

# Form the visible flange as a smooth majorant of the required envelope.
# Dilation followed by a periodic Gaussian rounds local peaks; a final measured
# offset guarantees that smoothing never cuts back through the required wall.
heights = points[4*192:12*192,2].reshape((8,192)).copy()
expanded = heights.copy()
for radial in range(-2,3):
    rows = np.clip(np.arange(8)+radial,0,7)
    for angular in range(-6,7):
        expanded = np.maximum(expanded, np.roll(heights[rows],angular,axis=1))
smoothed = np.zeros_like(expanded)
weight_sum = 0.
for radial in range(-2,3):
    rows = np.clip(np.arange(8)+radial,0,7)
    for angular in range(-8,9):
        weight=np.exp(-.5*(radial/1.2)**2-.5*(angular/3.)**2)
        smoothed += np.roll(expanded[rows],angular,axis=1)*weight
        weight_sum += weight
smoothed /= weight_sum
smoothed += max(0.,float(np.max(heights-smoothed)))+.0003
points[4*192:12*192,2]=smoothed.reshape(-1)
assert np.min(smoothed-heights)>=.0003-1e-12

report = {
    'constraint_points': len(constraints), 'axial_clearance': clearance,
    'minimum_constraint_residual': residual,
    'maximum_axial_change': float(np.max(points[:, 2] - original[:, 2])),
    'changed_vertices': int(np.sum(points[:, 2] != original[:, 2])),
    'vertices': points.tolist(),
    'scope': 'Exact planar overlap vertices bound the planar return triangles against supplied skin triangles. Not a mesh, withdrawal, minimum wall or visual acceptance.'
}
(OUT / 'height_solution.json').write_text(json.dumps(report, indent=2) + '\n')
print({k: v for k, v in report.items() if k != 'vertices'})
