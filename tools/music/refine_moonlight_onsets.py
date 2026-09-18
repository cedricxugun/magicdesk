"""Independent pitch/onset refinement candidates; never overwrite runtime warps."""
from pathlib import Path
import argparse,json,hashlib,collections
import numpy as np
import librosa,mido
from scipy.ndimage import maximum_filter1d
from scipy.signal import find_peaks
ROOT=Path(__file__).resolve().parents[2];OUT=ROOT/'review/I_refinement/moonlight/onset_refinement';OUT.mkdir(parents=True,exist_ok=True)
parser=argparse.ArgumentParser();parser.add_argument('--movement',type=int,required=True,choices=[1,2,3]);parser.add_argument('--adaptive',action='store_true');parser.add_argument('--score-time',action='store_true');parser.add_argument('--transient-weighted',action='store_true');args=parser.parse_args();movement=args.movement
manifest=json.loads((ROOT/'app/assets/collection/art/I/moonlight_candidate/manifest.json').read_text());row=manifest['movements'][movement-1];audio=ROOT/'app'/row['audio'].removeprefix('res://');runtime=ROOT/'app'/row['alignment'].removeprefix('res://');prior=json.loads(runtime.read_text());sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();assert sha(audio)==row['audio_sha256']
midi_path=ROOT/'production/I_refinement/moonlight/engraving'/f'moonlight{movement}-staff.midi';midi=mido.MidiFile(midi_path);grouped=collections.defaultdict(list)
for track in midi.tracks:
 tick=0
 for event in track:
  tick+=event.time
  if event.type=='note_on' and event.velocity:grouped[tick].append((event.note,event.velocity))
quarters=np.array(sorted(grouped))/midi.ticks_per_beat;notes=[grouped[t] for t in sorted(grouped)]
if args.score_time:
 score=json.loads((OUT/f'score_reference_{movement}.json').read_text());quarters=np.array([e['quarter'] for e in score['events']]);notes=[[(pitch,90) for pitch in e['pitches']] for e in score['events']]
old=np.interp(quarters,[p['quarter'] for p in prior['warp']],[p['seconds'] for p in prior['warp']])
sr=22050;hop=256;cache=OUT/f'm{movement}_{sha(audio)[:10]}_features.npz'
if cache.exists():
 data=np.load(cache);cqt=data['cqt'];flux=data['flux'];broadband=data['broadband']
else:
 print('PITCH_FEATURES',movement,flush=True);y,_=librosa.load(audio,sr=sr,mono=True)
 cqt=np.abs(librosa.cqt(y,sr=sr,hop_length=hop,fmin=librosa.midi_to_hz(21),n_bins=88,bins_per_octave=12)).astype(np.float32)
 # Per-key scale preserves octaves while tempering the stronger bass keys.
 scale=np.maximum(np.percentile(cqt,85,axis=1,keepdims=True),.001)
 whitened=np.log1p(cqt/scale)
 flux=np.maximum(0,whitened-np.pad(whitened[:,:-3],((0,0),(3,0)),mode='edge')).astype(np.float32)
 broadband=librosa.onset.onset_strength(y=y,sr=sr,hop_length=hop,n_fft=2048).astype(np.float32)
 np.savez_compressed(cache,cqt=cqt,flux=flux,broadband=broadband)
print('MONOTONE_ONSET_MATCH',movement,len(quarters),flush=True)
frames=flux.shape[1];times=np.arange(frames)*hop/sr
# CQT analysis spreads low-key transients in time. A short local maximum finds
# the same attack across neighboring frames, not an inferred acoustic timestamp.
support=maximum_filter1d(flux,size=5,axis=1,mode='nearest');norm=np.maximum(np.linalg.norm(support,axis=0),1e-6)
strength=np.linalg.norm(flux,axis=0);strength/=max(np.percentile(strength,95),1e-6)
span=.40;choices=[];local=[];pitch_scores=[]
for event_index,(expected,pitches) in enumerate(zip(old,notes)):
 if args.adaptive:
  adjacent=[]
  if event_index>0:adjacent.append(expected-old[event_index-1])
  if event_index+1<len(old):adjacent.append(old[event_index+1]-expected)
  local_gap=min(adjacent) if adjacent else .4
  span=max(.40,min(2.0 if args.score_time else 1.25,local_gap*(.80 if args.score_time else .48)))
 lo=max(1,int((expected-span)*sr/hop));hi=min(frames-1,int((expected+span)*sr/hop)+1);candidates=np.arange(lo,max(lo+1,hi))
 target=np.zeros(88)
 for pitch,velocity in pitches:
  if 21<=pitch<=108:target[pitch-21]=max(target[pitch-21],(velocity/127)**.5)
 target/=max(np.linalg.norm(target),1e-8)
 match=(target@support[:,candidates])/norm[candidates]
 evidence=match*np.sqrt(np.clip(strength[candidates]/max(float(np.max(strength[candidates])),1e-6),0,1)) if args.transient_weighted else match
 scores=-2.0*evidence-.16*np.clip(strength[candidates],0,2)+.32*((times[candidates]-expected)/span)**2
 choices.append(candidates);local.append(scores);pitch_scores.append(match)
