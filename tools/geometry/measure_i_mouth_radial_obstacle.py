"""Fine axial support envelope of actual evaluated A triangles over seven poses."""
import bpy,json,hashlib
import numpy as np
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];OUT=ROOT/'review/I_refinement/nautilus_r1/cowl_fairing_r22';s=json.loads((ROOT/'review/I_refinement/nautilus_r1/mouth_finish_r21/build.json').read_text());bpy.ops.wm.open_mainfile(filepath=str(ROOT/s['source']));scene=bpy.context.scene
lo=-.25;step=.005;grid=np.arange(lo,.900001,step);profile=np.zeros(len(grid));mouth=[o for o in bpy.data.objects if o.type=='MESH'and o.name.startswith('IAM_')]
for frame in [1,31,61,91,121,151,181]:
    scene.frame_set(frame);bpy.context.view_layer.update();inverse=bpy.data.objects['IAM_MODULE'].matrix_world.inverted();dg=bpy.context.evaluated_depsgraph_get()
    for o in mouth:
        e=o.evaluated_get(dg);m=e.to_mesh();m.calc_loop_triangles();coords=np.empty(len(m.vertices)*3);m.vertices.foreach_get('co',coords);coords=coords.reshape((-1,3));transform=np.asarray(inverse@e.matrix_world);p=np.einsum('ij,kj->ki',transform[:3,:3],coords)+transform[:3,3];radius=np.hypot(p[:,0],p[:,1]);z=p[:,2]
        k=(z-lo)/step
        for bins in [np.floor(k).astype(np.int64),np.ceil(k).astype(np.int64)]:
            valid=(bins>=0)&(bins<len(grid));np.maximum.at(profile,bins[valid],radius[valid])
        triangles=np.empty(len(m.loop_triangles)*3,dtype=np.int32);m.loop_triangles.foreach_get('vertices',triangles);triangles=triangles.reshape((-1,3));edges=np.concatenate((triangles[:,[0,1]],triangles[:,[1,2]],triangles[:,[2,0]]));a=p[edges[:,0]];b=p[edges[:,1]];low=np.maximum(0,np.ceil((np.minimum(a[:,2],b[:,2])-lo)/step).astype(np.int64));high=np.minimum(len(grid)-1,np.floor((np.maximum(a[:,2],b[:,2])-lo)/step).astype(np.int64));counts=np.maximum(high-low+1,0);counts[np.abs(b[:,2]-a[:,2])<1e-10]=0;valid=counts>0;a=a[valid];b=b[valid];low=low[valid];counts=counts[valid]
        if len(counts):
            starts=np.cumsum(counts)-counts;which=np.repeat(np.arange(len(counts)),counts);bins=np.repeat(low,counts)+np.arange(int(counts.sum()))-np.repeat(starts,counts);f=(grid[bins]-a[which,2])/(b[which,2]-a[which,2]);point=a[which,:2]+(b[which,:2]-a[which,:2])*f[:,None];np.maximum.at(profile,bins,np.hypot(point[:,0],point[:,1]))
        e.to_mesh_clear()
    print('RADIAL_OBSTACLE_FRAME',frame,float(profile.max()),flush=True)
# Neighbor maxima enclose vertex extrema between sample planes as well.
support=np.maximum.reduce([profile,np.r_[profile[0],profile[:-1]],np.r_[profile[1:],profile[-1]]])
(OUT/'mouth_obstacle.json').write_text(json.dumps({'source_sha256':s['source_sha256'],'mouth_component_sha256':s['mouth_component_sha256'],'step_mouth':step,'world_scale':.70,'clearance_world':.003,'profile':[[float(z),float(r)]for z,r in zip(grid,support)],'scope':'Actual evaluated A triangle edge-plane intersections and neighboring vertex extrema across seven source poses. Conservative rotational support, not continuous sweep or shell thickness.'},indent=2)+'\n')
