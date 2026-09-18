"""Extract three actual recording energy bands for visual chamber response."""
import json,hashlib,subprocess
from pathlib import Path
import numpy as np
ROOT=Path(__file__).resolve().parents[2];OUT=ROOT/'app/assets/collection/art/I/chamber_response_r35';OUT.mkdir(parents=True,exist_ok=True);manifest=json.loads((ROOT/'app/assets/collection/art/I/moonlight_candidate/manifest.json').read_text());rate=11025;hop=220;size=1024;frequencies=np.fft.rfftfreq(size,1/rate);ranges=[(55,350),(350,1500),(1500,5000)];window=np.hanning(size);rows=[];all_values=[]
for row in manifest['movements']:
    path=ROOT/'app'/row['audio'].removeprefix('res://');assert hashlib.sha256(path.read_bytes()).hexdigest()==row['audio_sha256']
    decoded=subprocess.run(['/opt/homebrew/bin/ffmpeg','-nostdin','-v','error','-i',str(path),'-f','f32le','-ac','1','-ar',str(rate),'-'],capture_output=True,check=True).stdout;samples=np.frombuffer(decoded,dtype='<f4');padded=np.pad(samples,(size//2,size));frames=np.lib.stride_tricks.sliding_window_view(padded,size)[::hop][:int(np.ceil(len(samples)/hop))+1];values=np.empty((len(frames),3))
    for start in range(0,len(frames),1024):
        spectrum=np.abs(np.fft.rfft(frames[start:start+1024]*window,axis=1))**2
        for band,(low,high)in enumerate(ranges):values[start:start+1024,band]=np.sqrt(spectrum[:,(frequencies>=low)&(frequencies<high)].sum(axis=1))/window.sum()
    rows.append({'movement':row['movement'],'audio_sha256':row['audio_sha256'],'decoded_seconds':len(samples)/rate,'values':values});all_values.append(values);print('AUDIO_BANDS',row['movement'],len(values),flush=True)
reference=np.quantile(np.concatenate(all_values),.985,axis=0);result=[]
for row in rows:
    value=np.clip(row['values']/reference,0,1)**.65
    # Offline attack/release envelope follows recording time on pause and seek.
    attack=np.exp(-(hop/rate)/.025);release=np.exp(-(hop/rate)/.16);state=np.zeros(3)
    for i in range(len(value)):
        coefficient=np.where(value[i]>state,attack,release);state=coefficient*state+(1-coefficient)*value[i];value[i]=state
    result.append({**row,'values':np.round(value,5).tolist()})
payload={'interval_seconds':hop/rate,'bands_hz':ranges,'sample_rate':rate,'fft_window_samples':size,'normalization_reference':reference.tolist(),'movements':result,'scope':'Three recording-derived energy bands for visual response; not note/pitch detection or proof of score alignment.'};path=OUT/'response_bands.json';path.write_text(json.dumps(payload,separators=(',',':'))+'\n');manifest['chamber_response_envelope']='res://'+str(path.relative_to(ROOT/'app'));manifest['chamber_response_envelope_sha256']=hashlib.sha256(path.read_bytes()).hexdigest();(OUT/'music_manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
