"""Formed support bodies, fitted feet and curved port lips; configured by the builder."""
import bpy,bmesh,math
from mathutils import Vector,Matrix
import i_machined_geometry as h
import i_fitted_surface as fitted

root=None
def configure(collection,parent):
    global root
    root=parent;h.configure(collection)

def own(name,points,faces,parent,material='A_Satin'):
    data=bpy.data.meshes.new(name+'Mesh');data.from_pydata(points,[],faces);data.update();o=bpy.data.objects.new(name,data);h.col.objects.link(o);h.finish(o,name,parent,(0,0,0),material)
    bm=bmesh.new();bm.from_mesh(data)
    if bm.calc_volume(signed=True)<0:bmesh.ops.reverse_faces(bm,faces=list(bm.faces));bm.to_mesh(data)
    assert not any(not e.is_manifold for e in bm.edges),(name,'Source formed solid is open');bm.free();return o

def boolean(target,tool,operation='UNION'):
    bpy.context.view_layer.update();bpy.context.view_layer.objects.active=target;mod=target.modifiers.new('Physical '+operation,'BOOLEAN');mod.operation=operation;mod.solver='EXACT';mod.object=tool;bpy.ops.object.modifier_apply(modifier=mod.name)
    if tool.name in h.parts:h.parts.remove(tool.name)
    bpy.data.objects.remove(tool,do_unlink=True)