back=[];cost=local[0].copy()
for index in range(1,len(choices)):
 dt=(choices[index][None,:]-choices[index-1][:,None])*hop/sr;expected=max(.035,old[index]-old[index-1])
 transition=.10*np.minimum(((dt-expected)/expected)**2,25);transition[dt<=0]=np.inf
 total=cost[:,None]+transition;parents=np.argmin(total,axis=0);cost=local[index]+total[parents,np.arange(total.shape[1])];back.append(parents.astype(np.int16))
 assert np.isfinite(cost).any(),('No monotone onset path',movement,index)
selected=[int(np.argmin(cost))]
for parents in back[::-1]:selected.append(int(parents[selected[-1]]))
selected=selected[::-1];corrected=np.array([times[c[k]] for c,k in zip(choices,selected)]);assert np.all(np.diff(corrected)>0)
# Separate broadband onset peaks provide additional review context. This is not
# annotated ground truth, and closeness to a peak is not proof of musical accuracy.
peaks,_=find_peaks(broadband,height=np.percentile(broadband,60),distance=3,prominence=.15)
peak_times=peaks*hop/sr;events=[]
for i,(q,a,b,pitches,k) in enumerate(zip(quarters,old,corrected,notes,selected)):
 nearest=float(peak_times[np.argmin(abs(peak_times-b))]) if len(peak_times) else None
 events.append({'quarter':float(q),'old_seconds':float(a),'candidate_seconds':float(b),'delta_seconds':float(b-a),'pitches':sorted(set(p for p,v in pitches)),'pitch_onset_support':float(pitch_scores[i][k]),'broadband_peak_seconds':nearest,'broadband_offset':None if nearest is None else float(b-nearest),'audio_onset_strength':float(strength[choices[i][k]]),'search_boundary':k in [0,len(choices[i])-1]})
result={'movement':movement,'status':'independent_onset_candidate_not_accepted','quarter_reference':'engraved notehead times including ties/grace groups' if args.score_time else 'MIDI performance ticks','recording_sha256':sha(audio),'midi_sha256':sha(midi_path),'prior_runtime_sha256':sha(runtime),'transient_weighted':args.transient_weighted,'feature_cache':cache.name,'feature_cache_sha256':sha(cache),'script_sha256':sha(Path(__file__)),'sample_rate':sr,'hop':hop,'search_policy':'adaptive isolated events up to 2.0 seconds' if args.score_time else 'adaptive isolated events up to 1.25 seconds' if args.adaptive else 'fixed 0.40 seconds','events':events,'summary':{'count':len(events),'median_abs_change':float(np.median(abs(corrected-old))),'p95_abs_change':float(np.percentile(abs(corrected-old),95)),'boundary_count':sum(x['search_boundary'] for x in events),'median_pitch_support':float(np.median([x['pitch_onset_support'] for x in events]))},'limitations':['Candidate is constrained by old coarse warp and does not independently solve ambiguous repeat routing.','Pitch/onset support and broadband peaks are algorithmic evidence, not annotated ground truth or a listening review.','CQT low-frequency latency, pedal, dynamics and ornaments limit precision. No automatic runtime promotion.']}
(OUT/('movement_%d%s%s%s.json'%(movement,'_scoretime' if args.score_time else '', '_adaptive' if args.adaptive else '', '_transient' if args.transient_weighted else ''))).write_text(json.dumps(result,indent=2)+'\n');print('ONSET_CANDIDATE',movement,result['summary'],flush=True)
