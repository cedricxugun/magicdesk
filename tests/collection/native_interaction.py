"""Replay through the Windows application's own form and bridge, without moving
the user's cursor. Captures are native compositor frames, not concept renders.
Requires MagicDeskPreview --collection-qa --control=... --diagnostics=....
"""
import argparse, json, pathlib, time

parser=argparse.ArgumentParser()
parser.add_argument('--directory',required=True)
parser.add_argument('--models',nargs='+',default=['F','G','I','J','K','L','M','N'])
args=parser.parse_args()
out=pathlib.Path(args.directory)
control=out/'commands.txt'
checks=[]
sequence=0

def command(text,delay=.13):
    global sequence
    sequence+=1
    temp=control.with_suffix('.tmp')
    temp.write_text(f'{text} {sequence}',encoding='ascii')
    for attempt in range(30):
        try:temp.replace(control);break
        except PermissionError:
            if attempt==29:raise
            time.sleep(.025)
    time.sleep(delay)

def probe():
    path=out/'collection_probe.json'
    before=path.stat().st_mtime_ns if path.exists() else 0
    command('probe',.15)
    until=time.monotonic()+3
    while time.monotonic()<until:
        try:
            if path.stat().st_mtime_ns!=before:return json.loads(path.read_text(encoding='utf-8-sig'))
        except (OSError,ValueError):pass
        time.sleep(.08)
    raise RuntimeError('Native renderer did not answer probe')

def wait(predicate,timeout=28):
    deadline=time.monotonic()+timeout
    last={}
    while time.monotonic()<deadline:
        last=probe()
        if predicate(last):return last
        time.sleep(.2)
    raise RuntimeError('Timed out waiting for state: '+str(last))

def check(name,passed,details=None):
    checks.append(dict(check=name,passed=bool(passed),details=details))
    print('NATIVE_CHECK',name,bool(passed),details or '',flush=True)
    (out/'interaction_report.json').write_text(json.dumps(dict(all_passed=all(c['passed'] for c in checks),checks=checks,verification='Application-owned input replay through native form, TCP bridge and 3D raycast; not physical mouse automation.',visual_acceptance=False),ensure_ascii=False,indent=2),encoding='utf-8')

def point(kind,p):command(f'point {kind} {round(p[0])} {round(p[1])}')
def click(p):point('down',p);point('up',p)
def capture(name):command('capture '+name,.5)
def button(info,index):return info['buttons'][index*2:index*2+2]

def select(model):
    info=probe()
    if info['active']==model and info['selector']<.01:
        check(model+'_all_controls_hit',all(info['control_hits'].get(str(i))==i for i in range(1,6)),info['control_hits'])
        return info
    if info['selector']<.01:
        entry=next(t for t in info['targets'] if t['kind']=='entry')
        click((entry['x'],entry['y']))
    info=wait(lambda v:v['selector']>.999 and v['state']=='idle')
    capture(model+'_archive')
    for _ in range(10):
        card=next((t for t in info['targets'] if t['kind']=='card' and t['id']==model and t['hit']),None)
        if card:break
        command('wheel -120',.65);info=probe()
    if not card:raise RuntimeError('No visible selectable card for '+model)
    check(model+'_physical_card_visible',True,card)
    click((card['x'],card['y']))
    info=wait(lambda v:v['active']==model and v['state']=='idle' and v['selector']<.001)
    capture(model+'_closed')
    check(model+'_single_base',info['base_instances']==1)
    check(model+'_all_controls_hit',all(info['control_hits'].get(str(i))==i for i in range(1,6)),info['control_hits'])
    return info

try:
    command('reset')
    command('rotation')
    for model in args.models:
        info=select(model)
        # N opens only from its actual bridge detent; other devices engage when
        # the player starts using their first control.
        if model=='N':
            p=button(info,5);point('down',p);point('move',(p[0],p[1]-145));point('up',(p[0],p[1]-145));time.sleep(2.6)
        info=probe();p=button(info,1)
        before=info.get('play',{}).get('values',{}).copy()
        point('down',p)
        held=probe()
        check(model+'_pointer_captured',held['held']==1 and held['drag_kind']==0,held['held'])
        point('move',(p[0]+55,p[1]-55))
        moved=probe()
        point('up',(p[0]+55,p[1]-55))
        check(model+'_drag_changes_control',moved['play']['values']!=before)
        info=probe()
        check(model+'_release_clears_capture',info['held']==-1)
        time.sleep(3)
        capture(model+'_operating')
        if model in ['F','I','L']:
            info=probe();p=button(info,2);point('down',p);time.sleep(1.1)
            held=probe();key={'F':'brake','I':'bellows','L':'aperture'}[model]
            check(model+'_hold_is_sustained',held['play']['values'][key]>.9)
            capture(model+'_held')
            point('up',p);released=probe()
            check(model+'_release_stops_hold',released['play']['values'][key]<.01)
        elif model=='K':
            info=probe();p=button(info,2);point('down',p);point('move',(p[0],p[1]-145));point('up',(p[0],p[1]-145))
            info=probe();check('K_needle_latches',info['play']['values']['stylus']>.9)
            p=button(info,1);point('down',p);point('move',(p[0]+70,p[1]-70));point('up',(p[0]+70,p[1]-70))
            info=probe();check('K_one_pointer_writes',info['play']['response']['ink']>.05)
            capture('K_contact_writing')
        elif model=='M':
            info=probe();p=button(info,2);point('down',p);point('move',(p[0],p[1]-145));point('up',(p[0],p[1]-145));time.sleep(2)
            info=probe();check('M_gravity_changes_orbits',info['play']['response']['capture_age']>2)
            capture('M_infall')
            time.sleep(2.2)
            p=button(info,5);point('down',p)
            for dx,dy in [(0,-55),(55,0),(0,55),(-55,0),(0,-55),(55,0),(0,55),(-55,0),(0,-55)]:point('move',(p[0]+dx,p[1]+dy))
            point('up',p);capture('M_reconstructed')
            check('M_reseed_clears_gravity',probe()['play']['values']['gravity']<.01)
        (out/(model+'_state.json')).write_text(json.dumps(probe(),ensure_ascii=False,indent=2),encoding='utf-8')
        # Passive gauge must never invoke overload/explosion, and a rightward
        # service-rocker gesture must assemble without touching shutdown.
        info=probe();p=button(info,3);actions=len(info['actions']);click(p)
        after=probe();check(model+'_gauge_readonly',len(after['actions'])==actions and after['held']==-1)
        p=button(after,4);point('down',p);point('move',(p[0]+100,p[1]));point('up',(p[0]+100,p[1]))
        info=wait(lambda v:v['module'].get('openness',1)<.01,12)
        check(model+'_assemble_keeps_app_open',info['state']=='idle' and info['active']==model)
    capture('review_end')
except Exception as exc:
    check('replay_completed',False,str(exc))
    raise
