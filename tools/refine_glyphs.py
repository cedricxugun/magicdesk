from pathlib import Path
p=Path(__file__).resolve().parents[1]/'blender'/'build_helios.py';s=p.read_text(encoding='utf-8')
a=s.index(' # Large geometric button glyphs');b=s.index(' BUTTONS.append',a)
s=s[:a]+''' # Enamel inlays match the six symbols on the approved B reference.
 def dot(name,x,y,r):
  cyl(name+'_Recess',r+.002,.0015,'Black',cap,(x,y,.0095),n=24)
  cyl(name+'_Red_Inlay',r,.0014,'Red',cap,(x,y,.0104),n=24)
 if i==0:
  pts=[]
  for cc,aa in [(.033,range(0,181,9)),(-.033,range(180,361,9))]:
   for deg in aa:a=math.radians(deg);pts.append((.017*math.cos(a),cc+.017*math.sin(a),.010))
  pts.append(pts[0]);tube('Reference_Power_Slot',pts,.0025,'Black',cap)
  cube('Reference_Power_Red',(.008,.062,.0015),'Red',cap,(0,0,.010),.001)
 elif i==1:
  dot('Reference_Sun_Core',0,0,.018)
  for j in range(8):
   a=j*math.tau/8;dot('Reference_Sun_Ray',.047*math.cos(a),.047*math.sin(a),.008)
 elif i==2:
  for x,y in [(0,.028),(-.029,-.024),(.029,-.024)]:dot('Reference_Triple',x,y,.020)
 elif i==3:
  for j in range(4):a=j*math.tau/4;dot('Reference_Quad',.033*math.cos(a),.033*math.sin(a),.019)
 elif i==4:
  points=[(-.049,-.043,.010),(.049,-.043,.010),(0,.063,.010)]
  me=bpy.data.meshes.new('Reference_Triangle');me.from_pydata(points,[],[(0,1,2)]);me.materials.append(M['Red']);o=bpy.data.objects.new('Reference_Triangle',me);COL.objects.link(o);o.parent=cap
  tube('Reference_Triangle_Outline',points+[points[0]],.0024,'Black',cap)
  beam('Reference_Triangle_Stem',(0,-.075,.011),(0,.047,.011),.0027,'Black',cap)
 else:
  for j in range(8):
   a=j*math.tau/8;length=.062 if j%2==0 else .045
   beam('Reference_Star_Ray',(.016*math.cos(a),.016*math.sin(a),.010),(length*math.cos(a),length*math.sin(a),.010),.003,'Red',cap)
  dot('Reference_Star_Core',0,0,.010)
'''+s[b:]
p.write_text(s,encoding='utf-8')
print('REFERENCE_CONTROL_GLYPHS_READY')
