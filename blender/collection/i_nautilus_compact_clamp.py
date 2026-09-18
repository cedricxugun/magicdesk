"""Retain the measured A grip and seam hardware; give the rear an inboard lip."""
import bpy,bmesh,math
from mathutils import Vector

def rebuild_halves(mount,col,h):
    profile=[(.570,.580),(.609,.580),(.613,.588),(.602,.620),(.590,.6265),(.570,.638),(.478,.638),(.478,.627),(.584,.627),(.584,.594),(.570,.587)]
    for name in ['IC1_CollarUpper','IC1_CollarLower']:bpy.data.objects.remove(bpy.data.objects[name],do_unlink=True)
    def make(name,vs,fs):
        m=bpy.data.meshes.new(name+'Mesh');m.from_pydata(vs,[],fs);m.update();o=bpy.data.objects.new(name,m);col.objects.link(o);h.finish(o,name,mount,(0,0,0),'A_Satin',.0004);return o
    def merge(a,b):
        bpy.context.view_layer.update();bpy.context.view_layer.objects.active=a
        mod=a.modifiers.new('Integral clamp boss','BOOLEAN');mod.operation='UNION';mod.solver='EXACT';mod.object=b;bpy.ops.object.modifier_apply(modifier=mod.name)
        h.parts.remove(b.name);bpy.data.objects.remove(b,do_unlink=True)
    halves=[]
    for half in range(2):
        begin=half*math.pi+.006;end=(half+1)*math.pi-.006;n=128;vs=[];fs=[]
        for r,z in profile:vs.extend((r*math.cos(begin+(end-begin)*i/n),r*math.sin(begin+(end-begin)*i/n),z) for i in range(n+1))
        for j in range(len(profile)):
            for i in range(n):fs.append((j*(n+1)+i,j*(n+1)+i+1,((j+1)%len(profile))*(n+1)+i+1,((j+1)%len(profile))*(n+1)+i))
        fs.extend([tuple(j*(n+1) for j in range(len(profile)-1,-1,-1)),tuple(j*(n+1)+n for j in range(len(profile)))])
        ring=make('IC1_CollarUpper' if half==0 else 'IC1_CollarLower',vs,fs)
        for sign in [-1,1]:
            tab=h.box('IN3_ClampTabTool',(.042,.055,.048),mount,(sign*.594,.036 if half==0 else -.036,.588),'A_Satin',.003);merge(ring,tab)
            h.drill(ring,.0056,.16,mount,(sign*.601,0,.590),(0,1,0))
        halves.append(ring)
    outline=[(-.555,.582),(-.583,.582),(-.653,.533),(-.653,.493),(-.606,.493),(-.555,.552)]
    for sign in [-1,1]:
        for cheek in [-1,1]:
            x=sign*.17+cheek*.021;vs=[(x+side*.005,y,z) for side in [-1,1] for y,z in outline];n=len(outline)
            fs=[tuple(range(n-1,-1,-1)),tuple(range(n,2*n))]+[(i,(i+1)%n,(i+1)%n+n,i+n) for i in range(n)]
            merge(halves[1],make('IN3_TrunnionCheekTool',vs,fs))
        h.drill(halves[1],.0092,.11,mount,(sign*.17,-.627,.519),(1,0,0))
    flange=bpy.data.objects['IAM_RearMountFlange_0074'];tool=flange.copy();tool.data=flange.data.copy();col.objects.link(tool);tool.name='IN3_ActualFlangeReliefTool'
    for v in tool.data.vertices:v.co+=v.normal*.0015
    tool.data.update();bpy.context.view_layer.update()
    for ring in halves:
        bpy.context.view_layer.objects.active=ring;mod=ring.modifiers.new('Measured original A flange relief','BOOLEAN');mod.operation='DIFFERENCE';mod.solver='EXACT';mod.object=tool;bpy.ops.object.modifier_apply(modifier=mod.name)
    bpy.data.objects.remove(tool,do_unlink=True)
    # A washer on a curved ring needs a real flat spotface. The old tab alone
    # did not remove the ring surface behind its washer and head.
    for sign in [-1,1]:
        x=sign*.601
        for side in [-1,1]:
            ring=halves[1 if side<0 else 0]
            h.drill(ring,.010,.24,mount,(x,side*(.0649+.12),.590),(0,side,0))
        old=bpy.data.objects['IC1_SeamCrossBolt_'+str(sign)];bpy.data.objects.remove(old,do_unlink=True)
        pin=h.cylinder('IC1_SeamCrossBolt_'+str(sign),.0052,.137,mount,(x,0,.590),'A_Nickel',(0,1,0))
        for side in [-1,1]:
            head=bpy.data.objects['IC1_SeamRetainer_%s_%s'%(sign,side)];head.location=Vector((x,side*.069,.590))
            bpy.context.view_layer.update();bpy.context.view_layer.objects.active=pin
            mod=pin.modifiers.new('Assembled pin and seated end cap','BOOLEAN');mod.operation='UNION';mod.solver='EXACT';mod.object=head;bpy.ops.object.modifier_apply(modifier=mod.name);bpy.data.objects.remove(head,do_unlink=True)
    return profile
