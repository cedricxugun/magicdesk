"""Independent Euler-Lagrange check in five generalized coordinates.

Uses finite differences of Cartesian energy geometry and a 5x5 mass matrix,
not the runtime's constraint-force elimination. Four-bar closure is solved
iteratively rather than by the runtime's analytic circle-intersection formula.
"""
import json,pathlib,math,numpy as np
ROOT=pathlib.Path(__file__).resolve().parents[2]
records=json.loads((ROOT/'review/F_complete/lagrange_samples.json').read_text())
REST=math.radians(-42)

def directions(q):
    return [np.array([a,-math.sqrt(1-a*a-b*b),b]) for a,b in [q[1:3],q[3:5]]]

def positions(q,yaw):
    theta=q[0];top=np.array([.4+.82*math.cos(theta),2.64+.82*math.sin(theta)])
    fixed=np.array([.4,.934]);point=np.array([1.14,1.63])
    for _ in range(16):
        u=point-fixed;v=point-top;f=np.array([u@u-1.01**2,v@v-.50**2])
        if np.max(np.abs(f))<1e-14:break
        point-=np.linalg.solve(2*np.stack([u,v]),f)
    assert np.max(np.abs(f))<1e-10
    rotation=np.array([[math.cos(yaw),0,math.sin(yaw)],[0,1,0],[-math.sin(yaw),0,math.cos(yaw)]])
    left=rotation@np.array([.4+.66*math.cos(theta-2*math.pi/3),2.64+.66*math.sin(theta-2*math.pi/3),.235])
    right=rotation@np.array([point[0],point[1],.055])
    d,e=directions(q)
    return np.stack([left+.45*d,right+.37*e])

def potential(q,s):
    r=positions(q,s['yaw'])
    return 9.81/s['scale']*(s['left_mass']*r[0,1]+s['right_mass']*r[1,1])+.5*s['spring']*(q[0]-REST-s['trim']*.55)**2-.4*s['polarity']*q[0]

def lagrange(s):
    q=np.array(s['q']);v=np.array(s['velocity']);yaw=s['yaw'];step=2e-5
    eye=np.eye(5);J=np.stack([(positions(q+step*e,yaw)-positions(q-step*e,yaw))/(2*step) for e in eye],axis=2)
    gradient=np.array([(potential(q+step*e,s)-potential(q-step*e,s))/(2*step) for e in eye])
    # Directional second derivative gives Jdot*qdot plus prescribed-yaw
    # acceleration; this is the Coriolis/centrifugal term from d/dt(dL/dqdot).
    dt=1e-4
    plus=positions(q+dt*v,yaw+dt*s['yaw_rate']+.5*dt*dt*s['yaw_accel'])
    zero=positions(q,yaw)
    minus=positions(q-dt*v,yaw-dt*s['yaw_rate']+.5*dt*dt*s['yaw_accel'])
    bias=(plus-2*zero+minus)/(dt*dt)
    cart_velocity=(plus-minus)/(2*dt)
    masses=[s['left_mass'],s['right_mass']]
    M=np.zeros((5,5));M[0,0]=s['inertia'];inertial=np.zeros(5);external=np.zeros(5)
    for i,m in enumerate(masses):
        M+=m*J[i].T@J[i];inertial+=m*J[i].T@bias[i]
        drag=s['air_drag']+(7 if s['parking'] else 0)
        force=-drag*cart_velocity[i]
        if s['parking']:
            d=directions(q)[i];force+=m*np.array([-d[0],0,-d[2]])*12
        external+=J[i].T@force
    external[0]-=s['shaft_drag']*v[0]+s['brake']*8*np.sign(v[0])
    if s['parking']:external[0]+=-18*(q[0]-REST)-4.5*v[0]
    return np.linalg.solve(M,-inertial-gradient+external),float(np.linalg.eigvalsh(M)[0])

errors=[];failed=[];minimum_eigenvalue=math.inf
for i,s in enumerate(records):
    expected,eigenvalue=lagrange(s);actual=np.array(s['actual']);difference=np.abs(actual-expected)
    minimum_eigenvalue=min(minimum_eigenvalue,eigenvalue);errors.append(float(difference.max()))
    if not np.all(difference<2e-4+3e-5*np.abs(expected)):failed.append(dict(sample=i,max_error=float(difference.max()),actual=actual.tolist(),lagrange=expected.tolist()))
report=dict(samples=len(records),all_passed=not failed,max_absolute_acceleration_difference=max(errors),minimum_mass_matrix_eigenvalue=minimum_eigenvalue,failures=failed,method='Independent finite-difference Euler-Lagrange mass-matrix calculation; five generalized coordinates, two spherical hangers, iterative linkage closure; includes gravity, spring, drag, sliding brake, magnetic torque, and prescribed yaw.',excluded='Static sticking/contact impacts and motor-driven storage are nonsmooth constraints or actuated choreography and tested separately.')
(ROOT/'review/F_complete/lagrange_equivalence.json').write_text(json.dumps(report,indent=2))
print(json.dumps(report,indent=2));raise SystemExit(0 if report['all_passed'] else 1)
