"""Convert unlit Mantaflow scalar grids, x-fastest Blender XYZ, to Godot R16F layers.
The density is preserved. Only axes change: Godot (x,y,z) = Blender (x,z,-y).
"""
from pathlib import Path
import argparse,json,numpy as np
p=argparse.ArgumentParser()
p.add_argument('--input',required=True);p.add_argument('--pattern',default='*.raw')
p.add_argument('--resolution',nargs=3,type=int,required=True)
p.add_argument('--bounds-min',nargs=3,type=float,required=True);p.add_argument('--bounds-max',nargs=3,type=float,required=True)
p.add_argument('--fps',type=float,default=12);p.add_argument('--stride',type=int,default=1)
p.add_argument('--out',required=True);args=p.parse_args()
source=Path(args.input);out=Path(args.out);out.mkdir(parents=True,exist_ok=True)
nx,ny,nz=args.resolution;files=sorted(source.glob(args.pattern))[::args.stride]
if not files:raise RuntimeError('No scalar density grids matched')
bmin=np.array(args.bounds_min);bmax=np.array(args.bounds_max)
gmin=np.array([bmin[0],bmin[2],-bmax[1]]);gmax=np.array([bmax[0],bmax[2],-bmin[1]])
resolution=np.array([nx,nz,ny]);cell=(gmax-gmin)/resolution
frames=[];frame_bounds=[];statistics=[]
occupancy_union=np.zeros((ny,nz,nx),dtype=np.bool_)
frame_times=[];source_times={};raw_manifest={}
if (source/'manifest.json').exists():
    raw_manifest=json.loads((source/'manifest.json').read_text(encoding='utf-8'))
    source_times={f.get('file_float32',f.get('file','')):float(f['time']) for f in raw_manifest.get('frames',[]) if isinstance(f,dict) and 'time' in f}
for i,file in enumerate(files):
    values=np.load(file) if file.suffix=='.npy' else np.fromfile(file,dtype='<f4')
    if values.size!=nx*ny*nz:raise RuntimeError(f'{file}: grid size {values.size} != {nx*ny*nz}')
    if not np.isfinite(values).all():raise RuntimeError(f'{file}: non-finite density')
    blender=values.reshape(nz,ny,nx)
    godot=np.ascontiguousarray(blender.transpose(1,0,2)[::-1,:,:])
    occupancy_union|=godot>1e-5
    target=out/f'frame_{i:03d}.r16';target.write_bytes(godot.astype('<f2').tobytes())
    frames.append(str(target).replace('\\','/'))
    frame_times.append(source_times.get(file.name,i*args.stride/args.fps))
    nonzero=np.argwhere(godot>1e-4)
    if nonzero.size:
        # NumPy Z/Y/X -> world X/Y/Z, with two extra voxels for soft interpolation.
        low=np.maximum(nonzero.min(axis=0)[::-1]-2,0);high=np.minimum(nonzero.max(axis=0)[::-1]+3,resolution)
        frame_bounds.append([(gmin+low*cell).tolist(),(gmin+high*cell).tolist()])
    else:frame_bounds.append([((gmin+gmax)/2).tolist(),((gmin+gmax)/2).tolist()])
    statistics.append({'source':file.name,'minimum':float(godot.min()),'maximum':float(godot.max()),'nonzero_voxels':int(nonzero.shape[0])})
coarse_shape=np.ceil(np.array(occupancy_union.shape)/4).astype(int)
edges=[np.linspace(0,n,c+1).astype(int) for n,c in zip(occupancy_union.shape,coarse_shape)]
coarse=np.zeros(tuple(coarse_shape),dtype=np.uint8)
for zz in range(coarse_shape[0]):
    for yy in range(coarse_shape[1]):
        for xx in range(coarse_shape[2]):
            coarse[zz,yy,xx]=255 if occupancy_union[edges[0][zz]:edges[0][zz+1],edges[1][yy]:edges[1][yy+1],edges[2][xx]:edges[2][xx+1]].any() else 0
pad=np.pad(coarse,1)
conservative=np.zeros_like(coarse)
for dz in range(3):
    for dy in range(3):
        for dx in range(3):conservative=np.maximum(conservative,pad[dz:dz+coarse_shape[0],dy:dy+coarse_shape[1],dx:dx+coarse_shape[2]])
occupancy_path=out/'occupancy.r8';occupancy_path.write_bytes(conservative.tobytes())
manifest={'format':'R16F','axis_mapping':'Godot (x,y,z) = Blender (x,z,-y); texture layers Z, rows Y, columns X','resolution':resolution.tolist(),'bounds_min':gmin.tolist(),'bounds_max':gmax.tolist(),'fps':args.fps/args.stride,'time_offset':0.0,'density_scale':1.0,'frames_raw':frames,'frame_times':frame_times,'frame_bounds':frame_bounds,'statistics':statistics,'occupancy_raw':str(occupancy_path).replace('\\','/'),'occupancy_resolution':coarse_shape[::-1].tolist(),'occupied_macro_fraction':float(np.mean(conservative>0))}
for key in ['method','loop_duration','loop_duration_seconds','loop_start','loop_end','loop_start_time','loop_end_time','loop_crossfade_seconds','crossfade_already_baked','warmup_handoff_source_time','looping']:
    if key in raw_manifest:manifest[key]=raw_manifest[key]
(out/'prepared.json').write_text(json.dumps(manifest,indent=2),encoding='utf-8')
print('PRESSURE_SCALAR_CACHE_PREPARED',len(frames),manifest['resolution'],manifest['fps'],out/'prepared.json')
