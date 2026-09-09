"""Real EXE native input replay: selection, wheel, hold, return, shutdown."""
import pathlib,json,time,argparse
p=argparse.ArgumentParser();p.add_argument('--directory',required=True);p.add_argument('--select-only',action='store_true');a=p.parse_args()
out=pathlib.Path(a.directory);control=out/'commands.txt';serial=0;checks=[]
def command(s,delay=.13):
    global serial
    serial+=1;temp=control.with_suffix('.tmp');temp.write_text(f'{s} {serial}',encoding='ascii')
    for _ in range(30):
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
    end=time.monotonic()+timeout
    while time.monotonic()<end:
        v=probe()
        if fn(v):return v
        time.sleep(.10)
    raise RuntimeError('Wait failed '+str(v))
def check(name,ok,detail=None):
    checks.append(dict(check=name,passed=bool(ok),detail=detail));print('G_NATIVE',name,bool(ok),detail or '',flush=True)
    (out/'report.json').write_text(json.dumps(dict(all_passed=all(x['passed'] for x in checks),checks=checks,input_path='native form input replay -> bridge -> projected 3D controls'),ensure_ascii=False,indent=2),encoding='utf-8')
def point(kind,p):command(f'point {kind} {round(p[0])} {round(p[1])}')
def click(p):point('down',p);point('up',p)
def button(v,i):return v['buttons'][i*2:i*2+2]
def capture(n):command('capture '+n,.30)
def state(v):return v['play']['g_instrument']
def drag(p,dx):point('down',p);point('move',(p[0]+dx,p[1]));point('up',(p[0]+dx,p[1]))
try:
    deadline=time.monotonic()+45
    while True:
        try:probe();break
        except RuntimeError:
            if time.monotonic()>deadline:raise
            time.sleep(.2)
    command('reset');command('rotation');v=probe()
    if v['active']!='G':
        entry=next(t for t in v['targets'] if t['kind']=='entry');click((entry['x'],entry['y']));v=wait(lambda x:x['selector']>.999)
        card=next(t for t in v['targets'] if t['kind']=='card' and t['id']=='G' and t['hit']);click((card['x'],card['y']));v=wait(lambda x:x['active']=='G' and x['state']=='idle' and x['selector']<.001)
    check('dedicated_G_mechanism_loaded','g_instrument' in v['play'])
    check('every_controller_hittable',all(v['control_hits'].get(str(i))==i for i in range(1,6)),v['control_hits']);capture('01_rest')
    dial=button(v,1);fold=button(v,2);paddle=button(v,5);service=button(v,4)
    point('move',dial);time.sleep(.6);v=probe();rect=v['tooltip_rect'];band=v['control_band']
    check('help_above_entire_row',v['tooltip_visible'] and rect[1]+rect[3]<band[1]-12);capture('02_help')
    command(f'scroll 120 {dial[0]} {dial[1]}');command(f'scroll -120 {dial[0]} {dial[1]}')
    v=probe();check('wheel_hides_hint_immediately',not v['tooltip_visible'])
    v=wait(lambda x:x['module']['openness']>.999)
    if a.select_only:
        point('down',paddle);time.sleep(4.5);point('up',paddle);command('rotation');print('G_READY_FOR_USER',flush=True);raise SystemExit(0)
    check('wheel_indexes_page',state(v)['selected']==0)
    drag(fold,55);time.sleep(.75);point('down',paddle);time.sleep(.7);v=probe()
    check('misalignment_blocks_record',state(v)['blocked'] and state(v)['records'][0]==0);capture('03_misregistered');point('up',paddle)
    value=state(v)['folds'][0];drag(fold,(.5-value)*130);time.sleep(.8)
    point('down',paddle);time.sleep(1.0);point('up',paddle);v=probe();progress=state(v)['records'][0];time.sleep(.55);v=probe()
    check('release_stops_and_preserves_partial_record',.05<progress<.9 and abs(state(v)['records'][0]-progress)<.00001,progress);capture('04_partial_record')
    command(f'scroll 120 {dial[0]} {dial[1]}');drag(fold,30);command(f'scroll -120 {dial[0]} {dial[1]}');v=probe()
    check('page_local_fold_and_record_recall',abs(v['play']['values']['fold']-.5)<.012 and abs(state(v)['records'][0]-progress)<.00001)
    command(f'scroll 120 {dial[0]} {dial[1]}');v=probe();drag(fold,(.5-v['play']['values']['fold'])*130);command(f'scroll -120 {dial[0]} {dial[1]}');time.sleep(.75)
    point('down',paddle);v=wait(lambda x:state(x)['peak_time']>.10,8);point('up',paddle)
    v=wait(lambda x:2.0<state(x)['peak_time']<4.8,7);check('complete_record_earns_relief',state(v)['records'][0]>.999 and state(v)['projection']>.85);capture('05_memory_relief')
    (out/'peak_state.json').write_text(json.dumps(v,ensure_ascii=False,indent=2),encoding='utf-8')
    command('rotation');time.sleep(3.0);capture('06_rotating_relief');command('rotation')
    drag(service,100);v=wait(lambda x:x['module']['openness']<.001 and state(x)['ready_to_fold'],16)
    check('assemble_rewinds_without_exiting',v['active']=='G' and v['state']=='idle');capture('07_rewound')
    drag(service,-100);v=wait(lambda x:x['module']['explosion']>.999,13);check('service_explodes_mechanism',v['module']['parts']==13);capture('08_exploded')
    drag(service,100);v=wait(lambda x:x['module']['explosion']<.001 and x['module']['openness']<.001,12);check('exact_reassembly',state(v)['ready_to_fold']);capture('09_reassembled')
    command(f'scroll 120 {dial[0]} {dial[1]}');time.sleep(.7);capture('10_interrupt_close');command('quit');check('shutdown_from_opening_requested',True)
except Exception as e:check('completed',False,str(e));raise
