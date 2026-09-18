"""Plot independent candidate timings against the actual pitch spectrogram."""
from pathlib import Path
import json,numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
ROOT=Path(__file__).resolve().parents[2];OUT=ROOT/'review/I_refinement/moonlight/onset_refinement';plt.rcParams.update({'font.size':9,'axes.spines.top':False,'axes.spines.right':False})
for movement,regions in [(1,[(4,13),(193,199),(326,332)]),(2,[(0,9),(58,65),(119,129)]),(3,[(2,10),(210,217),(472,489)])]:
 r=json.loads((OUT/f'movement_{movement}.json').read_text());cache=next(OUT.glob(f'm{movement}_*_features.npz'));cqt=np.load(cache)['cqt'];seconds=np.arange(cqt.shape[1])*r['hop']/r['sample_rate'];db=20*np.log10(np.maximum(cqt,1e-5));db-=db.max()
 fig,axes=plt.subplots(len(regions),1,figsize=(13,9),constrained_layout=True)
 for ax,(start,end) in zip(axes,regions):
  a=int(start*r['sample_rate']/r['hop']);b=int(end*r['sample_rate']/r['hop']);ax.imshow(db[:,a:b],origin='lower',aspect='auto',extent=(seconds[a],seconds[b-1],20.5,108.5),cmap='magma',vmin=-65,vmax=-8,interpolation='nearest')
  for event in r['events']:
   if not start-.5<event['candidate_seconds']<end+.5:continue
   for pitch in event['pitches']:
    ax.plot(event['old_seconds'],pitch,'x',color='#42d9ff',markersize=5,markeredgewidth=1)
    ax.plot(event['candidate_seconds'],pitch,'o',mfc='none',mec='#8cff7a',markersize=5,markeredgewidth=1)
  ax.set_xlim(start,end);ax.set_ylim(30,90);ax.set_ylabel('MIDI pitch');ax.set_xlabel('Recording time (seconds)');ax.set_title(f'Movement {movement} | {start}–{end}s',loc='left')
 fig.suptitle('Moonlight onset review — cyan ×: current warp; green ○: independent candidate\nCandidates are not annotated truth; bright regions are measured recording energy.',fontsize=12)
 fig.savefig(OUT/f'movement_{movement}_review.png',dpi=150);plt.close(fig)
print('ONSET_REVIEW_PLOTS_SAVED')
