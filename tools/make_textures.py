from pathlib import Path
from PIL import Image,ImageFilter,ImageDraw
import numpy as np,random,math,wave
OUT=Path(__file__).resolve().parents[1]/'app'/'assets';OUT.mkdir(parents=True,exist_ok=True)
rng=np.random.default_rng(1955);n=1024
cloud=Image.fromarray(rng.integers(0,256,(64,64),dtype=np.uint8)).resize((n,n),Image.Resampling.BICUBIC).filter(ImageFilter.GaussianBlur(12))
c=np.asarray(cloud,dtype=float)/255-.5;fine=rng.normal(0,1,(n,n))
rgb=np.stack([231+c*10+fine*.6,223+c*12+fine*.6,201+c*14+fine*.6],axis=-1)
Image.fromarray(np.clip(rgb,0,255).astype('uint8')).save(OUT/'enamel_albedo.png')
rough=np.clip(83+c*20+rng.normal(0,3,(n,n)),45,125).astype('uint8')
Image.fromarray(rough).save(OUT/'enamel_roughness.png')
metal=Image.fromarray(np.clip(65+rng.normal(0,3,(n,n)),35,100).astype('uint8'))
d=ImageDraw.Draw(metal);random.seed(1955)
for i in range(140):
 x=random.randrange(n);y=random.randrange(n);d.line((x,y,x+random.randint(3,35),y+random.randint(-2,2)),fill=random.randint(85,110),width=1)
metal.save(OUT/'metal_roughness.png')
# Original simple app icon, deliberately readable in the Windows taskbar.
icon=Image.new('RGBA',(256,256),(0,0,0,0));d=ImageDraw.Draw(icon)
d.ellipse((14,14,242,242),fill='#25282c',outline='#c6b391',width=12)
d.ellipse((59,40,197,216),fill='#ded4b8',outline='#66594b',width=7)
for x in [97,128,159]:d.arc((x-34,40,x+34,216),-87,87,fill='#6b5a48',width=4)
d.ellipse((106,99,150,143),fill='#ed692c',outline='#ffc67c',width=5)
icon.save(OUT/'icon.png');icon.save(OUT/'icon.ico',sizes=[(32,32),(64,64),(128,128),(256,256)])
sr=44100
def write_sound(name,dur,kind):
 t=np.arange(int(sr*dur))/sr;noise=rng.normal(0,1,len(t));sound=np.zeros_like(t)
 if kind=='click':sound=(.45*np.sin(2*np.pi*1700*t)+.28*np.sin(2*np.pi*560*t)+.16*noise)*np.exp(-t*48)
 elif kind=='wake':sound=(np.sin(2*np.pi*(90*t+180*t*t))*.23+np.sin(2*np.pi*880*t)*.05)*np.sin(np.pi*t/dur)**1.2
 elif kind=='open':
  sound=(.11*noise+.15*np.sin(2*np.pi*(140*t+20*t*t)))*np.sin(np.pi*t/dur)**.8
  for start in np.linspace(.12,dur-.25,6):sound+=.16*np.sin(2*np.pi*1200*t)*np.exp(-np.maximum(t-start,0)*45)*(t>=start)
 elif kind=='overload':sound=(.18*np.sin(2*np.pi*(120*t+180*t*t))+.06*noise)*np.sin(np.pi*t/dur)**.7
 elif kind=='explode':sound=(.25*noise*np.exp(-t*9)+.30*np.sin(2*np.pi*(120*t+140*t*t))*np.exp(-t*4))
 elif kind=='assemble':
  sound=(.13*noise+.14*np.sin(2*np.pi*(650*t-130*t*t)))*np.sin(np.pi*t/dur)**1.3
  for start in [.25,.48,.7,1.0,1.2]:sound+=.12*np.sin(2*np.pi*1100*t)*np.exp(-np.maximum(t-start,0)*45)*(t>=start)
 elif kind=='hum':sound=.17*np.sin(2*np.pi*110*t)+.05*np.sin(2*np.pi*220*t)+.03*np.sin(2*np.pi*330*t)
 sound=np.clip(sound,-.95,.95)
 with wave.open(str(OUT/(name+'.wav')),'wb') as f:f.setnchannels(1);f.setsampwidth(2);f.setframerate(sr);f.writeframes((sound*32767).astype('<i2').tobytes())
for args in [('click',.12,'click'),('wake',1.0,'wake'),('open',1.7,'open'),('overload',2.,'overload'),('explode',1.0,'explode'),('assemble',1.55,'assemble'),('hum',1.,'hum')]:write_sound(*args)
print('TEXTURES_AND_ORIGINAL_SOUNDS_READY',OUT)
