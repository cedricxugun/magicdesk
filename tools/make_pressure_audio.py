from pathlib import Path
import numpy as np,wave
P=Path(__file__).resolve().parents[1]/'app'/'assets';SR=44100;rng=np.random.default_rng(7351)
def noise(n,lo,hi):
    a=rng.normal(0,1,n);f=np.fft.rfftfreq(n,1/SR);s=np.fft.rfft(a)
    weight=(1-np.exp(-(f/lo)**4))*np.exp(-(f/hi)**4)
    a=np.fft.irfft(s*weight,n);return a/(np.std(a)+1e-8)
def pulse(t,start,attack,decay):
    q=t-start;return (q>0)*(1-np.exp(-np.maximum(q,0)/attack))*np.exp(-np.maximum(q,0)/decay)
def save(name,t,mono,width=.10):
    diffuse=noise(len(t),650,6000)*width
    env=np.minimum(np.arange(len(t))/500,(len(t)-np.arange(len(t)))/1500).clip(0,1)
    spread=np.abs(mono)*diffuse
    a=np.stack([mono+spread,mono-spread],axis=1)*env[:,None]
    peak=max(.95,float(np.max(np.abs(a))));a=np.tanh(a/peak*1.2)*.74
    with wave.open(str(P/(name+'.wav')),'wb') as f:
        f.setnchannels(2);f.setsampwidth(2);f.setframerate(SR);f.writeframes((a*32767).astype('<i2').tobytes())
def clanks(t,start):
    total=np.zeros(len(t))
    for i in range(6):
        q=t-(start+i*.026);e=pulse(t,start+i*.026,.0018,.037)
        total+=(np.sin(q*2*np.pi*(730+i*23))*.45+np.sin(q*2*np.pi*1940)*.12)*e
    return total
t=np.arange(int(SR*4.8))/SR
air=noise(len(t),160,6300);body=noise(len(t),20,340)
air_env=pulse(t,.38,.040,.66)+.26*pulse(t,1.00,.04,.53)
charge=(.05*np.sin(2*np.pi*(68*t+28*t*t))+.035*np.sin(2*np.pi*340*t))*pulse(t,0,.06,.40)
impact=(np.sin(2*np.pi*(47*t-2*t*t))*.36+body*.12)*pulse(t,.72,.008,.30)
tail=.12*air*pulse(t,1.9,.2,.5)
save('pressure_open',t,charge+.32*air*air_env+impact+clanks(t,.20)*.42+tail)
t=np.arange(int(SR*3.3))/SR
air=noise(len(t),190,5400);motor=np.sin(2*np.pi*(130*t-12*t*t))*.08
save('seal_close',t,motor*pulse(t,0,.15,.70)+air*.16*pulse(t,.10,.015,.42)+clanks(t,1.85)*.45+air*.12*pulse(t,2.1,.025,.15))
t=np.arange(int(SR*3.6))/SR
air=noise(len(t),140,6200);hum=np.sin(2*np.pi*(170*t-16*t*t))*.13
save('shutdown',t,hum*pulse(t,0,.04,.9)+.18*air*pulse(t,.12,.045,.56)+clanks(t,2.0)*.36+np.sin(t*2*np.pi*580)*pulse(t,2.45,.003,.12)*.07)
t=np.arange(int(SR*1.4))/SR
save('ignition',t,np.sin(2*np.pi*(65*t+72*t*t))*.17*pulse(t,0,.025,.60)+clanks(t,.48)*.18)
print('FOUR_CINEMATIC_PRESSURE_FOLEY_TRACKS_READY')
