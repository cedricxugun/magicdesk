from pathlib import Path
from PIL import Image,ImageDraw,ImageFilter
import numpy as np, random
OUT=Path(__file__).resolve().parents[1]/'app'/'assets'
N=2048;rng=np.random.default_rng(1709);random.seed(1709)
def cloud(size,aspect=1):
    a=Image.fromarray(rng.integers(0,256,(size*aspect,size),dtype=np.uint8))
    return np.asarray(a.resize((N,N),Image.Resampling.BICUBIC),dtype=np.float32)/255-.5
def save(a,name):Image.fromarray(np.clip(a,0,255).astype('uint8')).save(OUT/name)
c=cloud(55,4);m=cloud(180,4);fine=rng.normal(0,1,(N,N)).astype('float32')
y,x=np.mgrid[0:N,0:N]/(N-1)
edge=np.minimum.reduce([x,1-x,y*.8,(1-y)*.8])
dirt=np.exp(-edge*73)*(.42+c*.45+m*.22)
color=np.zeros((N,N,3),dtype='float32')
for ch,base in enumerate([218,207,181]):color[:,:,ch]=base+c*18+m*7+fine*.45-dirt*(80+ch*5)
# Wear is concentrated along machined edges, leaving the broad enamel face quiet.
chips=Image.new('L',(N,N));d=ImageDraw.Draw(chips)
for i in range(420):
    xx=random.choice([random.randrange(0,16),random.randrange(N-16,N)])
    yy=random.randrange(N);w=random.randrange(1,6);h=random.randrange(1,15)
    d.ellipse((xx,yy,xx+w,yy+h),fill=random.randint(65,210))
chip=np.asarray(chips,dtype='float32')/255
color=color*(1-chip[:,:,None]) + np.array([76,69,55])[None,None,:]*chip[:,:,None]
# Fine scratches catch light in roughness without turning the object into rust.
scratches=Image.new('L',(N,N));d=ImageDraw.Draw(scratches)
for i in range(1000):
    xx=random.randrange(N);yy=random.randrange(N)
    d.line((xx,yy,xx+random.randrange(-3,4),yy+random.randrange(2,55)),fill=random.randrange(20,95),width=1)
sc=np.asarray(scratches,dtype='float32')/255
color-=sc[:,:,None]*8
save(color,'enamel_albedo.png')
save(77+c*22+m*13+dirt*70+sc*70+chip*70,'enamel_roughness.png')
hmap=m*.06+fine*.0015+sc*.045
dy,dx=np.gradient(hmap)
norm=np.stack([-dx*2,-dy*2,np.ones_like(dx)],axis=-1);norm/=np.linalg.norm(norm,axis=-1)[:,:,None]
save((norm*.5+.5)*255,'enamel_normal.png')
metal=cloud(65);grain=np.asarray(Image.fromarray(rng.integers(0,255,(N,128),dtype='uint8')).resize((N,N)),dtype='float32')/255-.5
save(88+metal*13+grain*11+sc*45,'metal_roughness.png')
save(np.stack([142+metal*7,135+metal*7,122+metal*7],axis=-1),'nickel_albedo.png')
save(np.stack([83+metal*7,81+metal*7,72+metal*7],axis=-1),'steel_albedo.png')
metalheight=grain*.018+sc*.025;dy,dx=np.gradient(metalheight)
norm=np.stack([-dx*3,-dy*3,np.ones_like(dx)],axis=-1);norm/=np.linalg.norm(norm,axis=-1)[:,:,None]
save((norm*.5+.5)*255,'metal_normal.png')
print('HELIOS_PBR_V2_READY',N)
