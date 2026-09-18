"""Apply four locally reviewed tail anchors; retain all earlier warp data and files."""
from pathlib import Path
import json,hashlib,numpy as np
ROOT=Path(__file__).resolve().parents[2];BASE=ROOT/'app/assets/collection/art/I/moonlight_candidate';REVIEW=ROOT/'review/I_refinement/moonlight/onset_refinement';manifest=json.loads((BASE/'manifest.json').read_text());patches=[]
for movement,start,quarters,seed_file in [(1,268.,[270.,272.],'alignment1.json'),(3,1048.,[1050.,1052.],'alignment3_clean.json')]:
 seed_path=BASE/seed_file;seed=json.loads(seed_path.read_text());candidate=json.loads((REVIEW/f'movement_{movement}_scoretime_adaptive_transient.json').read_text());events=[next(e for e in candidate['events'] if e['quarter']==q) for q in quarters]
 # These specific isolated chords were inspected on the actual pitch-energy
 # image. Do not auto-promote the remainder of the algorithm's candidate path.
 assert all(abs(e['broadband_offset'])<.035 and e['audio_onset_strength']>.8 for e in events)
 xs=[r['quarter'] for r in seed['warp']];ys=[r['seconds'] for r in seed['warp']];end=float(xs[-1])
 warp=[r for r in seed['warp'] if float(r['quarter'])<start]+[{'quarter':start,'seconds':float(np.interp(start,xs,ys))}]+[{'quarter':e['quarter'],'seconds':e['candidate_seconds']} for e in events]+[seed['warp'][-1]]
 assert all(b['quarter']>a['quarter'] and b['seconds']>=a['seconds'] for a,b in zip(warp,warp[1:]))
 patch={'movement':movement,'range_quarters':[start,end],'anchors':events,'original_warp_sha256':hashlib.sha256(seed_path.read_bytes()).hexdigest(),'review_image':'review/I_refinement/moonlight/onset_refinement/tail_anchors_review.png','scope':'Only these four isolated chord onsets have pitch/spectral onset correspondence reviewed. Timing remains feature-resolution limited; no whole-work or subjective acceptance.'}
 result={**seed,'warp':warp,'status':'estimated_requires_musical_review','local_tail_review':patch};target=BASE/f'alignment{movement}_tail_r2.json';target.write_text(json.dumps(result,indent=2)+'\n')
 row=manifest['movements'][movement-1];row.setdefault('previous_alignment',row['alignment']);row['alignment']='res://'+str(target.relative_to(ROOT/'app'));patches.append(patch)
(BASE/'manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n')
(REVIEW/'applied_tail_anchors.json').write_text(json.dumps({'patches':patches,'status':'local_tail_correction_remaining_alignment_unaccepted'},indent=2)+'\n');print('TAIL_ANCHORS_APPLIED',len(patches))