def profile_body(name,top,foot,axis):
    direction=(foot-top).normalized();length=(foot-top).length;u=axis.normalized();v=direction.cross(u).normalized();n=64
    stations=[(.0105,.0098),(.036,.0098),(.050,.0125),(.068,.0225),(.080,.0275),(.088,.0278),(length-.082,.0278),(length-.050,.016),(length-.040,.0148),(length-.015,.0148)]
    def envelope(t):
        radii=[]
        if .0105<=t<=.038:radii.append(.0098)
        if .038<=t<=.080:radii.append(.0098+(.028-.0098)*(t-.038)/.042)
        if .078<=t<=length-.046:radii.append(.028)
        if length-.062<=t<=length-.013:radii.append(.028+(.015-.028)*(t-(length-.062))/.049)
        return max(radii)
    rings=[]
    for i,((a,ra),(b,rb)) in enumerate(zip(stations,stations[1:])):
        for j in range(7):
            if i and j==0:continue
            t=j/6;distance=a+(b-a)*t;radius=min(ra+(rb-ra)*t*t*(3-2*t),envelope(distance)-.0002);rings.append((distance,radius))
    points=[];faces=[]
    for distance,r in rings:points.extend(top+direction*distance+(u*math.cos(k*math.tau/n)+v*math.sin(k*math.tau/n))*r for k in range(n))
    for j in range(len(rings)-1):faces.extend((j*n+k,j*n+(k+1)%n,(j+1)*n+(k+1)%n,(j+1)*n+k) for k in range(n))
    side_count=len(faces);faces.extend([tuple(range(n-1,-1,-1)),tuple((len(rings)-1)*n+k for k in range(n))]);o=own(name,points,faces,root,'A_Nickel')
    for f in o.data.polygons:f.use_smooth=f.index<side_count
    uv=o.data.uv_layers.new(name='FormedMetalGrain')
    for f in o.data.polygons:
        for li in f.loop_indices:
            vi=o.data.loops[li].vertex_index;uv.data[li].uv=((vi%n)/n,rings[vi//n][0]/length)
    return o

def foot_frame(name,foot,axis,deck_top,deck_center):
    radial=Vector((foot.x-deck_center.x,foot.y-deck_center.y,0)).normalized();tangent=Vector((-radial.y,radial.x,0));frame=h.empty(name,root);matrix=Matrix((radial,tangent,Vector((0,0,1)))).transposed().to_4x4();matrix.translation=Vector((foot.x,foot.y,deck_top));frame.matrix_world=matrix;return frame,radial,tangent

def formed_foot(name,source_deck,frame):
    outline=[(.038*math.cos(k*math.tau/64),.068*math.sin(k*math.tau/64)) for k in range(64)];points,polys,boundary=fitted.clipped_surface([source_deck],outline,frame=frame.matrix_world,from_positive=True,normal_limit=.1)
    adjacency={}
    for a,b in boundary:adjacency.setdefault(a,[]).append(b);adjacency.setdefault(b,[]).append(a)
    assert all(len(v)==2 for v in adjacency.values());start=min(adjacency);loop=[start];previous=None;current=start
    while True:
        nxt=next(v for v in adjacency[current] if v!=previous)
        if nxt==start:break
        assert nxt not in loop;loop.append(nxt);previous,current=current,nxt
    assert len(loop)==len(adjacency)
    if sum(points[a].x*points[loop[(i+1)%len(loop)]].y-points[a].y*points[loop[(i+1)%len(loop)]].x for i,a in enumerate(loop))<0:loop.reverse()
    vs=[tuple(p+Vector((0,0,.0012))) for p in points];fs=[tuple(reversed(p)) for p in polys];previous_ring=loop;top=.0182;radius=.001
    for angle in [0.,math.pi/6,math.pi/3,math.pi/2]:
        ring=[]
        for index in loop:
            p=points[index];normal=Vector((p.x/.038**2,p.y/.068**2,0)).normalized();inset=radius*(1-math.cos(angle));ring.append(len(vs));vs.append((p.x-normal.x*inset,p.y-normal.y*inset,top-radius+radius*math.sin(angle)))
        for i,a in enumerate(previous_ring):fs.append((a,previous_ring[(i+1)%len(loop)],ring[(i+1)%len(loop)],ring[i]))
        previous_ring=ring
    fs.append(tuple(previous_ring));foot=own(name,vs,fs,frame)
    for f in foot.data.polygons:f.use_smooth=len(polys)<=f.index<len(foot.data.polygons)-1
    outline=[(.0373*math.cos(k*math.tau/64),.0673*math.sin(k*math.tau/64)) for k in range(64)];patch=fitted.clipped_surface([source_deck],outline,frame=frame.matrix_world,from_positive=True,normal_limit=.1);v,f=fitted.extruded_patch(*patch,top_offset=.0011,bottom_offset=.0001);gasket=own(name+'_Gasket',v,f,frame,'A_Rubber')
    return foot,gasket

def foot_fork(name,foot,axis,plate_top):
    up=(Vector((0,0,1))-axis*axis.z).normalized();side=axis.cross(up).normalized();height=foot.z-(plate_top-.003);origin=foot-up*height;frame=h.empty(name+'_Frame',root);matrix=Matrix((up,side,axis)).transposed().to_4x4();matrix.translation=origin;frame.matrix_world=matrix;objects=[]
    outline=[(0.,-.020),(height,-.022)]
    for k in range(1,25):
        a=-math.pi/2+k*math.pi/24;outline.append((height+.022*math.cos(a),.022*math.sin(a)))
    outline.append((0.,.020));count=len(outline)
    for sign in [-1,1]:
        offset=sign*.019;v=[(x,y,offset+z) for z in [-.003,.003] for x,y in outline];f=[tuple(range(count-1,-1,-1)),tuple(range(count,2*count))]+[(i,(i+1)%count,(i+1)%count+count,i+count) for i in range(count)];o=own(name+'_Cheek_'+str(sign),v,f,frame);h.drill(o,.00625,.030,frame,(height,0,offset));objects.append(o)
    return frame,objects

def formed_port_lip(name,skins,frame,radius=.041):
    outline=[(radius*math.cos(k*math.tau/64),radius*math.sin(k*math.tau/64)) for k in range(64)];segments=[];fits=[]
    for i,skin in enumerate(skins):
        patch=fitted.clipped_surface([skin],outline,frame=frame.matrix_world,from_positive=True,normal_limit=.1,allow_partial=True,strict_visible_triangle=True)
        points,polys,edges=patch;area=sum(abs(sum(points[a].x*points[p[(k+1)%len(p)]].y-points[a].y*points[p[(k+1)%len(p)]].x for k,a in enumerate(p)))/2 for p in polys);ratio=area/(math.pi*radius*radius)
        v,f=fitted.extruded_patch(*patch,top_offset=.0042,bottom_offset=.0002);segments.append(own(name+'_Layer%d'%i,v,f,frame));fits.append({'skin':skin.name,'footprint_ratio':ratio,'source_surface_range':[min(p.z for p in points),max(p.z for p in points)]})
    lip=segments[0]
    for segment in segments[1:]:boolean(lip,segment)
    # Separate source layers can overlap in projection. Union their formed
    # skirts, relieve against both actual skins, then leave a small axial gap.
    for skin in skins:
        tool=skin.copy();tool.data=skin.data.copy();h.col.objects.link(tool);tool.name='PortSkinReliefTool';boolean(lip,tool,'DIFFERENCE')
    for vertex in lip.data.vertices:vertex.co.z+=.0001
    h.drill(lip,.0305,1.,frame,(0,0,.15));lip.data.materials.clear();lip.data.materials.append(bpy.data.materials['Collection_A_Satin'])
    for face in lip.data.polygons:face.material_index=0
    bm=bmesh.new();bm.from_mesh(lip.data);bm.normal_update()
    for face in bm.faces:face.smooth=True
    for edge in bm.edges:edge.smooth=len(edge.link_faces)==2 and edge.calc_face_angle()<math.radians(55)
    bm.to_mesh(lip.data);bm.free();return lip,{'source_layers':fits,'formed_outer_offset':.0042,'source_gap':.0002,'post_relief_axial_gap':.0001}
