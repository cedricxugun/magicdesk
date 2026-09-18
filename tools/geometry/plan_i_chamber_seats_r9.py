"""Locate source-exact clamp seats on actual frame/film/core surfaces."""
import bpy,bmesh,json,hashlib,math,sys
from pathlib import Path
from mathutils import Vector,Matrix
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT/'blender/collection'));import i_fitted_surface as fitted;import i_fitted_laminate as laminate
args=sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else [];source_report=next((a.split('=',1)[1] for a in args if a.startswith('--source-report=')),'review/I_refinement/nautilus_r1/receiver_pocket_r8/build.json');output=next((a.split('=',1)[1] for a in args if a.startswith('--out=')),'review/I_refinement/nautilus_r1/chamber_seats_r9/layout_candidates.json');destination=ROOT/output;OUT=destination.parent;OUT.mkdir(parents=True,exist_ok=True);seed=json.loads((ROOT/source_report).read_text());assert hashlib.sha256((ROOT/seed['source']).read_bytes()).hexdigest()==seed['source_sha256']
bpy.ops.wm.open_mainfile(filepath=str(ROOT/seed['source']));bpy.context.scene.frame_set(1);bpy.context.view_layer.update();C=Vector(seed['shape_config']['body_center']);radii=Vector(seed['shape_config']['body_radii']);core=bpy.data.objects['IN3_ContinuousThroat']
from mathutils.bvhtree import BVHTree
core.data.calc_loop_triangles();core_tree=BVHTree.FromPolygons([core.matrix_world@v.co for v in core.data.vertices],[tuple(t.vertices) for t in core.data.loop_triangles],all_triangles=True)
def point(phi,theta,inset):
    a=theta+1.12*math.cos(phi)+.10*math.sin(phi)**2*math.sin(theta+1.);r=radii-Vector((inset,inset,inset));return C+Vector((r.x*math.sin(phi)*math.cos(a),-r.y*math.cos(phi),r.z*math.sin(phi)*math.sin(a)))
front_fragments='--front-fragments' in args
through_core='--through-core' in args
requested_cells=next((set(int(x) for x in a.split('=',1)[1].split(',')) for a in args if a.startswith('--cells=')),None)
requested_phi=next(([float(x) for x in a.split('=',1)[1].split(',')] for a in args if a.startswith('--phi=')),None)
outline=[];rx=.009 if front_fragments else .010;ry=.020 if front_fragments else .024;corner=.004 if front_fragments else .005
for cx,cy,start in [(rx-corner,ry-corner,0),(-rx+corner,ry-corner,math.pi/2),(-rx+corner,-ry+corner,math.pi),(rx-corner,-ry+corner,math.pi*1.5)]:
    for k in range(9):
        a=start+k*math.pi/2/8;outline.append((cx+corner*math.cos(a),cy+corner*math.sin(a)))
rows=[];failures=[]
for index,cell in enumerate(seed['acoustic_cells']):
    if requested_cells is not None and index+1 not in requested_cells:continue
    if front_fragments and requested_cells is None and index+1 not in [5,6,7,8]:continue
    frame=bpy.data.objects[cell['frame']];film=bpy.data.objects[cell['diaphragm']];a,b=cell['theta']
    for side,theta in [('L',a+.105),('R',b-.105)]:
        for phi in (requested_phi if requested_phi is not None else [.28,.32,.36,.40,.44,.48,.52,.56,.60,.64,.68] if front_fragments else [.70,.85,1.05,1.30,1.55,1.80,2.0,2.10,2.25,2.35,2.50,2.65]):
            origin=point(phi,theta,.074);n=Vector(tuple((origin[i]-C[i])/(radii[i]-.074)**2 for i in range(3))).normalized();y=(point(phi+.001,theta,.074)-point(phi-.001,theta,.074)).normalized();x=y.cross(n).normalized();y=n.cross(x).normalized();f=Matrix((x,y,n)).transposed().to_4x4();f.translation=origin;stage='frame'
            try:
                frame_under=fitted.clipped_surface([frame],outline,frame=f,from_positive=False,normal_limit=.80,with_planes=True)
                if through_core:
                    stage='visible_cap_footprint';cap_patch=fitted.clipped_surface([frame],outline,frame=f,from_positive=True,normal_limit=.15)
                    stage='visible_cap_topology';cv,cf=fitted.extruded_patch(*cap_patch,top_offset=.005,bottom_offset=.0002);cm=bpy.data.meshes.new('CapTopologyProbe');cm.from_pydata(cv,[],cf);cm.update();bm=bmesh.new();bm.from_mesh(cm);bad=sum(not e.is_manifold for e in bm.edges);bm.free();bpy.data.meshes.remove(cm);assert not bad,('Nonmanifold projected cap',bad)
                stage='film_front'
                film_front=fitted.clipped_surface([film],outline,frame=f,from_positive=True,normal_limit=.80,with_planes=True)
                stage='film_back'
                film_back=fitted.clipped_surface([film],outline,frame=f,from_positive=False,normal_limit=.80,with_planes=True)
                stage='core'
                core_front=fitted.clipped_surface([core],outline,frame=f,from_positive=True,normal_limit=.80,with_planes=True)
                stage='core_wall';walls=[]
                for by in [-.012,.012]:
                    ray=f@Vector((0,by,5.));first=core_tree.ray_cast(ray,-n,10.);assert first[0] is not None;second=core_tree.ray_cast(first[0]-n*.00001,-n,10.);assert second[0] is not None
                    wall=(first[0]-second[0]).dot(n);assert first[1].dot(n)>.5 and second[1].dot(n)<-.5,('Ambiguous core wall',first[1].dot(n),second[1].dot(n));assert wall>(.006 if through_core else .014),('Core too thin for this joint method',wall);walls.append(wall)
                if through_core:
                    stage='core_inner';fitted.clipped_surface([core],outline,frame=f,from_positive=False,normal_limit=.50,ray_from_positive=True,visible_layer=1,with_planes=True)
                stage='overlay'
                upper=laminate.between(frame_under,film_front);lower=laminate.between(film_back,core_front)
                rows.append({'cell':index+1,'side':side,'phi':phi,'theta':theta,'frame':frame.name,'film':film.name,'matrix':[list(r) for r in f],'outline':outline,'upper':upper[2],'lower':lower[2],'core_wall_at_bolts':walls,'joining_method':'through_bolt_with_fitted_inside_backing_and_nut' if through_core else 'blind_core_thread'})
            except AssertionError as error:failures.append({'cell':index+1,'side':side,'phi':phi,'stage':stage,'reason':str(error)})
    print('CHAMBER_SEAT_CANDIDATES',index+1,sum(r['cell']==index+1 for r in rows),flush=True)
destination.write_text(json.dumps({'source_sha256':seed['source_sha256'],'candidates':rows,'failed_candidates':failures,'scope':'Actual full footprint, paired source-plane overlay and core wall at both bolt axes; '+('inside wall footprint for a through joint with backing and nuts' if through_core else 'blind core thread depth')+'; no manufacturing holes or hardware yet.'},indent=2)+'\n')
print('CHAMBER_SEAT_PLAN',len(rows),len(failures),flush=True)
