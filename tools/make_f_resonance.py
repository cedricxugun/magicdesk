"""Original short modal-metal calibration sound, generated locally as PCM."""
import math,random,wave,struct,pathlib
ROOT=pathlib.Path(__file__).resolve().parents[1]
path=ROOT/'app/assets/collection/art/F/calibration.wav'
rate=44100;duration=3.2;rng=random.Random(971);samples=[];noise=0.0
for i in range(int(rate*duration)):
    t=i/rate;attack=1-math.exp(-t*160)
    modal=sum(math.sin(math.tau*f*t+p)*math.exp(-t*d)*a for f,a,d,p in [(91,.19,3.7,0),(183,.28,1.7,.2),(367,.13,2.2,.4),(649,.06,3.0,.1),(973,.025,3.8,0)])
    sweep=.09*math.sin(math.tau*(220*t+80*t*t))*math.exp(-t*5)
    noise=noise*.93+(rng.random()*2-1)*.07
    value=attack*(modal+sweep+noise*.04*math.exp(-t*8))
    tail=max(0,(duration-t)/.25);value*=min(1,tail)
    samples.append(value)
peak=max(abs(x) for x in samples);scale=.55/peak
with wave.open(str(path),'wb') as output:
    output.setnchannels(2);output.setsampwidth(2);output.setframerate(rate)
    output.writeframes(b''.join(struct.pack('<hh',int(v*scale*32767),int(samples[max(0,i-9)]*scale*.96*32767)) for i,v in enumerate(samples)))
print(path)
