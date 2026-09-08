from pathlib import Path
import numpy as np
N=128
ROOT=Path(__file__).resolve().parents[1]
rng=np.random.default_rng(194806)
k=np.fft.fftfreq(N).astype(np.float32)*N
k2=k[:,None,None]**2+k[None,:,None]**2+k[None,None,:]**2
pot=[]
for i in range(3):
 a=rng.standard_normal((N,N,N),dtype=np.float32)
 pot.append(np.fft.ifftn(np.fft.fftn(a)*np.exp(-k2/85.0)).real.astype(np.float32))
def deriv(a,axis):return (np.roll(a,-1,axis)-np.roll(a,1,axis))*.5
curl=[deriv(pot[2],1)-deriv(pot[1],2),deriv(pot[0],2)-deriv(pot[2],0),deriv(pot[1],0)-deriv(pot[0],1)]
noise=rng.standard_normal((N,N,N),dtype=np.float32)
power=(k2+5.0)**(-.64)*np.exp(-k2/2200.0)
density=np.fft.ifftn(np.fft.fftn(noise)*power).real.astype(np.float32)
density=(density-density.mean())/density.std()
out=np.empty((N,N,N,4),dtype=np.uint8)
for i,c in enumerate(curl):out[:,:,:,i]=np.clip(.5+c/(c.std()*5.2),0,1)*255
out[:,:,:,3]=np.clip(.5+density*.165,0,1)*255
(ROOT/'tools/pressure_field.rgba').write_bytes(out.tobytes())
print('PRESSURE_FIELD_128_READY',out.nbytes)
