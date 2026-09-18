"""Compare serialized motion fields to evaluated Blender geometry and driven parts."""
import bpy,json,hashlib,math
import numpy as np
from pathlib import Path
from mathutils import Matrix
ROOT=Path(__file__).resolve().parents[2];OUT=ROOT/'review/I_refinement/part_a_mouth/shutter_r2/tongue_probe';r=json.loads((OUT/'build.json').read_text());src=ROOT/r['source'];assert hashlib.sha256(src.read_bytes()).hexdigest()==r['source_sha256']
bpy.ops.wm.open_mainfile(filepath=str(src));scene=bpy.context.scene;arrays={}
for name,path in r['motion_textures'].items():
 p=ROOT/path;assert hashlib.sha256(p.read_bytes()).hexdigest()==r['texture_sha256'][name]
 im=bpy.data.images.load(str(p),check_existing=False);values=np.empty(im.size[0]*im.size[1]*4,dtype=np.float32);im.pixels.foreach_get(values);values=values.reshape(im.size[1],im.size[0],4)[::-1].copy();arrays[name]=values
 assert hashlib.sha256(values.astype('<f4').tobytes()).hexdigest()==r['field_pixel_sha256'][name],('Serialized field mismatch',name)
worst=0.;part_worst=0.;rows=[];w=np.linspace(0,1,17)
for frame in [1,37.25,55.37,68.13,81.29,99.43,119.71,139,199,216.38,257.18,289.43,319,337]:
 scene.frame_set(math.floor(frame),subframe=frame%1);bpy.context.view_layer.update();feed=float(bpy.data.objects[r['drive']]['feed']);k=feed*r['pose_steps'];lo=int(math.floor(k));hi=int(math.ceil(k));f=k-lo
 values={name:a[lo]*(1-f)+a[hi]*f for name,a in arrays.items()};center=values['center'][:,:3];width=values['width'][:,:3];normal=values['normal'][:,:3];bow=values['center'][:,3]-1
 errors=[]
 for skin,name in enumerate(r['mesh_names']):
  surface=center[:,None,:]+width[:,None,:]*(.5-w)[None,:,None]+normal[:,None,:]*(bow[:,None]*np.sin(math.pi*w)[None,:]+skin*.0036)[:,:,None]
  expected=np.concatenate([(surface+normal[:,None,:]*thick).reshape(-1,3) for thick in [-.00075,.00075]])
  expected=expected[:,[0,2,1]]*np.array([1,-1,1])
  o=bpy.data.objects[name];e=o.evaluated_get(bpy.context.evaluated_depsgraph_get());m=e.to_mesh();actual=np.empty(len(m.vertices)*3,dtype=np.float32);m.vertices.foreach_get('co',actual);actual=actual.reshape(-1,3);e.to_mesh_clear();error=float(np.linalg.norm(actual-expected,axis=1).max());errors.append(error);worst=max(worst,error)
 a=r['states'][lo];b=r['states'][hi];expected_axis=np.array(a['axis'])*(1-f)+np.array(b['axis'])*f;axis_error=float(np.linalg.norm(np.array(bpy.data.objects[r['carriage']].location)-expected_axis))
 angle=(a['angle']*(1-f)+b['angle']*f)*r['spin_sign'];target=Matrix.Rotation(angle,3,'Z');actual=bpy.data.objects[r['spool']].matrix_basis.to_3x3();rotation_error=max(abs(target[i][j]-actual[i][j]) for i in range(3) for j in range(3));part_worst=max(part_worst,axis_error,rotation_error)
 rows.append({'frame':frame,'feed':feed,'vertex_errors':errors,'axis_error':axis_error,'rotation_matrix_error':rotation_error})
result={'source_sha256':r['source_sha256'],'component_sha256':r['component_sha256'],'samples':rows,'max_vertex_error':worst,'max_part_error':part_worst,'scoped_passed':worst<1e-5 and part_worst<.0002,'scope':'Serialized fields vs evaluated source foil vertices at listed fractional forward/hold/reverse frames; carriage/spool interpolation. Whole image bytes independently checked during Godot bind. Not original-art, all hardware or continuous collision acceptance.'}
(OUT/'field_contract.json').write_text(json.dumps(result,indent=2)+'\n');print('TONGUE_FIELD_CONTRACT',result['scoped_passed'],worst,part_worst,flush=True)
