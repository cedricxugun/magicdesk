"""Quantify revision movement only for matching orthographic captures, never art fidelity."""
from pathlib import Path
import argparse,json
import numpy as np
from scipy import ndimage
from PIL import Image,ImageDraw
ROOT=Path(__file__).resolve().parents[2]
p=argparse.ArgumentParser();p.add_argument('--before',required=True);p.add_argument('--after',required=True);p.add_argument('--out',required=True);a=p.parse_args()
before=ROOT/a.before;after=ROOT/a.after;out=ROOT/a.out;out.mkdir(parents=True,exist_ok=True)
old=json.loads((before/'views.json').read_text());new=json.loads((after/'views.json').read_text())
measure=json.loads((after.parent/'measured_shape.json').read_text());D=measure['D'];rows=[]
def mask(path):
 im=np.array(Image.open(path).convert('RGBA'));return (im[:,:,:3].min(axis=2)>127)&(im[:,:,3]>127)
def edge(m):return m & ~ndimage.binary_erosion(m)
for left,right in zip(old['views'],new['views']):
 for k in ['view','camera_position','target','ortho_span','resolution']:assert left[k]==right[k],f'Camera mismatch: {k}'
 name=left['view'];x=mask(before/f'{name}_silhouette.png');y=mask(after/f'{name}_silhouette.png');assert x.shape==y.shape
 units_per_pixel=left['ortho_span']/x.shape[0]/D
 dx=ndimage.distance_transform_edt(~edge(x));dy=ndimage.distance_transform_edt(~edge(y));dist=np.r_[dx[edge(y)],dy[edge(x)]]
 union=(x|y).sum();iou=float((x&y).sum()/union) if union else 1.
 shifts={}
 for anchor,point in left['landmarks_pixels'].items():
  other=right['landmarks_pixels'][anchor];shifts[anchor]=float(np.linalg.norm(np.array(point)-np.array(other))*units_per_pixel)
 rows.append({'view':name,'silhouette_overlap_between_revisions':iou,'boundary_p95_D':float(np.percentile(dist,95)*units_per_pixel),'boundary_max_D':float(dist.max()*units_per_pixel),'landmark_shifts_D':shifts})
 pixels=np.zeros((*x.shape,3),dtype=np.uint8);pixels[x&y]=[210,213,214];pixels[x&~y]=[60,145,245];pixels[y&~x]=[245,133,59]
 image=Image.fromarray(pixels);draw=ImageDraw.Draw(image);draw.text((16,16),name+' | BLUE: previous only | ORANGE: current only | GRAY: overlap',fill='white');draw.text((16,36),'Revision change diagnostic - NOT a reference fidelity score',fill='white');image.save(out/f'{name}_delta.png')
report={'before_source_sha256':old['source_sha256'],'after_source_sha256':new['source_sha256'],'camera_match':True,'views':rows,'status':'diagnostic_only_unlocked_forms','scope':'Pixel masks under identical fixed cameras. IoU describes revision overlap, NOT accuracy against the original concept. No art acceptance or continuous geometry/animation claim.'}
(out/'comparison.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(rows,indent=2))
