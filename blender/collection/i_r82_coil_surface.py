"""Shared analytic coiled surface, without any Blender scene mutation."""
import math
from mathutils import Vector
class CoilSurface:
 def __init__(self,parameters):
  self.p=parameters;self.T=parameters['T'];self.shift=Vector(parameters['SHIFT'])
 def frame(self,t):
  p=self.p;r=p['RMAX']*math.exp(p['GROW']*(t-self.T));a=p['END']+t-self.T
  n=Vector((math.cos(a),0,math.sin(a)));u=max(0.,(t-(self.T-1.25))/1.25)
  tangent=Vector((r*(p['GROW']*math.cos(a)-math.sin(a)),-.44*3*u*u/1.25,r*(p['GROW']*math.sin(a)+math.cos(a)))).normalized()
  radial=(n-tangent*n.dot(tangent)).normalized()
  return r,radial,tangent,self.shift+n*r+Vector((0,-.44*u**3,0))
 @staticmethod
 def smooth_min(a,b,k):return min(a,b)-max(k-abs(a-b),0.)**2/(4*k)
 def wall(self,t):
  r,_,_,_=self.frame(t);small=min(self.p['RAD'],self.p['DEPTH'])*r
  inset=self.smooth_min(.042,small-.004,.003);thick=self.smooth_min(.012,(small-inset)*.42,.001)
  return inset,thick
 def point(self,t,u,inset=None):
  r,n,a,c=self.frame(t)
  if inset is None:inset=self.wall(t)[0]
  return c+n*((self.p['RAD']*r-inset)*math.cos(u))+n.cross(a).normalized()*((self.p['DEPTH']*r-inset)*math.sin(u))
 def normal(self,t,u):
  h=.0001;dt=self.point(t+h,u)-self.point(t-h,u);du=self.point(t,u+h)-self.point(t,u-h)
  v=dt.cross(du).normalized();_,_,_,c=self.frame(t)
  return v if v.dot(self.point(t,u)-c)>0 else -v
