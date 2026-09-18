"""Estimate score-quarter to recording-time alignment. Never auto-accept musical accuracy.
Usage: /tmp/magicdesk-music-venv/bin/python tools/music/align_moonlight.py --movement 1
"""
from pathlib import Path
import argparse,json,hashlib,collections
import numpy as np
import mido,librosa
ROOT=Path(__file__).resolve().parents[2];BASE=ROOT/'production/I_refinement/moonlight';OUT=ROOT/'review/I_refinement/moonlight';OUT.mkdir(exist_ok=True)
p=argparse.ArgumentParser();p.add_argument('--movement',type=int,choices=[1,2,3],required=True);args=p.parse_args();i=args.movement
recording=BASE/(f'pitman_movement_{i}.ogg' if i<3 else 'pitman_movement_3_original.mp3');midi_path=BASE/'engraving'/f'moonlight{i}-staff.midi'
midi=mido.MidiFile(midi_path);attacks=[];unmatched=[]
for track_index,track in enumerate(midi.tracks):
    tick=0;active=collections.defaultdict(list)
    for event in track:
        tick+=event.time
        if event.type=='note_on' and event.velocity:
            active[(event.channel,event.note)].append((tick,event.velocity))
        elif event.type=='note_off' or (event.type=='note_on' and not event.velocity):
            key=(event.channel,event.note)
            if not active[key]:unmatched.append((track_index,tick,event.note));continue
            start,velocity=active[key].pop(0);attacks.append({'quarter':start/midi.ticks_per_beat,'end_quarter':tick/midi.ticks_per_beat,'pitch':event.note,'velocity':velocity,'track':track_index})
    for key,values in active.items():
        if values:unmatched.append((track_index,key,values))
assert not unmatched,unmatched[:5]
attacks.sort(key=lambda x:(x['quarter'],x['pitch']));total_quarters=max(x['end_quarter'] for x in attacks)
print('AUDIO_FEATURES',i,flush=True)
y,sr=librosa.load(recording,sr=22050,mono=True)
# Retain original-file time and trim only leading/trailing low-level silence for alignment.
trimmed,interval=librosa.effects.trim(y,top_db=48);start_seconds=interval[0]/sr;end_seconds=interval[1]/sr;hop=2048
features=librosa.feature.chroma_cqt(y=trimmed,sr=sr,hop_length=hop,fmin=librosa.note_to_hz('C1'),n_octaves=7)
features=np.maximum(features,0.)**.7
frames=features.shape[1];quarter_axis=np.linspace(0,total_quarters,frames);reference=np.zeros((12,frames),dtype=np.float64)
for note in attacks:
    a=int(np.searchsorted(quarter_axis,note['quarter']));b=int(np.searchsorted(quarter_axis,note['end_quarter']+.12));b=min(frames,max(a+1,b))
    if a>=frames:continue
    weights=np.exp(-np.linspace(0,1.6,b-a))*(note['velocity']/127.)**.5
    reference[note['pitch']%12,a:b]+=weights
reference=np.maximum(reference,1e-5);reference=librosa.util.normalize(reference,axis=0);features=librosa.util.normalize(features+1e-5,axis=0)
print('DTW',i,frames,flush=True)
D,path=librosa.sequence.dtw(X=reference,Y=features,metric='cosine',step_sizes_sigma=np.array([[1,1],[1,2],[2,1]]),weights_mul=np.array([1.,1.15,1.15]),global_constraints=True,band_rad=.18)
path=path[::-1];buckets=collections.defaultdict(list)
for score_frame,audio_frame in path:buckets[int(score_frame)].append(int(audio_frame))
knots_x=np.array(sorted(buckets));knots_y=np.array([np.median(buckets[k]) for k in knots_x]);mapped=np.interp(np.arange(frames),knots_x,knots_y)*hop/sr+start_seconds
assert np.all(np.diff(mapped)>=0)
notation=json.loads((BASE/'engraving'/f'moonlight{i}-notation.json').read_text())
measures=[]
from fractions import Fraction
for measure in notation['measures']:
    q=float(Fraction(measure['first_quarter']));seconds=float(np.interp(q,quarter_axis,mapped));measures.append({'bar':measure['bar'],'score_quarter':q,'estimated_audio_seconds':round(seconds,5)})
# Sparse warp and estimated note attacks are review material; do not silently bind them to App.
notes=[dict(n,estimated_audio_seconds=round(float(np.interp(n['quarter'],quarter_axis,mapped)),5)) for n in attacks]
result={'movement':i,'status':'estimated_requires_musical_review','recording':str(recording.relative_to(ROOT)),'recording_sha256':hashlib.sha256(recording.read_bytes()).hexdigest(),'midi_sha256':hashlib.sha256(midi_path.read_bytes()).hexdigest(),'notation_sha256':hashlib.sha256((BASE/'engraving'/f'moonlight{i}-notation.json').read_bytes()).hexdigest(),'recording_duration':len(y)/sr,'active_audio_bounds':[start_seconds,end_seconds],'total_score_quarters':total_quarters,'dtw_frames':frames,'mean_path_cost':float(D[-1,-1]/len(path)),'warp':[{'quarter':round(float(quarter_axis[k]),6),'seconds':round(float(mapped[k]),6)} for k in list(range(0,frames,4))+([frames-1] if (frames-1)%4 else [])],'measures':measures,'note_attacks':notes,'limitations':['Chroma DTW estimate; no verified note-accurate sync or final acceptance.','Pedal, repeated sections and rubato can create ambiguous alignment; listen against score at landmarks.','Quantization and feature hop limit timing precision; no claim of sample-accurate note hits.']}
(OUT/f'alignment{i}_candidate.json').write_text(json.dumps(result,indent=2)+'\n');print('ALIGNMENT_CANDIDATE',i,result['mean_path_cost'],len(measures),flush=True)
