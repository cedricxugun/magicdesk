"""Author short original modal-metal cues offline; no external recordings."""
from pathlib import Path
import numpy as np,json,wave,hashlib
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'app/assets/collection/art/I/echo_r2';OUT.mkdir(parents=True,exist_ok=True)
rate=48000;duration=1.6;t=np.arange(int(rate*duration))/rate;random=np.random.default_rng(210913)
# Three related prong resonances, intentionally restrained rather than a chord.
frequencies=[196.,392.4,537.2,783.6,1051.3,1452.7]
amplitudes=[.42,.28,.115,.078,.045,.027];decays=[.58,.46,.31,.26,.19,.13]
strike=random.normal(0,1,len(t));strike=np.r_[0,np.diff(strike)]*.009*np.exp(-t*110)
body=sum(a*np.sin(2*np.pi*f*t+.08*i)*np.exp(-t/tau) for i,(f,a,tau) in enumerate(zip(frequencies,amplitudes,decays)))
body=(body+strike)*(1-np.exp(-t*650));body*=np.minimum(1,(duration-t)/.12);body*=.24/max(abs(body))
records=[]
for name,is_return in [('send',False),('return',True)]:
 signal=body.copy()
 if is_return:
  # Return loses high-frequency attack; stronger reduction is applied by event gain.
  signal=np.convolve(signal,np.ones(9)/9,mode='same')*.82
  signal*=1-np.exp(-t*140)
 left=signal.copy();right=signal.copy()
 for delay,weight in [(.037,.11),(.061,.06)]:
  n=int(delay*rate);left[n:]+=signal[:-n]*weight;right[n+71:]+=signal[:-(n+71)]*weight*.85
 stereo=np.stack([left,right],axis=1);peak=float(np.max(abs(stereo)));assert peak<.5
 pcm=np.round(np.clip(stereo,-1,1)*32767).astype('<i2');path=OUT/(name+'.wav')
 with wave.open(str(path),'wb') as f:f.setnchannels(2);f.setsampwidth(2);f.setframerate(rate);f.writeframes(pcm.tobytes())
 records.append({'file':str(path.relative_to(ROOT)),'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'duration':duration,'peak_linear':peak,'rms':float(np.sqrt(np.mean(stereo**2))),'dc':float(stereo.mean())})
manifest={'method':'Original offline modal synthesis from listed partials and deterministic transient; no third-party recording.','sample_rate':rate,'partials_hz':frequencies,'files':records,'scope':'Candidate mechanical acoustic cues. PCM/level checks are technical evidence, not listening or final audio acceptance.'}
(ROOT/'production/I_refinement/part_a_mouth/shutter_r2/cassette/echo_r2/audio_manifest.json').write_text(json.dumps(manifest,indent=2)+'\n');print(json.dumps(records,indent=2))
