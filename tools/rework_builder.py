from pathlib import Path
p=Path(__file__).resolve().parents[1]/'blender'/'build_helios.py'
s=p.read_text(encoding='utf-8')
def rep(a,b):
 global s
 assert a in s,a[:120]
 s=s.replace(a,b)
rep("(.91,.875,.785),.13,.29", "(.86,.82,.73),.05,.29")
rep("(.22,.255,.285),.92,.28", "(.33,.32,.285),.91,.32")
rep("(.075,.085,.098),.72,.32", "(.105,.10,.087),.72,.35")
rep("(.73,.78,.81),.96,.19", "(.58,.55,.49),.96,.24")
rep("(.46,.055,.035),.3,.25", "(.34,.055,.032),.3,.28")
rep("(.55,.42,.27),.83,.24", "(.45,.34,.22),.88,.3")
rep("(1,.18,.022),.38,.2,3", "(1,.115,.008),.42,.23,.8")
rep("(1,.37,.045),.2,.24,1.5", "(1,.25,.023),.25,.25,1.4")
rep("('Steel','metal_roughness.png','Roughness')", "('Steel','steel_albedo.png','Base Color'),('Chrome','nickel_albedo.png','Base Color'),('Steel','metal_roughness.png','Roughness')")
rep('def put(o,parent=None', '''for key,filename in [('Ivory','enamel_normal.png'),('Steel','metal_normal.png'),('Chrome','metal_normal.png')]:
 m=M[key];nt=m.node_tree;tex=nt.nodes.new('ShaderNodeTexImage');tex.image=bpy.data.images.load(str(ASSET/filename),check_existing=True);tex.image.colorspace_settings.name='Non-Color';normal=nt.nodes.new('ShaderNodeNormalMap');normal.inputs['Strength'].default_value=.32;nt.links.new(tex.outputs['Color'],normal.inputs['Color']);nt.links.new(normal.outputs['Normal'],nt.nodes.get('Principled BSDF').inputs['Normal'])
M['Ivory'].node_tree.nodes.get('Principled BSDF').inputs['Coat Weight'].default_value=.24
M['Ivory'].node_tree.nodes.get('Principled BSDF').inputs['Coat Roughness'].default_value=.2

def put(o,parent=None''')
rep("True,.006 if r>.06 else 0)","True,min(.004,r*.12))")
rep("sol=o.modifiers.new('Panel thickness','SOLIDIFY')", """layer=me.uv_layers.new(name='PanelUV')
 for p in me.polygons:
  for li in p.loop_indices:
   vi=me.loops[li].vertex_index;layer.data[li].uv=(vi%(steps+1)/steps,vi//(steps+1))
 sol=o.modifiers.new('Panel thickness','SOLIDIFY')""")
rep("1.354,.175,.44", "1.354,.155,.46")
rep("cyl('Button_%d_Gasket'%i,.164,.025,'Red',mount,(0,0,.008))", "cyl('Button_%d_Gasket'%i,.146,.018,'Rubber',mount,(0,0,.002))")
rep("cyl('Button_%d_Bezel'%i,.148,.048,'Chrome',mount,(0,0,.035))", "cyl('Button_%d_Bezel'%i,.138,.043,'Steel',mount,(0,0,.023))\n torus('Button_%d_MilledRim'%i,.124,.009,'Chrome',mount,(0,0,.051))")
rep(".125,.025,'Ivory',mount,(0,0,.069),n=48", ".113,.016,'Ivory',mount,(0,0,.055),n=64")
rep("(.035,.13,.32),'Red',strip,bevel=.02", "(.02,.042,.18),'Red',strip,bevel=.006")
rep('Z0=1.055;HEIGHT=2.68;R0=.31', 'Z0=1.02;HEIGHT=2.68;R0=.31')
rep('def radius(t):return .31*(1-t)+.10*t+.79*(math.sin(math.pi*t)**.94)*(1-.10*t)', '''def radius(t):
 ts=[0,.06,.16,.30,.47,.62,.76,.87,.95,1];rs=[.31,.43,.62,.78,.865,.84,.73,.565,.365,.17]
 t=max(0,min(1,t));j=next((i for i in range(len(ts)-1) if t<=ts[i+1]),len(ts)-2);u=(t-ts[j])/(ts[j+1]-ts[j]);h=ts[j+1]-ts[j]
 m0=(rs[j+1]-rs[max(0,j-1)])/(ts[j+1]-ts[max(0,j-1)])
 m1=(rs[min(len(ts)-1,j+2)]-rs[j])/(ts[min(len(ts)-1,j+2)]-ts[j])
 return (2*u**3-3*u*u+1)*rs[j]+(u**3-2*u*u+u)*h*m0+(-2*u**3+3*u*u)*rs[j+1]+(u**3-u*u)*h*m1''')
