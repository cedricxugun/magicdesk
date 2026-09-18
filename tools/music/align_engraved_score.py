"""Independent coarse score-time alignment, using engraved durations not MIDI ticks."""
from pathlib import Path
import argparse,json,hashlib
import numpy as np,librosa
ROOT=Path(__file__).resolve().parents[2];OUT=ROOT/'review/I_refinement/moonlight/onset_refinement';p=argparse.ArgumentParser();p.add_argument('--movement',required=True,type=int,choices=[1,2,3]);args=p.parse_args();i=args.movement
score=json.loads((OUT/f'score_reference_{i}.json').read_text());old=json.loads((ROOT/'review/I_refinement/moonlight'/f'alignment{i}_candidate.json').read_text());data=np.load(next(OUT.glob(f'm{i}_*_features.npz')));cqt=data['cqt'];sr=22050;hop=1024
start,end=old['active_audio_bounds'];begin=int(start*sr/256);finish=int(end*sr/256);cqt=cqt[:,begin:finish:4]
features=np.zeros((12,cqt.shape[1]),dtype=np.float32)
for bin in range(88):features[(bin+21)%12]+=cqt[bin]**.7
features=librosa.util.normalize(features+1e-6,axis=0)
last=max(e['quarter']+n['duration_quarters'] for e in score['events'] for n in e['heads']);quarters=np.arange(0,last+.125,.125);reference=np.zeros((12,len(quarters)),dtype=np.float32)
for event in score['events']:
 for note in event['heads']:
  a=int(np.searchsorted(quarters,event['quarter']));b=min(len(quarters),max(a+1,int(np.searchsorted(quarters,event['quarter']+note['duration_quarters']))))
  reference[note['pitch']%12,a:b]=np.maximum(reference[note['pitch']%12,a:b],np.exp(-np.linspace(0,1.6,b-a)))
reference=librosa.util.normalize(reference+1e-6,axis=0)
print('ENGRAVING_DTW',i,reference.shape,features.shape,flush=True)
D,path=librosa.sequence.dtw(X=reference,Y=features,metric='cosine',step_sizes_sigma=np.array([[1,1],[1,2],[2,1]]),weights_mul=np.array([1.,1.15,1.15]),global_constraints=True,band_rad=.18)
path=path[::-1];xs=np.unique(path[:,0]);ys=np.array([np.median(path[path[:,0]==x,1]) for x in xs]);seconds=ys*hop/sr+begin*256/sr;assert np.all(np.diff(seconds)>=0)
result={'movement':i,'status':'engraved_score_time_candidate_not_accepted','notation_sha256':score['notation_sha256'],'reference_last_quarter':last,'frame_hop_seconds':hop/sr,'mean_cost':float(D[-1,-1]/len(path)),'warp':[{'quarter':float(quarters[x]),'seconds':float(y)} for x,y in zip(xs,seconds)],'scope':'Independent chroma DTW whose quarter axis is the actual engraved staff. Fixes the reference-coordinate assumption; does not certify repeat routing, grace/tie handling or note-accurate synchronization. No runtime promotion.'}
(OUT/f'engraved_alignment_{i}.json').write_text(json.dumps(result,indent=2)+'\n');print('ENGRAVED_ALIGNMENT_DONE',i,result['mean_cost'],flush=True)
