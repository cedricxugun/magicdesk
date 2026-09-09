"""Replay only the native EXE's physical controls; no floating UI targets."""
import pathlib,json,time,argparse
p=argparse.ArgumentParser();p.add_argument('--directory',required=True);p.add_argument('--live',action='store_true');args=p.parse_args()
out=pathlib.Path(args.directory);control=out/'commands.txt';serial=0;checks=[]
def command(s,delay=.13):
    global serial
    serial+=1;temp=control.with_suffix('.tmp');temp.write_text(f'{s} console_{serial}',encoding='ascii')
    for _ in range(40):
        try:temp.replace(control);break
        except PermissionError:time.sleep(.025)
    time.sleep(delay)
def probe():
    path=out/'collection_probe.json';old=path.stat().st_mtime_ns if path.exists() else 0;command('probe');end=time.monotonic()+4
    while time.monotonic()<end:
        try:
            if path.stat().st_mtime_ns!=old:return json.loads(path.read_text(encoding='utf-8-sig'))
        except (OSError,ValueError):pass
        time.sleep(.05)
    raise RuntimeError('No native probe')
def wait(fn,timeout=25):
    end=time.monotonic()+timeout
    while time.monotonic()<end:
        v=probe()
        if fn(v):return v
        time.sleep(.12)
    raise RuntimeError('Timeout '+str(v.get('play',{})))
def check(name,ok,detail=None):
    checks.append({'check':name,'passed':bool(ok),'detail':detail});print('CONSOLE_NATIVE',name,bool(ok),detail or '',flush=True)
    (out/'report.json').write_text(json.dumps({'all_passed':all(c['passed'] for c in checks),'checks':checks,'input_path':'native desktop form -> bridge -> physical console raycast; no Canvas controls'},ensure_ascii=False,indent=2),encoding='utf-8')
    if not ok:raise AssertionError(name)
def point(kind,p):command(f'point {kind} {round(p[0])} {round(p[1])}')
def click(p):point('down',p);point('up',p)
def state(v):return v['play']['g_instrument']
def capture(name):command('capture '+name,.25)
def button(v,i):return v['buttons'][i*2:i*2+2]
def wheel(v,i,direction):
    x,y=button(v,i);command(f'scroll {120*direction} {x} {y}')
def choose(i):
    v=probe();before=state(v)['selected']
    for _ in range((i-before)%6):wheel(v,1,1)
    return wait(lambda x:state(x)['loaded_index']==i and state(x)['stage']=='playing')
try:
    deadline=time.monotonic()+55
    while True:
        try:v=probe();break
        except RuntimeError:
            if time.monotonic()>deadline:raise
            time.sleep(.2)
    if v['active']!='G':
        entry=next(t for t in v['targets'] if t['kind']=='entry');click((entry['x'],entry['y']));v=wait(lambda x:x['selector']>.999)
        card=next(t for t in v['targets'] if t['kind']=='card' and t['id']=='G' and t['hit']);click((card['x'],card['y']))
        v=wait(lambda x:x['active']=='G' and x['state']=='idle' and x['selector']<.001,40)
    check('no_floating_operator_panel',not v['g_operator']['visible'] and not v['g_operator']['targets'])
    check('all_five_physical_controls_hittable',all(v['control_hits'].get(str(i))==i for i in range(1,6)),v['control_hits'])
    capture('00_physical_console_only')
    knob=button(v,1);point('move',knob);time.sleep(.65);v=probe()
    check('hover_has_no_tooltip_or_toast',not v['tooltip_visible'] and not v['toast_visible'])
    if args.live:
        choose(1);print('RECORD_CONSOLE_READY_FOR_USER',flush=True);raise SystemExit(0)
    # Power must wake the current selected media, even with the shared base lit.
    click(button(v,0));v=wait(lambda x:state(x)['stage']=='playing')
    check('physical_power_wakes_selected_media',state(v)['loaded_index']==state(v)['selected']);capture('01_wake')
    click(button(v,3));time.sleep(.7);v=probe();angle=state(v)['platter_angle'];time.sleep(.55);v=probe()
    check('physical_stop_stays_stopped',not state(v)['spin_enabled'] and abs(state(v)['platter_angle']-angle)<.000001)
    click(button(v,3));time.sleep(.8);v=probe();angle=state(v)['platter_angle'];time.sleep(.60);v=probe()
    check('physical_start_resumes_slow_turn',state(v)['spin_enabled'] and .035<state(v)['platter_angle']-angle<.12)
    before=state(v)['selected'];click(button(v,1));v=probe();check('dial_tap_selects_next',state(v)['selected']==(before+1)%6)
    wheel(v,1,-1);v=probe();check('wheel_selects_previous',state(v)['selected']==before)
    for i in range(6):
        v=choose(i);check('media_%d_original_disc_on_platter'%(i+1),state(v)['owners'][i]=='platter' and state(v)['owners'].count('slot')==5)
        capture('play_%d'%(i+1));before=state(v)['parameters'][i];wheel(v,2,1);v=probe()
        check('media_%d_parameter_wheel'%(i+1),state(v)['parameters'][i]>before)
        check('manipulation_stops_spin',not state(v)['spin_enabled'])
        hold=button(v,5);point('down',hold);time.sleep(.65);v=probe();check('media_%d_pressure_action'%(i+1),state(v)['action_energy']>.99 and v['held']==5)
        capture('action_%d'%(i+1));point('up',(hold[0]+260,hold[1]-170));v=wait(lambda x:state(x)['action_energy']<.001,4)
        check('release_outside_control_recovers',v['held']==-1 and not v['g_operator']['visible'])
    wheel(v,1,1);v=probe();check('six_to_one_wraps',state(v)['selected']==0)
    wheel(v,1,-1);v=probe();check('one_to_six_wraps',state(v)['selected']==5)
    v=wait(lambda x:state(x)['stage']=='playing')
    click(v['console_targets']['disassemble']);v=wait(lambda x:x['module']['explosion']>.999,22)
    check('tap_left_returns_media_then_disassembles',state(v)['owners'].count('slot')==6 and v['module']['parts']==20);capture('07_exploded')
    click(v['console_targets']['assemble']);v=wait(lambda x:x['module']['explosion']<.001 and state(x)['ready_to_fold'],10)
    check('tap_right_assembles_without_quitting',v['state']=='idle');capture('08_assembled')
    click(button(v,0));v=wait(lambda x:state(x)['stage']=='playing')
    click(button(v,0));v=wait(lambda x:state(x)['ready_to_fold'] and x['power']<.001,18)
    check('physical_power_returns_and_sleeps',state(v)['owners'].count('slot')==6);capture('09_sleep')
    click(button(v,1));v=wait(lambda x:state(x)['stage']=='lifting_record',10);click(button(v,6))
    check('physical_close_during_pick_requested',True)
except Exception as e:
    if not checks or checks[-1]['passed']:
        checks.append({'check':'completed','passed':False,'detail':str(e)});(out/'report.json').write_text(json.dumps({'all_passed':False,'checks':checks},ensure_ascii=False,indent=2),encoding='utf-8')
    print('CONSOLE_NATIVE_FAILED',str(e),flush=True);raise
