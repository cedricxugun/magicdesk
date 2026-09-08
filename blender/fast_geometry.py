# Data API primitive construction avoids dependency-graph evaluation on every screw.
GEOMETRY_CACHE={}
def fast_instance(name,verts,faces,key,parent,loc,rot=None,smooth_faces=None,uv=None,cache=None):
 if cache in GEOMETRY_CACHE:
  me=GEOMETRY_CACHE[cache]
 else:
  me=bpy.data.meshes.new(name+'_Mesh');me.from_pydata(verts,[],faces);me.materials.append(M[key])
  if smooth_faces is not None:
   for i,p in enumerate(me.polygons):p.use_smooth=smooth_faces if isinstance(smooth_faces,bool) else smooth_faces[i]
  if uv is not None:
   layer=me.uv_layers.new(name='MachiningUV')
   for po in me.polygons:
    for li in po.loop_indices:layer.data[li].uv=uv[me.loops[li].vertex_index]
  if cache is not None:GEOMETRY_CACHE[cache]=me
 o=bpy.data.objects.new(name,me);COL.objects.link(o);o.parent=parent;o.location=loc
 if rot is not None:
  if isinstance(rot,Quaternion):o.rotation_mode='QUATERNION';o.rotation_quaternion=rot
  else:o.rotation_euler=rot
 return o

def cyl(name,r,depth,key,parent=None,loc=(0,0,0),rot=None,n=48):
 ck=('cyl',round(r,6),round(depth,6),key,n)
 if ck in GEOMETRY_CACHE:return fast_instance(name,[],[],key,parent,loc,rot,cache=ck)
 be=min(.004,r*.12,depth*.16);profile=[(r-be,-depth/2),(r,-depth/2+be),(r,depth/2-be),(r-be,depth/2)]
 verts=[];uv=[]
 for rr,z in profile:
  for k in range(n):
   a=k*math.tau/n;verts.append((rr*math.cos(a),rr*math.sin(a),z));uv.append((k/n,z/max(.0001,depth)+.5))
 faces=[]
 for j in range(3):
  for k in range(n):faces.append((j*n+k,j*n+(k+1)%n,(j+1)*n+(k+1)%n,(j+1)*n+k))
 faces += [tuple(range(n-1,-1,-1)),tuple(range(3*n,4*n))]
 smooth=[n>12]*(n*3)+[False,False]
 return fast_instance(name,verts,faces,key,parent,loc,rot,smooth,uv,ck)

def cube(name,dim,key,parent=None,loc=(0,0,0),bevel=.02,rot=None):
 x,y,z=[v/2 for v in dim];verts=[(-x,-y,-z),(-x,-y,z),(-x,y,-z),(-x,y,z),(x,-y,-z),(x,-y,z),(x,y,-z),(x,y,z)]
 faces=[(2,6,4,0),(5,7,3,1),(4,5,1,0),(3,7,6,2),(1,3,2,0),(6,7,5,4)]
 o=fast_instance(name,verts,faces,key,parent,loc,rot,False)
 if bevel:
  mo=o.modifiers.new('Manufactured radius','BEVEL');mo.width=min(bevel,min(dim)*.4);mo.segments=3
  no=o.modifiers.new('Face weighted normals','WEIGHTED_NORMAL');no.keep_sharp=True
 return o

def sphere(name,r,key,parent=None,loc=(0,0,0),scale=None):
 N=24;J=12;s=scale or (1,1,1);ck=('sphere',r,key,tuple(s));verts=[];uv=[]
 if ck in GEOMETRY_CACHE:return fast_instance(name,[],[],key,parent,loc,cache=ck)
 for j in range(J+1):
  th=math.pi*j/J
  for k in range(N):
   a=math.tau*k/N;verts.append((r*math.sin(th)*math.cos(a)*s[0],r*math.sin(th)*math.sin(a)*s[1],r*math.cos(th)*s[2]));uv.append((k/N,j/J))
 faces=[((j+1)*N+k,(j+1)*N+(k+1)%N,j*N+(k+1)%N,j*N+k) for j in range(J) for k in range(N)]
 return fast_instance(name,verts,faces,key,parent,loc,smooth_faces=True,uv=uv,cache=ck)

def torus(name,r,t,key,parent=None,loc=(0,0,0),rot=None):
 N=96;J=10;ck=('torus',r,t,key)
 if ck in GEOMETRY_CACHE:return fast_instance(name,[],[],key,parent,loc,rot,cache=ck)
 verts=[];uv=[]
 for i in range(N):
  a=math.tau*i/N
  for j in range(J):
   b=math.tau*j/J;rr=r+t*math.cos(b);verts.append((rr*math.cos(a),rr*math.sin(a),t*math.sin(b)));uv.append((i/N,j/J))
 faces=[(i*J+j,((i+1)%N)*J+j,((i+1)%N)*J+(j+1)%J,i*J+(j+1)%J) for i in range(N) for j in range(J)]
 return fast_instance(name,verts,faces,key,parent,loc,rot,True,uv,ck)
