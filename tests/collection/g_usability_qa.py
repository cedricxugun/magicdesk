"""0.3.2 native EXE: labelled controls, tap-to-select, pause and useful guidance."""
import pathlib,json,time,argparse
p=argparse.ArgumentParser();p.add_argument('--directory',required=True);p.add_argument('--live',action='store_true');args=p.parse_args()
out=pathlib.Path(args.directory);control=out/'commands.txt';serial=0;checks=[]
def command(s,delay=.14):
    global serial
    serial+=1;temp=control.with_suffix('.tmp');temp.write_text(f'{s} ux_{serial}',encoding='ascii')
    for i in range(40):
        try:temp.replace(control);break
        except PermissionError:time.sleep(.025)
    time.sleep(delay)
def probe():
    path=out/'collection_probe.json';old=path.stat().st_mtime_ns if path.exists() else 0;command('probe');deadline=time.monotonic()+4
    while time.monotonic()<deadline:
        try:
            if path.stat().st_mtime_ns!=old:return json.loads(path.read_text(encoding='utf-8-sig'))
        except (OSError,ValueError):pass
        time.sleep(.05)
    raise RuntimeError('No native probe')
def wait(fn,timeout=35):
    until=time.monotonic()+timeout
    while time.monotonic()<until:
        v=probe()
        if fn(v):return v
        time.sleep(.15)
    raise RuntimeError('Timeout: '+str(v))
def check(name,ok,detail=None):
    checks.append({'check':name,'passed':bool(ok),'detail':detail});print('G_UX',name,bool(ok),detail or '',flush=True)
    (out/'report.json').write_text(json.dumps({'all_passed':all(x['passed'] for x in checks),'checks':checks,'scope':'native form events through the production hit/capture path; visual inspection separate'},ensure_ascii=False,indent=2),encoding='utf-8')
def point(kind,p):command(f'point {kind} {round(p[0])} {round(p[1])}')
def click(p):point('down',p);point('up',p)
def button(v,i):return v['buttons'][i*2:i*2+2]
def target(v,id):
    t=next(t for t in v['g_operator']['targets'] if t['id']==id);return [t['x'],t['y']]
def action(id):
    v=probe();click(target(v,id));return probe()
def capture(n):command('capture '+n,.3)
def g(v):return v['play']['g_instrument']
try:
    deadline=time.monotonic()+45
    while True:
        try:v=probe();break
        except RuntimeError:
            if time.monotonic()>deadline:raise
            time.sleep(.2)
    if v['active']!='G':
        entry=next(t for t in v['targets'] if t['kind']=='entry');click((entry['x'],entry['y']));v=wait(lambda x:x['selector']>.999)
        card=next(t for t in v['targets'] if t['kind']=='card' and t['id']=='G' and t['hit']);click((card['x'],card['y']));v=wait(lambda x:x['active']=='G' and x['state']=='idle' and x['g_operator']['visible'])
    check('G_defaults_paused',not v['g_operator']['rotation_enabled'])
    check('labelled_controls_are_always_visible',v['g_operator']['visible'] and len(v['g_operator']['targets'])==14)
    capture('01_clear_start')
    if args.live:
        action('page_0');action('align');wait(lambda x:x['module']['openness']>.995)
        print('G_USER_READY_PAUSED_AND_UNWRITTEN',flush=True);raise SystemExit(0)
    v=action('rotate');first=v['angle'];time.sleep(.7);v=probe()
    check('visible_button_starts_rotation',v['g_operator']['rotation_enabled'] and abs(v['angle']-first)>.04)
    v=action('rotate');first=v['angle'];time.sleep(.7);v=probe()
    check('visible_button_stops_rotation',not v['g_operator']['rotation_enabled'] and abs(v['angle']-first)<.0001)
    action('rotate');v=action('page_2');wait(lambda x:x['module']['openness']>.995)
    check('explicit_page_choice_pauses_and_selects',g(v)['selected']==2 and not v['g_operator']['rotation_enabled']);capture('02_rear_page_selected')
    v=probe();before=g(v)['selected'];click(button(v,1));v=probe()
    check('single_tap_on_real_dial_changes_page',g(v)['selected']==(before+1)%6)
    for i in range(6):
        v=action('page_'+str(i));check('page_'+str(i+1)+'_has_direct_selection',g(v)['selected']==i)
    v=action('front');check('front_view_is_paused',abs(v['angle'])<.00001 and not v['g_operator']['rotation_enabled'])
    v=action('page_0');fold=button(v,2);point('down',fold);point('move',(fold[0]+52,fold[1]));point('up',(fold[0]+52,fold[1]));time.sleep(.8)
    v=probe();check('manual_fold_shows_misalignment',g(v)['alignment']<.8);capture('03_clear_misalignment')
    # Capture persists even when the physical slider is released over the UI.
    point('down',fold);point('move',target(v,'page_4'));point('up',target(v,'page_4'));v=probe();check('physical_capture_releases_over_plaque',v['held']==-1)
    action('align');v=wait(lambda x:g(x)['alignment']>.99 and g(x)['pins']>.99)
    check('labelled_align_recovers_whole_bank',all(abs(x-.5)<.0001 for x in g(v)['actual'][:3]));capture('04_ready_to_write')
    write=target(v,'write');point('down',write);time.sleep(.85);point('up',(write[0]+400,write[1]-300));v=probe();part=g(v)['records'][0];time.sleep(.5);v=probe()
    check('hold_button_writes_and_release_outside_pauses',.05<part<.6 and abs(part-g(v)['records'][0])<.000001 and v['g_operator']['held']=='');capture('05_partial_and_instruction')
    point('down',target(v,'write'));v=wait(lambda x:g(x)['peak_time']>.1,8);point('up',target(v,'write'));v=wait(lambda x:1.8<g(x)['peak_time']<4.5,6)
    check('labelled_controls_complete_a_record',g(v)['records'][0]==1.0);capture('06_completed')
    action('assemble');v=wait(lambda x:x['module']['openness']<.001);check('labelled_assemble_stays_running',v['state']=='idle')
    action('explode');v=wait(lambda x:x['module']['explosion']>.999,15);capture('07_exploded_with_controls')
    action('assemble');v=wait(lambda x:x['module']['explosion']<.001,12)
    action('open');time.sleep(.6);action('exit');check('labelled_exit_dispatched',True)
except Exception as e:check('completed',False,str(e));raise
