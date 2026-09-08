"""Quiet, isotropic ivory glazed ceramic. Creates NEW ceramic_* files only."""
from pathlib import Path
from PIL import Image
import numpy as np, json

ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'app'/'assets';REV=ROOT/'review';N=4096
rng=np.random.default_rng(840217)

def field(size,blur=0):
    from PIL import ImageFilter
    a=rng.random((size,size),dtype=np.float32)
    im=Image.fromarray(a,mode='F').resize((N,N),Image.Resampling.BICUBIC)
    # Square source and equal scaling: no fiber/grain direction.
    x=np.array(im,dtype=np.float32);x-=x.mean();x/=max(float(x.std()),1.e-8)
    return x

slow=field(9);middle=field(61);fine=field(712)
coords=(np.arange(N,dtype=np.float32)+.5)/N
border=np.minimum.reduce([np.broadcast_to(coords[None,:],(N,N)),np.broadcast_to((1-coords)[None,:],(N,N)),np.broadcast_to(coords[:,None],(N,N)),np.broadcast_to((1-coords)[:,None],(N,N))])
# A 0.28%-UV seam band; no dirt on broad faces. Lateral seams are mostly hidden by ribs.
edge=np.exp(-np.square(border/.0028)).astype(np.float32)
wear=edge*np.clip(.48+middle*.17,0,.90)
base=np.array([226.,220.,208.],dtype=np.float32)
color=base[None,None,:]+(slow*.32+middle*.075)[:,:,None]
color-=wear[:,:,None]*np.array([7.5,8.0,8.5],dtype=np.float32)
Image.fromarray(np.clip(np.rint(color),0,255).astype(np.uint8),'RGB').save(OUT/'ceramic_ivory_albedo.png')
# Principled perceptual roughness. Most of the shell is 0.207-0.223.
rough=np.clip(.215+slow*.0018+middle*.0010+fine*.0004+wear*.050,.205,.266)
Image.fromarray(np.rint(rough*255).astype(np.uint8),'L').save(OUT/'ceramic_glaze_roughness.png')
# Tiny isotropic subvisible glaze ripples; no woven fibers, pitting, scratches or macro pores.
height=fine*.004+middle*.012+slow*.018
dy,dx=np.gradient(height)
norm=np.stack([-dx,-dy,np.ones_like(dx)],axis=-1)
norm/=np.linalg.norm(norm,axis=-1)[:,:,None]
Image.fromarray(np.clip(np.rint((norm*.5+.5)*255),0,255).astype(np.uint8),'RGB').save(OUT/'ceramic_glaze_normal.png')
Image.fromarray(np.rint(wear*255).astype(np.uint8),'L').save(OUT/'ceramic_edge_wear_mask.png')
inside=border>.012
info={'resolution':[N,N],'seed':840217,'color_space':{'ceramic_ivory_albedo.png':'sRGB','ceramic_glaze_roughness.png':'linear/non-color; perceptual roughness in R','ceramic_glaze_normal.png':'linear/non-color; tangent-space OpenGL +Y','ceramic_edge_wear_mask.png':'linear/non-color; optional R mask'},'parameters':{'metallic':0.0,'roughness_multiplier':1.0,'roughness_fallback':.215,'normal_strength':.20,'coat_weight_blender':.42,'coat_roughness_blender':.105,'coat_ior':1.46,'ior':1.46,'specular_ior_level':.5,'anisotropy':0.0,'subsurface_weight':0.0},'godot_suggestion':{'metallic':0.,'roughness':1.,'roughness_texture_channel':'R','normal_scale':.20,'clearcoat':.42,'clearcoat_roughness':.105,'specular':.5,'base_color_tint':'white (texture already contains ivory)','normal_y_convention':'OpenGL +Y'},'measured':{'broad_surface_roughness_min':float(rough[inside].min()),'broad_surface_roughness_max':float(rough[inside].max()),'broad_surface_roughness_mean':float(rough[inside].mean()),'broad_surface_albedo_std_rgb':color[inside].std(axis=0,dtype=np.float64).tolist(),'normal_x_std':float(norm[:,:,0].std()),'normal_y_std':float(norm[:,:,1].std()),'normal_direction_ratio':float(norm[:,:,0].std()/norm[:,:,1].std()),'edge_wear_coverage_over_10pct':float(np.mean(wear>.1))},'notes':['NEW maps, old enamel maps unchanged.','No macro grain, no directional scratches, no ambient occlusion or highlights baked into base color.','Wear exists only within a narrow UV perimeter band.','Do not multiply old enamel noise/roughness/normal on top of these maps.','Normal amplitude is intentionally almost flat: material reads from dielectric Fresnel, smooth curvature and rectangular light reflection.']}
(REV/'ceramic_refine_material_spec.json').write_text(json.dumps(info,indent=2),encoding='utf-8')
print(json.dumps(info['measured'],indent=2));print('CERAMIC_PBR_READY',flush=True)