rep('nu=14;nv=42;half=math.radians(28.65)', 'nu=24;nv=72;half=math.radians(28.5 if inside else 26.5)')
rep("sol.thickness=.030 if inside else .036;sol.offset=-1", "sol.thickness=.028 if inside else .035;sol.offset=-1\n bev=o.modifiers.new('Rolled enamel edge','BEVEL');bev.width=.005;bev.segments=3")
rep('a=math.radians(28.4)*side', 'a=math.radians(26.5)*side')
rep("pts,.015,'Chrome',rails)", "pts,.006,'Chrome',rails)")
start=s.index(' t=.24;rr=radius(t);q=');end=s.index(" hub=part('Petal_",start)
s=s[:start]+''' t=.34;rr=radius(t);ang=math.radians(23);q=(rr*math.cos(ang)-R0,rr*math.sin(ang),HEIGHT*t)
 cube('Latch_Chrome_%02d'%i,(.04,.065,.16),'Steel',latch,q,.007,rot=(0,0,ang))
 cube('Latch_Red_%02d'%i,(.047,.038,.126),'Red',latch,(q[0]+.02,q[1],q[2]),.006,rot=(0,0,ang))
 for dz in [-.067,.067]:cyl('Latch_Pin_%d_%s'%(i,dz),.013,.014,'Chrome',latch,(q[0]+.038,q[1],q[2]+dz),rot=(0,math.pi/2,0),n=16)
'''+s[end:]
rep("A=rad*1.01+Vector((0,0,.69));sphere('BaseJoint_Ball_%02d'%i,.13,'Steel',fixed,A)", "A=rad*.99+Vector((0,0,.88));sphere('BaseJoint_Ball_%02d'%i,.105,'Steel',fixed,A)")
rep(" for side in [-1,1]:cube('BaseJoint_Clevis_%02d_%d'%(i,side),(.24,.095,.20),'Chrome',fixed,A+tan*side*.12,.025,rot=(0,0,th))",'')
rep("cyl('ActuatorBarrel_%02d'%i,.082,.42,'Steel',bp)", "cyl('ActuatorBarrel_%02d'%i,.09,.32,'Chrome',bp)")
rep("for z in [-.18,.16]:torus('ActuatorCollar_%02d_%s'%(i,z),.085,.016,'Chrome',bp,(0,0,z))", "for z in [-.18,-.14,.135,.18]:cyl('ActuatorCollar_%02d_%s'%(i,z),.108,.03,'Steel',bp,(0,0,z))")
rep("cyl('ActuatorRedBand_%02d'%i,.087,.07,'Red',bp,(0,0,-.09))", "torus('ActuatorRedBand_%02d'%i,.1,.008,'Red',bp,(0,0,-.118))")
rep("attach=Vector((radius(.20)-R0,0,HEIGHT*.20))", "attach=Vector((radius(.145)-R0,0,HEIGHT*.145))")
# New detailing module runs before transforms are sampled and before mesh merging.
rep('def smooth(t):t=max', "exec(compile((OUT/'detail_helios.py').read_text(encoding='utf-8'),str(OUT/'detail_helios.py'),'exec'))\n\ndef smooth(t):t=max")
rep("location=(4.8,-7.9,4.3)", "location=(.75,-9,4.3)")
rep("S.cycles.samples=32", "S.cycles.samples=96")
rep("S.render.resolution_x=1200;S.render.resolution_y=1400", "S.render.resolution_x=1400;S.render.resolution_y=1600")
rep("bg.inputs['Strength'].default_value=.4", "bg.inputs['Strength'].default_value=.24")
rep("('Key',(-3,-4,7),750,5,(1,.91,.78)),('Rim',(4,2,5),1000,4,(.74,.84,1)),('Front',(-1,-6,3),250,3,(1,.98,.94))", "('Key',(-3.5,-4,6),650,3,(1,.93,.82)),('Rim',(3,2,5),900,3,(.83,.88,1)),('Front',(1,-6,3),110,4,(1,.98,.94))")
rep("S.view_settings.view_transform='AgX'", "S.view_settings.view_transform='AgX';S.view_settings.look='AgX - Medium High Contrast'")
# Neutral ground and photography are only in the Blender review collection, never in GLB.
rep('def pose(open_v=0,phase=0,explosion=0):', '''bpy.ops.mesh.primitive_plane_add(size=200,location=(0,0,-.015));ground=bpy.context.object;ground.name='STUDIO_Ground';ground.data.materials.append(mat('Studio_Backdrop',(.055,.059,.061),.1,.5))
S.render.film_transparent=False
try:
 prefs=bpy.context.preferences.addons['cycles'].preferences;prefs.compute_device_type='OPTIX';prefs.get_devices()
 for dev in prefs.devices:dev.use=dev.type!='CPU'
 if any(d.use for d in prefs.devices):S.cycles.device='GPU'
except Exception as e:print('CYCLES_DEVICE',e)

def pose(open_v=0,phase=0,explosion=0):''')
rep("('closed',1,5.15),('open',180,7.25),('exploded',340,8.5)", "('closed',1,4.55),('open',180,7.25),('exploded',340,8.5)")
p.write_text(s,encoding='utf-8')
print('REFINED_BUILDER_READY')
