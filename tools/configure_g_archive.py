"""Point the G slot at the redesigned archive; update only its control hints."""
import pathlib,json
ROOT=pathlib.Path(__file__).resolve().parents[1]
p=ROOT/'app/assets/collection/control_profiles.json';text=p.read_text(encoding='utf-8');data=json.loads(text)
hints={'leaf':'单击换下一页，或用滚轮 / 下方编号直接选页；读头会自动播放这一页的藏品。','fold':'拖动或滚轮调整当前藏品；具体用途显示在下方操作铭牌上。','imprint':'按住触发当前藏品的专属动作；松手后平缓恢复。'}
labels={'leaf':'选择藏品书页','fold':'藏品参数','imprint':'藏品动作'}
for c in data['models']['G']:
    for key,new in [('hint',hints[c['key']]),('label',labels[c['key']])]:text=text.replace(json.dumps(c[key],ensure_ascii=False),json.dumps(new,ensure_ascii=False),1)
p.write_text(text,encoding='utf-8')
