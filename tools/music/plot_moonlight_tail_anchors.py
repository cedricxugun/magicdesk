from pathlib import Path
import json,numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
ROOT=Path(__file__).resolve().parents[2];OUT=ROOT/'review/I_refinement/moonlight/onset_refinement';fig,axes=plt.subplots(2,1,figsize=(12,7),constrained_layout=True)
for ax,i,region,chosen in [(axes[0],1,(320,331),[270.,272.]),(axes[1],3,(483,488.5),[1050.,1052.])]:
 r=json.loads((OUT/f'movement_{i}_scoretime_adaptive_transient.json').read_text());c=np.load(OUT/r['feature_cache'])['cqt'];times=np.arange(c.shape[1])*r['hop']/r['sample_rate'];a=np.searchsorted(times,region[0]);b=np.searchsorted(times,region[1]);db=20*np.log10(np.maximum(c,1e-5));db-=db.max()
 ax.imshow(db[:,a:b],origin='lower',aspect='auto',extent=(times[a],times[b-1],20.5,108.5),cmap='magma',vmin=-65,vmax=-8)
 for q in chosen:
  e=next(e for e in r['events'] if abs(e['quarter']-q)<1e-5)
  ax.axvline(e['old_seconds'],color='#42d9ff',linestyle='--',lw=1.2)
  ax.axvline(e['candidate_seconds'],color='#8cff7a',lw=1.2)
  for pitch in e['pitches']:ax.scatter(e['candidate_seconds'],pitch,s=30,facecolors='none',edgecolors='#8cff7a')
  ax.text(e['candidate_seconds']+.02,90,f'q{q:g}: {e["candidate_seconds"]:.3f}s',color='#134d09',fontsize=9,bbox={'facecolor':'white','alpha':.9,'edgecolor':'none'})
 ax.set_xlim(region);ax.set_ylim(30,94);ax.set_xlabel('Recording seconds');ax.set_ylabel('MIDI pitch');ax.set_title(f'Movement {i}: actual engraved simultaneous chord groups',loc='left')
fig.suptitle('Tail onset anchors — cyan dashed: current warp; green: reviewed candidate\nPitch energy + separate broadband onset evidence; no whole-work accuracy claim.',fontsize=12)
fig.savefig(OUT/'tail_anchors_review.png',dpi=150)
