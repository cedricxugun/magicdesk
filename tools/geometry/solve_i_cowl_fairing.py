"""Matrix-free regularized biharmonic fairing using NumPy only."""
import json,time
from pathlib import Path
import numpy as np
ROOT=Path(__file__).resolve().parents[2];OUT=ROOT/'review/I_refinement/nautilus_r1/cowl_fairing_r22';s=json.loads((OUT/'problem.json').read_text());rows=[]
for mesh in s['meshes']:
    vertices=np.asarray(mesh['vertices'],dtype=np.float64);edges=np.asarray(mesh['edges'],dtype=np.int64);free=np.asarray(mesh['free'],dtype=bool);n=len(vertices)
    a=np.concatenate((edges[:,0],edges[:,1]));b=np.concatenate((edges[:,1],edges[:,0]));length=np.linalg.norm(vertices[a]-vertices[b],axis=1)
    weights=1/np.maximum(length,np.quantile(length,.10));total=np.bincount(a,weights,minlength=n);weights/=total[a]
    def lap(x):return x-np.bincount(a,weights*x[b],minlength=n)
    def transpose(x):return x-np.bincount(b,weights*x[a],minlength=n)
    alpha=1e-7
    def full(x):return transpose(lap(x))+alpha*x
    def operator(x):
        v=np.zeros(n);v[free]=x;return full(v)[free]
    result=vertices.copy();solves=[]
    for axis in range(3):
        fixed=vertices[:,axis].copy();fixed[free]=0.;rhs=alpha*vertices[free,axis]-full(fixed)[free]
        x=vertices[free,axis].copy();residual=rhs-operator(x);direction=residual.copy();rr=float(np.sum(residual*residual));initial=max(rr,1e-30)
        for iteration in range(3500):
            ap=operator(direction);denom=float(np.sum(direction*ap))
            if denom<=0 or rr/initial<1e-14:break
            step=rr/denom;x+=step*direction;residual-=step*ap;new_rr=float(np.sum(residual*residual));direction=residual+(new_rr/max(rr,1e-30))*direction;rr=new_rr
        result[free,axis]=x;solves.append({'axis':axis,'iterations':iteration+1,'relative_residual':(rr/initial)**.5})
    displacement=np.linalg.norm(result-vertices,axis=1);assert np.isfinite(result).all() and np.isfinite(displacement).all();assert np.array_equal(result[~free],vertices[~free])
    row={'mesh':mesh['mesh'],'vertices':result.tolist(),'free_count':int(free.sum()),'maximum_displacement':float(displacement.max()),'mean_free_displacement':float(displacement[free].mean()),'solves':solves,'fixed_vertices_exact':True};rows.append(row)
    print(mesh['mesh'],row['maximum_displacement'],row['mean_free_displacement'],solves,flush=True)
(OUT/'solution.json').write_text(json.dumps({'source_sha256':s['source_sha256'],'regularization':1e-7,'meshes':rows,'scope':'Candidate surface fairing with exactly pinned vertices; no geometry/clearance acceptance implied.'},separators=(',',':'))+'\n')
