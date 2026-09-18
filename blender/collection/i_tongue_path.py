"""Tape-spring tongue: retained leader, flattening entry guide, rotating layered coil.

Numerical art/kinematics model, not an elastic stress simulation. All lengths are scene units.
"""
import math
import numpy as np
BANDS=[((.46,.59),(-.47,-.57),-.12,-.43),((.05,.745),(-.56,-.49),-.025,-.30),((-.29,.685),(-.67,-.28),-.025,-.245)]
def normalize(a):return a/np.maximum(1e-12,np.linalg.norm(a,axis=-1,keepdims=True))
def smooth(a):a=np.clip(a,0,1);return a*a*(3-2*a)
class TonguePath:
 def __init__(self,index,rows=360,columns=16):
  self.index=index;self.rows=rows;self.columns=columns
  aa,dd,self.left,self.right=BANDS[index];self.A=np.array([*aa,.014+index*.036]);self.D=np.array([*dd,self.A[2]])
  self.axis=normalize(self.D-self.A);self.side=np.array([-self.axis[1],self.axis[0],0]);self.mid=(self.left+self.right)/2
  self.front_t=np.linspace(0,1,4097);points=self.front(self.front_t);self.front_s=np.r_[0,np.cumsum(np.linalg.norm(np.diff(points,axis=0),axis=1))];self.length=float(self.front_s[-1])
  self.entry=points[0];self.entry_tangent=-normalize(self.front_derivative(np.array([0.]))[0]);self.outward=normalize(self.entry*np.array([1.,1.,0.]));self.back=np.array([0.,0.,1.]);self.roll_side=normalize(np.cross(self.back,self.outward))
  if np.dot(self.roll_side,self.side)<0:self.roll_side=-self.roll_side
  self.turn_controls=np.array([self.entry,self.entry+self.entry_tangent*.009,self.entry+self.outward*.010,self.entry+self.outward*.016])
  self.turn_t=np.linspace(0,1,1025);turn_points=self.turn(self.turn_t);self.turn_s=np.r_[0,np.cumsum(np.linalg.norm(np.diff(turn_points,axis=0),axis=1))];self.turn_length=float(self.turn_s[-1]);self.turn_end=turn_points[-1]
  self.entry_radius=.017;self.bend_length=math.pi*self.entry_radius/2
  self.coil_z=.330+index*.014;self.straight_z=self.coil_z-self.entry[2]-self.entry_radius;self.guide_inset=.020
  self.guide_t=np.linspace(0,1,2049);guide_points=self.guide(self.guide_t);self.guide_s=np.r_[0,np.cumsum(np.linalg.norm(np.diff(guide_points,axis=0),axis=1))];self.straight_length=float(self.guide_s[-1])
  self.guide_length=self.turn_length+self.bend_length+self.straight_length
  self.coil_entry=self.turn_end+self.outward*self.entry_radius+self.back*(self.coil_z-self.entry[2])
  self.r0=.030;self.pitch=.0062;self.spiral_b=self.pitch/math.tau
  theta=np.linspace(0,100,20001);radius=self.r0+self.spiral_b*theta
  self.spiral_theta=theta;self.spiral_r=radius
  self.spiral_s=np.r_[0,np.cumsum(np.sqrt((radius[1:]**2+self.spiral_b**2)))*float(theta[1]-theta[0])]
  self.starter_length=.12;self.leader_length=self.guide_length+self.starter_length;self.total_length=self.leader_length+self.length
  self.material_s=np.linspace(0,self.total_length,rows+1)
  self.material_t=np.interp(self.material_s-self.leader_length,self.front_s,self.front_t)
  self.material_width=np.where(self.material_s<self.leader_length,.035*(self.left-self.right),(.035+.965*np.sin(math.pi*self.material_t))*(self.left-self.right))
  self.open_travel=self.length+.045
  self.steering_length=.32 if index==2 else .20
 def front(self,t):
  return self.A[None,:]+(self.D-self.A)[None,:]*t[:,None]+self.side[None,:]*self.mid*(.035+.965*np.sin(math.pi*t))[:,None]
 def front_derivative(self,t):
  return (self.D-self.A)[None,:]+self.side[None,:]*self.mid*.965*math.pi*np.cos(math.pi*t)[:,None]
 def turn(self,t):
  t=t[:,None];p=self.turn_controls;return (1-t)**3*p[0]+3*(1-t)**2*t*p[1]+3*(1-t)*t*t*p[2]+t**3*p[3]
 def turn_derivative(self,t):
  t=t[:,None];p=self.turn_controls;return 3*(1-t)**2*(p[1]-p[0])+6*(1-t)*t*(p[2]-p[1])+3*t*t*(p[3]-p[2])
 def guide(self,t):
  return self.turn_end+self.outward*self.entry_radius+self.back[None,:]*(self.entry_radius+self.straight_z*t)[:,None]-self.outward[None,:]*(self.guide_inset*np.sin(math.pi*t)**2)[:,None]
 def guide_derivative(self,t):
  return self.back[None,:]*self.straight_z-self.outward[None,:]*(self.guide_inset*math.pi*np.sin(2*math.pi*t))[:,None]
 def frames(self,amount):
  feed=self.leader_length+self.open_travel*amount;q=self.material_s-feed;a=-q
  pos=np.zeros((len(q),3));tangent=np.zeros_like(pos);width=np.zeros_like(pos)
  visible=q>=0;tt=np.interp(q[visible],self.front_s,self.front_t)
  steering=float(smooth(amount/.08));k=(steering*smooth(1-q[visible]/self.steering_length))[:,None]
  pos[visible]=self.front(tt);tangent[visible]=normalize(self.front_derivative(tt));width[visible]=normalize(self.side*(1-k)+self.roll_side*k)
  entry_width=normalize(self.side*(1-steering)+self.roll_side*steering)
  turn=(q<0)&(a<=self.turn_length);tt=np.interp(a[turn],self.turn_s,self.turn_t);pos[turn]=self.turn(tt);tangent[turn]=-normalize(self.turn_derivative(tt));k=smooth(tt)[:,None];width[turn]=normalize(entry_width*(1-k)+self.roll_side*k)
  bend=(a>self.turn_length)&(a<=self.turn_length+self.bend_length);theta=(a[bend]-self.turn_length)/self.entry_radius
  pos[bend]=self.turn_end+self.outward[None,:]*(self.entry_radius*np.sin(theta))[:,None]+self.back[None,:]*(self.entry_radius*(1-np.cos(theta)))[:,None]
  tangent[bend]=-self.outward[None,:]*np.cos(theta)[:,None]-self.back[None,:]*np.sin(theta)[:,None]
  width[bend]=self.roll_side
  straight=(a>self.turn_length+self.bend_length)&(a<=self.guide_length)
  tt=np.interp(a[straight]-self.turn_length-self.bend_length,self.guide_s,self.guide_t);pos[straight]=self.guide(tt)
  tangent[straight]=-normalize(self.guide_derivative(tt));width[straight]=self.roll_side
  wound=a>self.guide_length;stored=max(0,feed-self.guide_length)
  outer_theta=float(np.interp(stored,self.spiral_s,self.spiral_theta));outer_radius=float(np.interp(stored,self.spiral_s,self.spiral_r))
  coil_axis=self.coil_entry-self.outward*outer_radius
  ms=self.material_s[wound];theta=outer_theta-np.interp(ms,self.spiral_s,self.spiral_theta);rr=np.interp(ms,self.spiral_s,self.spiral_r)
  pos[wound]=coil_axis+self.outward[None,:]*(rr*np.cos(theta))[:,None]+self.back[None,:]*(rr*np.sin(theta))[:,None]
  tangent[wound]=normalize(self.outward[None,:]*(self.spiral_b*np.cos(theta)+rr*np.sin(theta))[:,None]+self.back[None,:]*(self.spiral_b*np.sin(theta)-rr*np.cos(theta))[:,None])
  width[wound]=self.roll_side
  normal=normalize(np.cross(tangent,width))
  return pos,width,normal,q,{'axis':coil_axis.tolist(),'outer_radius':outer_radius,'angle':outer_theta,'stored_length':stored,'feed':feed}
 def vertices(self,amount,skin=0):
  center,wide,normal,q,state=self.frames(amount);w=np.linspace(0,1,self.columns+1)
  bow=self.profile_height(q)
  # Two actual retained foils; both flatten in the guide and maintain the winding pitch.
  offsets=skin*.0036+bow[:,None]*np.sin(math.pi*w)[None,:]
  surface=center[:,None,:]+wide[:,None,:]*self.material_width[:,None,None]*(.5-w)[None,:,None]+normal[:,None,:]*offsets[:,:,None]
  return np.concatenate([(surface+normal[:,None,:]*thick).reshape(-1,3) for thick in [-.00075,.00075]]),state
 def profile_height(self,q):
  # The throat former always flattens the cross section continuously before the bend.
  return -.026*np.sin(math.pi*self.material_t)*smooth(q/.18)
 def topology(self):
  nv=self.columns;nu=self.rows;stride=(nu+1)*(nv+1);faces=[]
  for j in range(nu):
   for k in range(nv):
    v=j*(nv+1)+k;quad=(v,v+1,v+nv+2,v+nv+1);faces.extend([quad[::-1],tuple(x+stride for x in quad)])
  boundary=list(range(nv+1))+[j*(nv+1)+nv for j in range(1,nu+1)]+[nu*(nv+1)+k for k in range(nv-1,-1,-1)]+[j*(nv+1) for j in range(nu-1,0,-1)]
  for j,a in enumerate(boundary):
   b=boundary[(j+1)%len(boundary)];faces.append((a,b,b+stride,a+stride))
  return faces
