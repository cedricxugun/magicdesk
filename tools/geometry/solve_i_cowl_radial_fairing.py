"""Bounded radial surface fairing; original angular and axial coordinates stay fixed."""
import json,hashlib,shutil
from pathlib import Path
import numpy as np
ROOT=Path(__file__).resolve().parents[2];OUT=ROOT/'review/I_refinement/nautilus_r1/cowl_fairing_r22';s=json.loads((OUT/'problem.json').read_text());obstacle=json.loads((OUT/'mouth_obstacle.json').read_text());assert s['source_sha256']==obstacle['source_sha256']
if (OUT/'solution.json').exists():
    old=(OUT/'solution.json').read_bytes();(OUT/('solution_before_radial_'+hashlib.sha256(old).hexdigest()[:8]+'.json')).write_bytes(old)
matrix=np.asarray(s['mouth_matrix_blender']);inverse=np.linalg.inv(matrix);profile=np.asarray(obstacle['profile']);rows=[]
for mesh in s['meshes']:
    vertices=np.asarray(mesh['vertices']);local=np.einsum('ij,kj->ki',inverse[:3,:3],vertices)+inverse[:3,3];r0=np.hypot(local[:,0],local[:,1]);free=np.asarray(mesh['free'],dtype=bool);edges=np.asarray(mesh['edges']);n=len(vertices)
    a=np.concatenate((edges[:,0],edges[:,1]));b=np.concatenate((edges[:,1],edges[:,0]));length=np.linalg.norm(vertices[a]-vertices[b],axis=1);weights=1/np.maximum(length,np.quantile(length,.10));weights/=np.bincount(a,weights,minlength=n)[a]
    def lap(x):return x-np.bincount(a,weights*x[b],minlength=n)
    def transpose(x):return x-np.bincount(b,weights*x[a],minlength=n)
    alpha=1e-7
    def hessian(x):return transpose(lap(x))+alpha*x
    floor=np.interp(local[:,2],profile[:,0],profile[:,1])+obstacle['clearance_world']/.70+np.asarray(mesh['outer_radial_surface'])*(.024/.70)
    result=r0.copy();active=np.zeros(n,dtype=bool);history=[]
    for outer_iteration in range(24):
        unknown=free&~active;fixed=result.copy();fixed[unknown]=0.;fixed[active]=floor[active]
        def operator(x):
            full=np.zeros(n);full[unknown]=x;return hessian(full)[unknown]
        rhs=alpha*r0[unknown]-hessian(fixed)[unknown];x=result[unknown].copy();residual=rhs-operator(x);direction=residual.copy();rr=float(np.sum(residual*residual));initial=max(rr,1e-30)
        for iteration in range(3500):
            ap=operator(direction);denom=float(np.sum(direction*ap))
            if denom<=0 or rr/initial<1e-12:break
            step=rr/denom;x+=step*direction;residual-=step*ap;next_rr=float(np.sum(residual*residual));direction=residual+(next_rr/max(rr,1e-30))*direction;rr=next_rr
        result[unknown]=x;result[active]=floor[active]
        violations=free&(result<floor-1e-7);gradient=hessian(result)-alpha*r0;release=active&(gradient<-1e-7)
        history.append({'iteration':outer_iteration,'active':int(active.sum()),'violations':int(violations.sum()),'release':int(release.sum()),'cg_iterations':iteration+1,'relative_residual':(rr/initial)**.5})
        if not np.any(violations)and not np.any(release):break
        active=(active&~release)|violations
    result[free]=np.maximum(result[free],floor[free]);output_local=local.copy();output_local[free,:2]*=(result[free]/r0[free])[:,None]
    output=vertices.copy();output[free]=np.einsum('ij,kj->ki',matrix[:3,:3],output_local[free])+matrix[:3,3]
    assert np.array_equal(output[~free],vertices[~free])and np.isfinite(output).all()
    displacement=np.linalg.norm(output-vertices,axis=1)
    row={'mesh':mesh['mesh'],'vertices':output.tolist(),'free_count':int(free.sum()),'maximum_displacement':float(displacement.max()),'mean_free_displacement':float(displacement[free].mean()),'fixed_vertices_exact':True,'radial_constraints':int(active.sum()),'minimum_vertex_obstacle_margin_mouth':float(np.min(result[free]-floor[free])),'iterations':history};rows.append(row)
    print(mesh['mesh'],row['maximum_displacement'],row['mean_free_displacement'],history[-1],flush=True)
(OUT/'solution.json').write_text(json.dumps({'source_sha256':s['source_sha256'],'solver':'radial_biharmonic_with_A_obstacle','regularization':alpha,'obstacle_sha256':hashlib.sha256((OUT/'mouth_obstacle.json').read_bytes()).hexdigest(),'meshes':rows,'scope':'Candidate radial fairing with fixed angular/axial coordinates, exact pinned vertices, measured A radial obstacle and outer-wall reserve. Actual triangle clearance and thickness still require verification.'},separators=(',',':'))+'\n')
