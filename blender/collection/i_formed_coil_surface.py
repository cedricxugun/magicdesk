"""R86/R89 formed gold surface, without modifying a Blender scene."""
import math
from i_r82_coil_surface import CoilSurface
class FormedCoilSurface:
 def __init__(self,parameters,mouth_inverse,return_spec):
  self.base=CoilSurface(parameters);self.T=self.base.T;self.mouth_inverse=mouth_inverse;self.return_spec=return_spec
 def frame(self,t):return self.base.frame(t)
 def wall(self,t):return self.base.wall(t)
 @staticmethod
 def smooth(a,b,x):
  x=max(0.,min(1.,(x-a)/(b-a)));return x*x*(3-2*x)
 def point(self,t,u,inset=None):
  p=self.base.point(t,u,inset)
  if self.return_spec and t>self.T-.7:
   local=self.mouth_inverse@self.base.point(t,u);angle=math.atan2(local.y,local.x);aa,ab,ac,ad=self.return_spec['angle'];za,zb,zc,zd=self.return_spec['depth']
   w=self.smooth(aa,ab,angle)*(1-self.smooth(ac,ad,angle))*self.smooth(za,zb,local.z)*(1-self.smooth(zc,zd,local.z))
   p+=self.base.normal(t,u)*(self.return_spec['maximum_normal_shift']*w)
  return p
 def normal(self,t,u):
  h=.0001;dt=self.point(t+h,u)-self.point(t-h,u);du=self.point(t,u+h)-self.point(t,u-h);n=dt.cross(du).normalized()
  return n if n.dot(self.point(t,u)-self.frame(t)[3])>0 else -n
