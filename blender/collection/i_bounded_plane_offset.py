"""A bounded outward corner offset, using active planes when least squares fails."""
import itertools
import numpy as np

def solve(normals,minimum=1.,maximum=2.,maximum_length=8.):
    n=np.asarray(normals,dtype=float)
    candidate=np.linalg.lstsq(n,np.ones(len(n)),rcond=.005)[0];dots=n@candidate
    if min(dots)>.25:
        candidate*=minimum/min(dots);dots=n@candidate
        if min(dots)>=minimum-1e-6 and (maximum is None or max(dots)<=maximum) and np.linalg.norm(candidate)<maximum_length:return candidate,'scaled_least_squares'
    # In 3D the minimum-norm point of a feasible polyhedron has at most three
    # independent active planes. Include upper offsets to bound formed corners.
    a=n if maximum is None else np.concatenate([n,-n]);b=np.full(len(n),minimum) if maximum is None else np.concatenate([np.full(len(n),minimum),np.full(len(n),-maximum)]);best=None
    for size in [1,2,3]:
        for indices in itertools.combinations(range(len(a)),size):
            active=a[list(indices)];rhs=b[list(indices)];delta=np.linalg.lstsq(active,rhs,rcond=1e-8)[0]
            if np.max(np.abs(active@delta-rhs))>1e-6:continue
            multipliers=np.linalg.lstsq(active.T,delta,rcond=1e-8)[0]
            if min(multipliers)<-1e-7:continue
            length=np.linalg.norm(delta)
            if length>=maximum_length or best is not None and length>=best[0]:continue
            if np.min(a@delta-b)<-1e-6:continue
            best=(length,delta)
    assert best is not None,('No bounded outward offset',n.tolist(),minimum,maximum,maximum_length)
    return best[1],'active_planes'
