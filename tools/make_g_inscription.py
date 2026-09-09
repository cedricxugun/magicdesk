"""Original optical archive completion cue: sequential comb tones and latch."""
import math,wave,struct,pathlib,random
root=pathlib.Path(__file__).resolve().parents[1];rate=44100;duration=4.4;rng=random.Random(734);samples=[]
for i in range(int(duration*rate)):
    t=i/rate;value=0
    for k,f in enumerate([174.6,261.6,349.2,523.3,698.5,1046.5]):
        age=t-k*.145
        if age>=0:value+=.065*math.sin(math.tau*f*age)*(1-math.exp(-age*120))*math.exp(-age*1.7)
    value+=(rng.random()*2-1)*.06*math.exp(-t*65)
    value+=.065*math.sin(math.tau*(92*t+14*t*t))*math.exp(-t*3)
    value*=min(1,(duration-t)/.2);samples.append(value)
path=root/'app/assets/collection/art/G/inscription.wav'
with wave.open(str(path),'wb') as f:
    f.setnchannels(2);f.setsampwidth(2);f.setframerate(rate)
    f.writeframes(b''.join(struct.pack('<hh',int(v*32767),int(samples[max(0,i-11)]*32767*.97)) for i,v in enumerate(samples)))
print(path)
