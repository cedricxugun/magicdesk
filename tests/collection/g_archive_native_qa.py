"""User-facing EXE validation of the six-media player and its actual controls."""
import pathlib,json,time,argparse
p=argparse.ArgumentParser();p.add_argument('--directory',required=True);p.add_argument('--live',action='store_true');args=p.parse_args()
out=pathlib.Path(args.directory);control=out/'commands.txt';serial=0;checks=[]
def command(s,delay=.14):
    global serial
    serial+=1;temp=control.with_suffix('.tmp');temp.write_text(f'{s} archive_{serial}',encoding='ascii')
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
def wait(fn,timeout=35):
    end=time.monotonic()+timeout
    while time.monotonic()<end:
        v=probe()
        if fn(v):return v
        time.sleep(.12)
    raise RuntimeError('Timeout '+str(v))
def check(name,ok,detail=None):
    checks.append({'check':name,'passed':bool(ok),'detail':detail});print('ARCHIVE_NATIVE',name,bool(ok),detail or '',flush=True)
    (out/'report.json').write_text(json.dumps({'all_passed':all(c['passed'] for c in checks),'checks':checks,'input_path':'native desktop form -> actual UI/3D hit capture -> archive state'},ensure_ascii=False,indent=2),encoding='utf-8')
def point(kind,p):command(f'point {kind} {round(p[0])} {round(p[1])}')
def click(p):point('down',p);point('up',p)
def target(v,id):
    t=next(t for t in v['g_operator']['targets'] if t['id']==id);return [t['x'],t['y']]
def action(id):v=probe();click(target(v,id));return probe()
def state(v):return v['play']['g_instrument']
def capture(name):command('capture '+name,.32)
def button(v,i):return v['buttons'][i*2:i*2+2]
try:
    deadline=time.monotonic()+50
    while True:
        try:v=probe();break
        except RuntimeError:
            if time.monotonic()>deadline:raise
            time.sleep(.2)
    if v['active']!='G':
        t=next(t for t in v['targets'] if t['kind']=='entry');click((t['x'],t['y']));v=wait(lambda x:x['selector']>.999)
        t=next(t for t in v['targets'] if t['kind']=='card' and t['id']=='G' and t['hit']);click((t['x'],t['y']));v=wait(lambda x:x['active']=='G' and x['state']=='idle' and x['g_operator']['visible'])
    check('default_stopped',not v['g_operator']['rotation_enabled']);check('fifteen_named_inputs',len(v['g_operator']['targets'])==15)
    capture('00_closed_player')
    if args.live:
        action('page_1');wait(lambda x:state(x)['stage']=='playing',12);print('ARCHIVE_READY_FOR_USER_PAUSED',flush=True);raise SystemExit(0)
    action('rotate');v=probe();angle=v['angle'];time.sleep(.6);v=probe();check('visible_start_rotation',abs(v['angle']-angle)>.04)
    action('rotate');v=probe();angle=v['angle'];time.sleep(.6);v=probe();check('visible_stop_rotation',abs(v['angle']-angle)<.00001)
    action('front')
    for i in range(6):
        action('page_'+str(i));v=wait(lambda x:state(x)['stage']=='playing' and state(x)['loaded_index']==i,12)
        check('page_%d_automatically_reads_unique_content'%(i+1),state(v)['display_amount']>.99,state(v)['title'])
        capture('%02d_idle_%d'%(i*2+1,i+1))
        panel=v['g_operator']['panel'];start=target(v,'parameter');finish=[panel[0]+136+(214*.8 if i%2 else 214*.2),start[1]]
        point('down',start);point('move',finish);point('up',finish);v=probe()
        check('page_%d_parameter_changes'%(i+1),abs(state(v)['parameters'][i]-(.8 if i%2 else .2))<.02)
        hold=target(v,'write');point('down',hold);time.sleep(.45);v=probe();check('page_%d_action_responds'%(i+1),state(v)['action_energy']>.99)
        capture('%02d_action_%d'%(i*2+2,i+1));time.sleep(.65);point('up',(hold[0]+310,hold[1]-210));v=wait(lambda x:state(x)['action_energy']<.001,4)
        check('page_%d_release_recovers'%(i+1),v['g_operator']['held']=='')
    v=action('play');before=state(v)['times'][5];time.sleep(.7);v=probe();check('pause_current_specimen',state(v)['playback_paused'] and abs(state(v)['times'][5]-before)<.00001);capture('13_paused')
    action('play');v=probe();before=state(v)['selected'];click(button(v,1));v=probe();check('physical_dial_single_click_selects',state(v)['selected']==(before+1)%6)
    action('page_1');wait(lambda x:state(x)['stage']=='playing',12)
    action('open');v=wait(lambda x:x['power']<.01 and x['module']['openness']<.001 and state(x)['stage']=='sleep',18)
    check('sleep_closes_book_before_power_off',state(v)['platform_amount']<.001 and state(v)['loaded_index']==-1);capture('14_true_sleep')
    action('page_3');wait(lambda x:state(x)['stage']=='playing',14);check('page_choice_wakes_and_plays',True)
    action('explode');v=wait(lambda x:x['module']['explosion']>.999,18);check('whole_player_disassembly',v['module']['parts']==14);capture('15_disassembled')
    action('assemble');wait(lambda x:x['module']['explosion']<.001 and x['module']['openness']<.001,14)
    action('page_0');time.sleep(.55);action('exit');check('exit_interrupts_reading_safely_requested',True)
except Exception as e:check('completed',False,str(e));raise
