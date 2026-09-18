"""Fixed-camera service layout. Parts first clear their seats, then spread.

All offsets are in Godot Y-up coordinates. Disc/cradle pairs keep their own
numbered column, instead of using the obsolete circular magazine offsets.
"""
from mathutils import Vector

def arrange(parts,spec,head):
    by_name={p['name']:p for p in parts}
    def route(name,knots):
        p=by_name[name];p['offset']=list(knots[-1][1])
        p['route']=[{'at':t,'offset':list(v)} for t,v in knots]
    zero=(0,0,0)
    for i in range(6):
        side=-1 if i<3 else 1;row=i%3
        slot=Vector(spec['slots'][i]['p'])
        # Top original record stays at the top; the front record moves down.
        target=Vector((side*1.63,3.22-row*1.01,.02))
        travel=target-slot
        release=Vector((-side*.50,.30,.81)).normalized()*.18
        lift=Vector((0,travel.y+.18,0))
        # Spread vertically before bringing the three inclined trays into a
        # common display plane. Diagonal straight-line travel crossed them.
        route('GA_P_Record'+str(i),[(0,zero),(.12,zero),(.35,lift),(.56,travel),(.64,travel),(.75,travel+release),(1,travel+release)])
        route('GA_P_Cradle'+str(i),[(0,zero),(.12,zero),(.35,lift),(.56,travel),(1,travel)])
    paths={
      'GA_P_Stand':[(0,zero),(.45,zero),(.62,(0,.08,0)),(1,(0,.08,0))],
      'GA_P_Magazine':[(0,zero),(.65,zero),(.80,(0,.16,-.10)),(1,(0,.16,-.10))],
      'GA_P_UpperArm':[(0,zero),(.25,zero),(.51,(.32,.30,0)),(1,(.32,.30,0))],
      'GA_P_Forearm':[(0,zero),(.21,zero),(.49,(.32,.55,0)),(1,(.32,.55,0))],
      'GA_P_Wrist':[(0,zero),(.17,zero),(.45,(.56,.92,-.40)),(1,(.56,.92,-.40))],
      'GA_P_ReaderPlatter':[(0,zero),(.38,zero),(.56,(0,.18,.14)),(1,(0,.18,.14))],
      'GA_P_ToneLiftBase':[(0,zero),(.18,zero),(.35,(.24,.08,0)),(1,(.24,.08,0))],
      'GA_P_OpticalTonearm':[(0,zero),(.10,(0,.35,0)),(.19,(.24,.35,.22)),(1,(.24,.35,.22))],
    }
    for name,knots in paths.items():route(name,knots)
    # Head coordinates are neutral during service. Ring modules first leave
    # their coaxial seats and only then stagger into separate viewing lanes.
    destinations={
      'GA_P_OpticalBarrel':(-1.03,.16,.62),
      'GA_P_IrisCartridge':(-.46,.20,.38),
      'GA_P_DisplayCartridge':(.12,.19,.12),
      'GA_P_HeadChassis':(.72,.24,-.13),
      'GA_P_HeadController':(1.35,.58,-.37),
      'GA_P_HeadHeatSink':(.82,-.32,.16),
    }
    for name,target in destinations.items():
        axial=(0,0,.16) if name in ['GA_P_OpticalBarrel','GA_P_IrisCartridge','GA_P_DisplayCartridge'] else (0,0,-.12)
        if name=='GA_P_HeadController':axial=(0,0,-.40)
        if name=='GA_P_HeadHeatSink':axial=(0,0,-.70)
        route(name,[(0,zero),(.48,zero),(.63,axial),(.81,target),(1,target)])
        if name=='GA_P_HeadHeatSink':by_name[name]['route'].insert(3,{'at':.74,'offset':[.82,-.32,-.75]})
        yaw={'GA_P_OpticalBarrel':-.25,'GA_P_IrisCartridge':-.58,'GA_P_DisplayCartridge':-.16,'GA_P_HeadChassis':-.65,'GA_P_HeadController':-.30,'GA_P_HeadHeatSink':.62}[name]
        for knot in by_name[name]['route']:knot['rotation']=[0,yaw if knot['at']>=.81 else 0,0]
    shell_targets=[(.45,.80,0),(-.45,.80,0),(0,-.44,-.52)]
    for i,target in enumerate(shell_targets):
        clearance=(0,-.38,-.36) if i==2 else tuple(v*.32 for v in target)
        if i==2:
            # First unseat the lip, slide the open throat clear of the neck
            # and wrist yoke, then lower the detached cover behind them.
            route('GA_P_HeadShell'+str(i),[(0,zero),(.30,zero),(.33,(0,-.04,0)),(.41,(0,-.04,-.52)),(.46,target),(1,target)])
        else:
            route('GA_P_HeadShell'+str(i),[(0,zero),(.30,zero),(.37,clearance),(.46,target),(1,target)])
    head['service_layout']='production/G_optical_curator/head_service/structure_and_explode_target.png'
