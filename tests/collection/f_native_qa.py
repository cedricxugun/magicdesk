"""F-only native-input ergonomics and full operational art replay."""
import pathlib,json,time,argparse
p=argparse.ArgumentParser();p.add_argument('--directory',required=True);p.add_argument('--extended',action='store_true');p.add_argument('--select-only',action='store_true');args=p.parse_args()
out=pathlib.Path(args.directory);control=out/'commands.txt';serial=0;checks=[]
def command(s,delay=.13):
    global serial
    serial+=1;temp=control.with_suffix('.tmp');temp.write_text(f'{s} {serial}',encoding='ascii')
    for i in range(30):
        try:temp.replace(control);break
        except PermissionError:time.sleep(.025)
    time.sleep(delay)
def probe():
    path=out/'collection_probe.json';old=path.stat().st_mtime_ns if path.exists() else 0
    command('probe',.13);deadline=time.monotonic()+4
    while time.monotonic()<deadline:
        try:
            if path.stat().st_mtime_ns!=old:return json.loads(path.read_text(encoding='utf-8-sig'))
        except (OSError,ValueError):pass
        time.sleep(.05)
    raise RuntimeError('No native probe reply')
def wait(fn,timeout=30):
    deadline=time.monotonic()+timeout
    while time.monotonic()<deadline:
        v=probe()
        if fn(v):return v
        time.sleep(.15)
    raise RuntimeError('Timed out: '+str(v))
def check(name,passed,detail=None):
    checks.append(dict(check=name,passed=bool(passed),detail=detail));print('F_NATIVE',name,bool(passed),detail or '',flush=True)
    (out/'report.json').write_text(json.dumps(dict(all_passed=all(c['passed'] for c in checks),checks=checks,input_path='native form -> bridge -> actual 3D hit test'),ensure_ascii=False,indent=2),encoding='utf-8')
def point(kind,p):command(f'point {kind} {round(p[0])} {round(p[1])}')
def click(p):point('down',p);point('up',p)
def capture(name):command('capture '+name,.35)
def button(v,i):return v['buttons'][i*2:i*2+2]
try:
    deadline=time.monotonic()+40
    while True:
        try:probe();break
        except RuntimeError:
            if time.monotonic()>deadline:raise
            time.sleep(.2)
    command('reset');command('rotation')
    v=probe()
    if v['active']!='F':
        entry=next(t for t in v['targets'] if t['kind']=='entry');click((entry['x'],entry['y']))
        v=wait(lambda x:x['selector']>.999)
        card=next(t for t in v['targets'] if t['kind']=='card' and t['id']=='F' and t['hit']);click((card['x'],card['y']))
        v=wait(lambda x:x['active']=='F' and x['state']=='idle' and x['selector']<.001)
    check('F_full_physics_loaded','instrument' in v['play'])
    check('every_physical_control_is_hittable',all(v['control_hits'].get(str(i))==i for i in range(1,6)),v['control_hits'])
    if args.select_only:
        knob=button(v,1);command(f'scroll 120 {knob[0]} {knob[1]}');command(f'scroll -120 {knob[0]} {knob[1]}');command('rotation')
        print('F_READY_FOR_USER',flush=True);raise SystemExit(0)
    capture('01_rest')
    knob=button(v,1);point('move',knob);time.sleep(.65);v=probe()
    rect=v['tooltip_rect'];band=v['control_band']
    check('tooltip_after_deliberate_hover',v['tooltip_visible'])
    check('tooltip_clear_of_entire_control_band',rect[1]+rect[3]<=band[1]-12,[rect,band]);capture('02_help_clearance')
    before=v['play']['values']['trim'];command(f'scroll 120 {knob[0]} {knob[1]}');v=probe()
    check('wheel_changes_preload',v['play']['values']['trim']>before,[before,v['play']['values']['trim']])
    check('scroll_hides_hint_immediately',not v['tooltip_visible'])
    time.sleep(3.2)
    point('down',knob);v=probe();check('press_hides_hint_and_captures',v['held']==1 and not v['tooltip_visible'])
    point('move',(knob[0]+32,knob[1]));point('up',(knob[0]+32,knob[1]));time.sleep(1)
    v=probe();check('linear_drag_without_drawing_circle',v['play']['values']['trim']>before+.3);capture('03_bias')
    brake=button(v,2);point('down',brake);time.sleep(.65);v=probe()
    check('brake_has_zero_beam_velocity',abs(v['play']['instrument']['physics']['omega'])<.006)
    check('held_hint_stays_hidden',not v['tooltip_visible']);capture('04_brake')
    point('up',brake)
    v=probe();trim=v['play']['values']['trim'];point('down',knob);point('move',(knob[0]-trim*90,knob[1]));point('up',(knob[0]-trim*90,knob[1]))
    v=wait(lambda x:1.3<x['play']['instrument']['peak_time']<2.5,35)
    check('physical_balance_earns_signature',v['play']['instrument']['coherence']>.70);capture('05_suspended_vernier')
    (out/'peak_state.json').write_text(json.dumps(v,ensure_ascii=False,indent=2),encoding='utf-8')
    v=wait(lambda x:x['play']['instrument']['peak_time']>4.5,8);capture('06_writeback')
    v=probe();assembly=button(v,4);point('down',assembly);point('move',(assembly[0]+100,assembly[1]));point('up',(assembly[0]+100,assembly[1]))
    v=wait(lambda x:x['module']['openness']<.001 and x['play']['instrument']['stage']=='rest',18)
    check('assembly_parks_without_exiting',v['active']=='F' and v['state']=='idle');capture('07_parked')
    if args.extended:
        command('rotation');command(f'scroll 120 {knob[0]} {knob[1]}');time.sleep(8)
        v=probe();physics=v['play']['instrument']['physics']
        vectors=[[float(x) for x in physics[k].strip('()').split(',')] for k in ['direction','right_direction']]
        check('rotation_keeps_gravity_vertical',all(x[1]<-.97 for x in vectors),vectors);capture('08_rotating_side')
        command('rotation')
        assembly=button(v,4);point('down',assembly);point('move',(assembly[0]-100,assembly[1]));point('up',(assembly[0]-100,assembly[1]))
        v=wait(lambda x:x['module']['explosion']>.999,20)
        check('native_full_disassembly',v['module']['parts']==18);capture('09_exploded_side')
        point('down',assembly);point('move',(assembly[0]+100,assembly[1]));point('up',(assembly[0]+100,assembly[1]))
        v=wait(lambda x:x['module']['explosion']<.001 and x['module']['openness']<.001,12);capture('10_reassembled_side')
        command(f'scroll -120 {knob[0]} {knob[1]}');time.sleep(.8);capture('11_shutdown_during_motion')
        command('quit');check('graceful_shutdown_requested_from_motion',True)
except Exception as e:
    check('completed',False,str(e));raise
