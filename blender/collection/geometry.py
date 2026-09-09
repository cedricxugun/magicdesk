"""Blender-authored collection assets. Positions use Blender Z-up.

Runtime pose metadata is converted to glTF/Godot Y-up. No original HELIOS
source file is executed or overwritten; only its primitive utility is reused.
"""
import bpy
import bmesh
import math
import json
from pathlib import Path
from mathutils import Vector, Matrix, Quaternion

ROOT = Path(__file__).resolve().parents[2]
ASSETS = ROOT / 'app/assets'
C = Matrix(((1,0,0,0),(0,0,1,0),(0,-1,0,0),(0,0,0,1)))

def smooth(t):
    t=max(0.,min(1.,t));return t*t*(3.-2.*t)

def window(t,a,b):return smooth((t-a)/max(.00001,b-a))

def pose(matrix):
    p,q,s=(C @ matrix @ C.inverted()).decompose()
    return {'p':list(p),'q':[q.x,q.y,q.z,q.w],'s':list(s)}

class Builder:
    def __init__(self, ident, title):
        bpy.ops.wm.read_factory_settings(use_empty=True)
        self.id=ident;self.title=title;self.scene=bpy.context.scene
        self.scene.unit_settings.system='METRIC';self.scene.render.fps=24
        self.col=bpy.data.collections.new('MODULE_'+ident);self.scene.collection.children.link(self.col)
        self.parts=[];self.controls=[];self.motions=[];self.sockets={};self.qa_shells=[];self.extra={}
        self.mats={};self.serial=0
        self.material('Ivory',(.83,.78,.68),0,.24,albedo='ceramic_ivory_albedo.png',rough='ceramic_glaze_roughness.png',normal='ceramic_glaze_normal.png',coat=.4)
        self.material('Chrome',(.62,.58,.50),.96,.24,albedo='nickel_albedo.png',rough='metal_roughness.png',normal='metal_normal.png')
        self.material('Steel',(.22,.22,.20),.9,.34,albedo='steel_albedo.png',rough='metal_roughness.png',normal='metal_normal.png')
        self.material('Black',(.045,.045,.04),.55,.32)
        self.material('Red',(.32,.025,.015),.18,.22,coat=.4)
        self.material('Copper',(.40,.16,.06),.94,.23)
        self.material('Glow',(1,.16,.035),.1,.25,emission=1.2)
        self.material('Lens',(.015,.025,.022),.72,.1,coat=.6)
        self.material('Glass',(.6,.68,.66),0,.08,transmission=.65)
        namespace={'bpy':bpy,'math':math,'Vector':Vector,'Matrix':Matrix,'Quaternion':Quaternion,'COL':self.col,'M':self.mats}
        exec(compile((ROOT/'blender/fast_geometry.py').read_text(),str(ROOT/'blender/fast_geometry.py'),'exec'),namespace)
        self.fast=namespace
        self.root=self.empty(ident+'_MODULE')
        self.upper=self.empty(ident+'_UPPER',self.root)

    def material(self,name,color,metal,roughness,albedo=None,rough=None,normal=None,coat=0,emission=0,transmission=0):
        m=bpy.data.materials.new('Collection_'+name);m.use_nodes=True
        p=m.node_tree.nodes.get('Principled BSDF')
        p.inputs['Base Color'].default_value=(*color,1);p.inputs['Metallic'].default_value=metal
        p.inputs['Roughness'].default_value=roughness
        p.inputs['Coat Weight'].default_value=coat;p.inputs['Coat Roughness'].default_value=.12
        if emission:p.inputs['Emission Color'].default_value=(*color,1);p.inputs['Emission Strength'].default_value=emission
        if transmission:p.inputs['Transmission Weight'].default_value=transmission
        if albedo:
            t=m.node_tree.nodes.new('ShaderNodeTexImage');t.image=bpy.data.images.load(str(ASSETS/albedo),check_existing=True)
            m.node_tree.links.new(t.outputs['Color'],p.inputs['Base Color'])
        if rough:
            t=m.node_tree.nodes.new('ShaderNodeTexImage');t.image=bpy.data.images.load(str(ASSETS/rough),check_existing=True);t.image.colorspace_settings.name='Non-Color'
            m.node_tree.links.new(t.outputs['Color'],p.inputs['Roughness'])
        if normal:
            t=m.node_tree.nodes.new('ShaderNodeTexImage');t.image=bpy.data.images.load(str(ASSETS/normal),check_existing=True);t.image.colorspace_settings.name='Non-Color'
            n=m.node_tree.nodes.new('ShaderNodeNormalMap');n.inputs['Strength'].default_value=.13
            m.node_tree.links.new(t.outputs['Color'],n.inputs['Color']);m.node_tree.links.new(n.outputs['Normal'],p.inputs['Normal'])
        self.mats[name]=m;return m

    def name(self,n):self.serial+=1;return '%s_%s_%04d'%(self.id,n,self.serial)

    def empty(self,name,parent=None,loc=(0,0,0)):
        o=bpy.data.objects.new(name,None);self.col.objects.link(o);o.parent=parent;o.location=loc;return o

    def part(self,name,offset=(0,0,.4),stage=.1,parent=None):
        o=self.empty(self.id+'_P_'+name,parent or self.upper)
        self.parts.append({'obj':o,'offset':list((C@Vector(offset).to_4d()).xyz),'stage':stage})
        return o

    def extraction_route(self,node,knots):
        for part in self.parts:
            if part['obj']==node:
                part['route']=[{'at':at,'offset':list((C@Vector(offset).to_4d()).xyz)} for at,offset in knots]
                return

    def extraction_offset(self,part,amount):
        if 'route' in part:
            knots=part['route']
            for first,last in zip(knots,knots[1:]):
                if amount<=last['at']:
                    return Vector(first['offset']).lerp(Vector(last['offset']),window(amount,first['at'],last['at']))
            return Vector(knots[-1]['offset'])
        return Vector(part['offset'])*window(amount,part['stage']*.25,1)

    def control(self,name,parent,fn):
        o=self.empty(self.id+'_C_'+name,parent);self.controls.append((o,fn));fn(o,0.);return o

    def rotor(self,name,parent,axis='z',speed=.5,amplitude=0,phase=0):
        o=self.empty(self.id+'_R_'+name,parent)
        self.motions.append({'name':o.name,'axis':{'x':'x','y':'z','z':'y'}[axis],'speed':speed*(-1 if axis=='y' else 1),'amplitude':amplitude,'phase':phase})
        return o

    def socket(self,name,parent,loc):
        o=self.empty(self.id+'_S_'+name,parent,loc);self.sockets[name]=o.name;return o

    def cube(self,name,dim,key='Ivory',parent=None,loc=(0,0,0),bevel=.025,rot=None):
        obj=self.fast['cube'](self.name(name),dim,key,parent or self.upper,loc,bevel,rot)
        layer=obj.data.uv_layers.new(name='ManufacturedUV')
        for face in obj.data.polygons:
            normal=face.normal
            axes=[k for k in range(3) if k!=max(range(3),key=lambda a:abs(normal[a]))]
            for li in face.loop_indices:
                vertex=obj.data.vertices[obj.data.loops[li].vertex_index].co
                layer.data[li].uv=(vertex[axes[0]]/max(.001,dim[axes[0]])+.5,vertex[axes[1]]/max(.001,dim[axes[1]])+.5)
        if key=='Ivory':self.qa_shells.append(obj.name)
        return obj

    def cyl(self,name,r,depth,key='Chrome',parent=None,loc=(0,0,0),rot=None,n=48):
        return self.fast['cyl'](self.name(name),r,depth,key,parent or self.upper,loc,rot,n)

    def sphere(self,name,r,key='Chrome',parent=None,loc=(0,0,0),scale=None):
        # Close-up silhouettes and a duplicated longitude seam for stable UVs.
        n=64;jmax=32;s=scale or (1,1,1);verts=[];uv=[];faces=[]
        for j in range(jmax+1):
            theta=math.pi*j/jmax
            for k in range(n+1):
                angle=k*math.tau/n
                verts.append((r*math.sin(theta)*math.cos(angle)*s[0],r*math.sin(theta)*math.sin(angle)*s[1],r*math.cos(theta)*s[2]))
                uv.append((k/n,1-j/jmax))
        for j in range(jmax):
            for k in range(n):
                a=j*(n+1)+k;faces.append((a,a+1,a+n+2,a+n+1))
        obj=self.fast['fast_instance'](self.name(name),verts,faces,key,parent or self.upper,loc,smooth_faces=True,uv=uv)
        if key=='Ivory':self.qa_shells.append(obj.name)
        return obj

    def sleeve(self,name,r,inside,depth,key='Steel',parent=None,loc=(0,0,0),n=64):
        verts=[];faces=[];uv=[]
        for radius,z in [(r,-depth/2),(r,depth/2),(inside,depth/2),(inside,-depth/2)]:
            for k in range(n):
                a=k*math.tau/n;verts.append((radius*math.cos(a),radius*math.sin(a),z));uv.append((k/n,z/depth+.5))
        for band in range(4):
            for k in range(n):faces.append((band*n+k,band*n+(k+1)%n,((band+1)%4)*n+(k+1)%n,((band+1)%4)*n+k))
        obj=self.fast['fast_instance'](self.name(name),verts,faces,key,parent or self.upper,loc,smooth_faces=[j//n in [0,2] for j in range(n*4)],uv=uv)
        bevel=obj.modifiers.new('Machined bore rims','BEVEL');bevel.width=.003;bevel.segments=2
        if key=='Ivory':self.qa_shells.append(obj.name)
        return obj

    def torus(self,name,r,t,key='Chrome',parent=None,loc=(0,0,0),rot=None):
        return self.fast['torus'](self.name(name),r,t,key,parent or self.upper,loc,rot)

    def tube(self,name,points,r,key='Chrome',parent=None,resolution=2):
        d=bpy.data.curves.new(self.name(name),'CURVE');d.dimensions='3D';d.resolution_u=2;d.bevel_depth=r;d.bevel_resolution=resolution
        s=d.splines.new('POLY');s.points.add(len(points)-1)
        for p,v in zip(s.points,points):p.co=(*v,1)
        o=bpy.data.objects.new(d.name,d);self.col.objects.link(o);o.parent=parent or self.upper;d.materials.append(self.mats[key]);return o

    def beam(self,name,a,b,r,key='Chrome',parent=None):
        a=Vector(a);b=Vector(b);v=b-a
        return self.cyl(name,r,v.length,key,parent,(a+b)*.5,v.to_track_quat('Z','Y'),24)

    def screw(self,parent,p,axis=(0,0,1),r=.016):
        q=Vector(axis).to_track_quat('Z','Y')
        self.cyl('Screw',r,.013,'Chrome',parent,p,q,12)
        o=self.cube('ScrewSlot',(r*1.2,r*.16,.002),'Black',parent,p,.001,q)
        o.location+=Vector(axis)*.007

    def joint(self,parent,p,r=.075,axis=(0,1,0)):
        q=Vector(axis).to_track_quat('Z','Y')
        self.cyl('Joint',r,r*.9,'Steel',parent,p,q)
        self.cyl('Bearing',r*.77,r*.96,'Chrome',parent,p,q)
        self.cyl('RedPin',r*.35,r,'Red',parent,p,q,24)

    def coil(self,parent,center,r=.065,height=.25,turns=12,axis=(0,0,1)):
        q=Vector(axis).to_track_quat('Z','Y');pts=[]
        for i in range(turns*16+1):
            t=i/(turns*16);a=t*turns*math.tau
            pts.append(Vector(center)+q@Vector((r*math.cos(a),r*math.sin(a),height*(t-.5))))
        self.tube('Coil',pts,.006,'Copper',parent,1)

    def ribbon(self,name,points,widths,depth=.025,key='Ivory',parent=None):
        # Closed elliptical section swept along a planar/3D backbone.
        points=[Vector(p) for p in points];verts=[];faces=[];uv=[];sides=12
        for i,p in enumerate(points):
            tangent=(points[min(i+1,len(points)-1)]-points[max(i-1,0)]).normalized()
            guide=Vector((0,1,0))
            if abs(tangent.dot(guide))>.95:guide=Vector((1,0,0))
            side=tangent.cross(guide).normalized();normal=side.cross(tangent).normalized()
            width=widths[i] if isinstance(widths,list) else widths
            thick=depth[i] if isinstance(depth,list) else depth
            for j in range(sides):
                a=j*math.tau/sides;verts.append(p+side*math.cos(a)*width+normal*math.sin(a)*thick);uv.append((j/sides,i/max(1,len(points)-1)))
        for i in range(len(points)-1):
            for j in range(sides):faces.append((i*sides+j,i*sides+(j+1)%sides,(i+1)*sides+(j+1)%sides,(i+1)*sides+j))
        faces.extend([tuple(range(sides-1,-1,-1)),tuple(range((len(points)-1)*sides,len(points)*sides))])
        o=self.fast['fast_instance'](self.name(name),verts,faces,key,parent or self.upper,(0,0,0),smooth_faces=True,uv=uv)
        bm=bmesh.new();bm.from_mesh(o.data);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(o.data);bm.free()
        if key=='Ivory':self.qa_shells.append(o.name)
        return o

    def panel(self,name,parent,width,height,thickness=.035,loc=(0,0,0)):
        o=self.cube(name,(width,thickness,height),'Ivory',parent,loc,min(.04,width*.08))
        if o.name not in self.qa_shells:self.qa_shells.append(o.name)
        for x in [-width*.40,width*.40]:
            for z in [-height*.43,height*.43]:self.screw(parent,Vector(loc)+Vector((x,-thickness*.52,z)),(0,-1,0),.011)
        return o

    def pedestal_mount(self,r=.33):
        p=self.part('Mount',(0,0,.08),.8)
        self.cyl('MountFoot',r+.08,.055,'Steel',p,(0,0,.615))
        self.cyl('Mount',r,.14,'Chrome',p,(0,0,.70))
        self.torus('MountRing',r,.015,'Copper',p,(0,0,.772))
        for i in range(12):
            a=i*math.tau/12;self.cube('MountSlot',(.025,.022,.075),'Black',p,(r*math.cos(a),r*math.sin(a),.70),.004,(0,0,a))
        return p

    def apply_pose(self,t):
        for o,fn in self.controls:fn(o,t)
        bpy.context.view_layer.update()

    def reference_scene(self):
        before=set(bpy.data.objects)
        bpy.ops.import_scene.gltf(filepath=str(ASSETS/'helios_model.glb'))
        added=set(bpy.data.objects)-before
        upper=next((o for o in added if o.name=='TURNTABLE'),None)
        retained=added-set(list(upper.children_recursive)+[upper]) if upper else added
        if upper:
            for o in list(upper.children_recursive)+[upper]:bpy.data.objects.remove(o,do_unlink=True)
        for o in retained:o.hide_select=True
        self.scene.render.engine='CYCLES';self.scene.cycles.samples=48;self.scene.cycles.use_denoising=True
        self.scene.render.resolution_x=1440;self.scene.render.resolution_y=1050;self.scene.render.resolution_percentage=100
        self.scene.render.film_transparent=True
        self.scene.world=bpy.data.worlds.new('Collection_Studio');w=self.scene.world;w.use_nodes=True
        t=w.node_tree.nodes.new('ShaderNodeTexEnvironment');t.image=bpy.data.images.load(str(ASSETS/'studio_small_09_4k.exr'),check_existing=True)
        w.node_tree.nodes.get('Background').inputs['Strength'].default_value=.35
        w.node_tree.links.new(t.outputs['Color'],w.node_tree.nodes.get('Background').inputs['Color'])
        for index,(pos,power,size) in enumerate([((-3,-4,5),450,4),((4,2,4),550,3),((0,-5,2.5),160,4)]):
            d=bpy.data.lights.new('Studio_'+str(index),'AREA');d.energy=power;d.shape='DISK';d.size=size
            o=bpy.data.objects.new(d.name,d);self.scene.collection.objects.link(o);o.location=pos;o.rotation_euler=(Vector((0,0,1.5))-o.location).to_track_quat('-Z','Y').to_euler()
        d=bpy.data.cameras.new('Shared_Camera');o=bpy.data.objects.new('Shared_Camera',d);self.scene.collection.objects.link(o)
        o.location=(.65,-7.65,3.95);o.rotation_euler=(Vector((0,0,1.92))-o.location).to_track_quat('-Z','Y').to_euler();d.sensor_fit='VERTICAL';d.sensor_height=24;d.lens=26
        self.scene.camera=o

    def export(self):
        out=ASSETS/'collection/models';out.mkdir(parents=True,exist_ok=True)
        calibration={'F':1.20,'G':1.12,'I':1.14,'J':1.0,'K':1.10,'L':1.23,'M':1.0,'N':1.25}.get(self.id,1.0)
        self.upper.scale=(calibration,calibration,calibration)
        self.upper.location.z=.615*(1-calibration)
        self.extra['display_calibration']={'scale':calibration,'fixed_mount_height':.615,'base_scaled':False}
        seen=set()
        for obj in self.col.all_objects:
            if obj.type!='MESH' or obj.data.as_pointer() in seen or obj.data.shape_keys:continue
            seen.add(obj.data.as_pointer())
            bm=bmesh.new();bm.from_mesh(obj.data)
            bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(obj.data);bm.free();obj.data.update()
        self.apply_pose(0)
        rest_locations={p['obj'].name:p['obj'].location.copy() for p in self.parts}
        samples={o.name:[] for o,_ in self.controls}
        for i in range(101):
            self.apply_pose(i/100)
            for o,_ in self.controls:samples[o.name].append(pose(o.matrix_basis))
        self.apply_pose(0)
        parts=[{'name':p['obj'].name,'home':pose(p['obj'].matrix_basis),'offset':p['offset'],'stage':p['stage'],**({'route':p['route']} if 'route' in p else {})} for p in self.parts]
        metadata={'id':self.id,'title':self.title,'root':self.root.name,'upper':self.upper.name,'parts':parts,
                  'controls':[{'name':name,'samples':values} for name,values in samples.items()],
                  'motions':self.motions,'sockets':self.sockets,'qa_shells':self.qa_shells,'part_count':len(parts),
                  'base_diameter':2.74,'includes_base':False,'source_blend':'blender/collection/'+self.id+'.blend'}
        metadata.update(self.extra)
        (out/(self.id+'.json')).write_text(json.dumps(metadata,separators=(',',':')))
        bpy.ops.object.select_all(action='DESELECT')
        for o in self.col.all_objects:o.select_set(True)
        bpy.context.view_layer.objects.active=self.root
        bpy.ops.export_scene.gltf(filepath=str(out/(self.id+'.glb')),export_format='GLB',use_selection=True,export_apply=True,export_animations=False,export_extras=True,export_yup=True)
        # Preserve a complete, editable demonstration timeline in the source.
        for frame in range(1,362,4):
            if frame<49:t=0.
            elif frame<121:t=smooth((frame-49)/72)
            elif frame<169:t=1.
            elif frame<211:t=1.-smooth((frame-169)/42)
            else:t=0.
            self.apply_pose(t)
            for motion in self.motions:
                node=bpy.data.objects[motion['name']]
                value=frame/24*motion['speed']+motion['phase']
                if motion['amplitude']>0:value=math.sin(value)*motion['amplitude']
                axis={'x':0,'y':2,'z':1}[motion['axis']]
                node.rotation_euler[axis]=value*(-1 if motion['axis']=='z' else 1)
                node.keyframe_insert('rotation_euler',frame=frame)
            if self.id=='K':
                for index in range(3):
                    node=bpy.data.objects.get('K_C_StylusLift'+str(index))
                    if node:node.location.z-=.055*max(0,math.sin(frame/24*4+index*math.tau/3))*t
            explosion=window(frame,213,261)*(1-window(frame,293,337))
            for p in self.parts:
                offset=C.inverted()@self.extraction_offset(p,explosion).to_4d()
                p['obj'].location=rest_locations[p['obj'].name]+offset.xyz
            for o in [p['obj'] for p in self.parts]+[c[0] for c in self.controls]:
                o.keyframe_insert('location',frame=frame);o.keyframe_insert('rotation_quaternion' if o.rotation_mode=='QUATERNION' else 'rotation_euler',frame=frame);o.keyframe_insert('scale',frame=frame)
        self.scene.frame_end=361;self.scene.frame_set(1)
        self.reference_scene()
        self.scene.frame_end=361;self.scene.frame_set(1)
        # Source images remain available when the checkout moves to another Mac.
        for image in bpy.data.images:
            if image.source=='FILE' and image.filepath and not image.packed_file:
                image.filepath=bpy.path.relpath(bpy.path.abspath(image.filepath),start=str(ROOT/'blender/collection'))
        bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'blender/collection'/(self.id+'.blend')))
        print('COLLECTION_EXPORTED',self.id,'parts',len(parts),'controls',len(samples),flush=True)
        if self.id=='G':
            from optimize_runtime_meshes import optimize
            optimize(out/(self.id+'.glb'))
