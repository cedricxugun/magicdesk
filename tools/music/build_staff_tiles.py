"""Bounded, glyph-complete score tiles from Cairo SVG, preserving original geometry."""
from pathlib import Path
from fractions import Fraction
import xml.etree.ElementTree as E
import re,json,copy,math,hashlib,statistics,argparse
ROOT=Path(__file__).resolve().parents[2];BASE=ROOT/'production/I_refinement/moonlight/engraving'
OUT=ROOT/'production/I_refinement/moonlight/tiles';OUT.mkdir(exist_ok=True)
E.register_namespace('','http://www.w3.org/2000/svg');E.register_namespace('xlink','http://www.w3.org/1999/xlink')
parser=argparse.ArgumentParser();parser.add_argument('--variant',choices=['staff','compact'],default='compact');args=parser.parse_args();prefix='compact-' if args.variant=='compact' else ''
NUM=r'[-+]?(?:\d*\.\d+|\d+)(?:[eE][-+]?\d+)?';TILE=512.;SCALE=4

def transform(box,raw):
    if not raw:return box
    m=re.fullmatch(r'matrix\(([^)]+)\)',raw);assert m,raw
    a,b,c,d,e,f=map(float,re.findall(NUM,m[1]));points=[(a*x+c*y+e,b*x+d*y+f) for x in [box[0],box[2]] for y in [box[1],box[3]]]
    return min(p[0] for p in points),min(p[1] for p in points),max(p[0] for p in points),max(p[1] for p in points)
def bounds(node):
    tag=node.tag.split('}')[-1]
    if tag=='path':
        commands=re.findall(r'[a-df-zA-DF-Z]',node.get('d',''));assert set(commands)<=set('MLCZmlcz'),set(commands)
        assert not set(commands)&set('mlc'),'relative Cairo paths require explicit parser'
        numbers=list(map(float,re.findall(NUM,node.get('d',''))));assert len(numbers)%2==0
        xx=numbers[::2];yy=numbers[1::2];box=(min(xx),min(yy),max(xx),max(yy)) if xx else (0,0,0,0)
    elif tag=='use':
        x=float(node.get('x',0));y=float(node.get('y',0));box=(x-16,y-28,x+30,y+20)
    elif tag=='g':
        bb=[bounds(c) for c in node];box=(min(b[0] for b in bb),min(b[1] for b in bb),max(b[2] for b in bb),max(b[3] for b in bb)) if bb else (0,0,0,0)
    else:raise ValueError(tag)
    return transform(box,node.get('transform',''))
all_rows=[]
for movement in [1,2,3]:
    source=BASE/f'moonlight{movement}-{prefix}cairo.svg';root=E.parse(source).getroot();view=list(map(float,root.get('viewBox').split()));width,height=view[2:]
    definitions=[c for c in root if c.tag.endswith('defs')];draw=[c for c in root if c not in definitions];boxes=[bounds(c) for c in draw]
    folder=OUT/f'm{movement}';folder.mkdir(exist_ok=True);paths=[]
    for index in range(math.ceil(width/TILE)):
        left=index*TILE;right=left+TILE
        page=E.Element(root.tag,dict(root.attrib));page.set('viewBox',f'{left} 0 {TILE} {height}');page.set('width',str(int(TILE*SCALE)));page.set('height',str(math.ceil(height*SCALE)))
        for definition in definitions:page.append(copy.deepcopy(definition))
        for child,box in zip(draw,boxes):
            # Keep conservative control-point bounds. Crossing staff lines are clipped by viewport.
            if box[2]>=left-2 and box[0]<=right+2:page.append(copy.deepcopy(child))
        for node in page.iter():
            for attr in ['fill','stroke']:
                if node.get(attr) and node.get(attr)!='none':node.set(attr,'#ffffff')
            if node.get('style'):node.set('style',node.get('style').replace('rgb(0%,0%,0%)','#ffffff'))
        dest=folder/f'{index:03}.svg';dest.write_bytes(E.tostring(page,encoding='utf-8',xml_declaration=True));paths.append(str(dest.relative_to(ROOT)))
    notation=json.loads((BASE/f'moonlight{movement}-{prefix}notation.json').read_text());factor=width/float(notation['viewbox'].split()[2]);groups={}
    for note in notation['notes']:
        if note['visible']:groups.setdefault(float(Fraction(note['quarter'])),[]).append(note['x']*factor)
    anchors=[{'quarter':q,'x':statistics.median(xs)} for q,xs in sorted(groups.items())]
    # Grace/collision offsets may move a glyph left; the scrolling clock itself never reverses.
    for a,b in zip(anchors,anchors[1:]):b['x']=max(a['x'],b['x'])
    all_rows.append({'movement':movement,'width':width,'height':height,'tile_width':TILE,'pixels_per_unit':SCALE,'tiles':paths,'anchors':anchors,'source_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),'scope':'Conservative whole-glyph vector tiles. Compact candidate omits long TextScript instructions and fingerings; full-source engraving retained. Native readability and source mapping still require review.'})
    print('STAFF_TILES',movement,len(paths),flush=True)
(OUT/'manifest.json').write_text(json.dumps({'movements':all_rows},indent=2)+'\n')
