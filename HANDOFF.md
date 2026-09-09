# MagicDesk 接手说明

## 2026-09-10 换机交接：从 AI 机头和独立特效的实际制作继续

本段优先于所有下方历史日志。用户要求把工作推送 Git 后换机器继续；**这是开发中交接，不是美术验收或新版 EXE 发布。** 下面旧段落中的“尚未推送”“正在烘焙”等是当时状态，当前事实以本段为准。

### 最新用户要求与已确定方向

1. 用户明确拒绝首轮唱机：上部太小、唱片没铺满小唱盘、结构和材质质量差，打印特效不符图稿；不能再拿功能测试说已完成或达到AAA。
2. 爪子被替换：机械臂末端改球形 AI 机头，有真实相机快门叶片、镜头内像素眼睛，可眨眼/歪头/打盹。独立下投射器通过光束吸附原唱片；面部表演不能带偏承载唱片的投射器。
3. 所有操作在实体操控台上。黑色浮动 UI 和挡操作的提示已被拒绝，不能恢复。实体选片轮支持单击/滚轮，调节滑块支持拖动/滚轮，按住演绎、转/停、左右拆/装，保留电源/退出。
4. 原片存取、同盘打印、60秒一圈、完整反向回收、拆解/组装/退出均要成立；最多六片。不能在落盘时放大片子或生成替身。
5. 所有设计/特效素材使用订阅内置 image_gen，禁止使用或探测 apilink / 外部图片 API。当前工具不暴露底层型号，不得把图片说成已核验的指定Sunburst。

### 已保存、可在另一台机器取得的内容

| 内容 | 路径 | 当前状态 |
| --- | --- | --- |
| AI主造型、修正比例的打印高潮、快门性格 | `production/G_record_player/r2/` | 新视觉目标，尚未做成AI三维模型 |
| 四组独立特效分镜 | `production/G_record_player/r3_fx/01_optical_capture.png`、`02_groove_decode.png`、`03_materialization.png`、`04_safe_recovery.png` | 已单独出图，每组含三个连续阶段；不能拿整机概念图替代这些特效图 |
| 特效制作契约、节奏和素材出处 | `production/G_record_player/r3_fx/README.md`、`prompts.json`、`manifest.json` | 已记录接点、峰值、完整收光、颜色联动和三维实现方式 |
| 专用纹理 | `app/assets/collection/art/G_AI/field_strands.png`、`groove_traces.png`、`optical_field_atlas.png` | 已生成/存入项目；**尚未接入**，不是已完成特效 |
| 原始六件藏品独立源 | `blender/collection/G_curiosities.blend/.json` | 不再依赖大书壳；可复用rig，但用户仍要求精修几何。r2/r3的新观测塔未制作 |
| 旧爪式唱机功能源 | `blender/collection/G_record_player.blend`、`build_g_record_player.py`、`app/assets/collection/models/G_record_player.glb/.json` | 注册表仍加载这版；.50唱片/.80唱盘，20组拆解，视觉被用户否定，不能当新AI版 |
| 旧功能版完整源动画 | `G_record_player.blend`、`bake_g_record_player.py`、`review/G_record_player/blender_bake.json` | 已烘焙3523帧/30FPS、111对象、四光学层/32微光；未做完整源动画视觉验收 |
| 新实体控件 | `blender/collection/G_Record_Controls.blend`、`build_g_record_controls.py`、`app/assets/collection/record_controls.glb`、`app/collection/record_console.gd` | 已在旧功能版接入，无Canvas操作面板；140网格合为15刚性组 |
| Windows实际输入与帧时间证据 | `review/G_record_player/native_console/` | 五实体控件、六件内容、轮选、参数、按住/释放、起停、拆装、休眠、持片中关闭均回放通过；平均59.10FPS/P95 21.09ms，含首次载入最大238.91ms；正常退出0，原生错误0。视频仅代表旧爪式功能版 |

`dist/MagicDesk.exe` 保留旧0.3.1发布文件。当前源码版本0.4.0，生成过的0.4.0功能试制包只在本机 `dist/staging/MagicDesk-Record-Console.exe`，不随Git提交，也不应冒充通过美术验收的版本。原B/HELIOS与F保留。Mac尚未导出或验证本次改动。

### 新机器从这里接着做

1. 拉取代码与LFS资产，先看本段、r2的 `ART_AND_BEHAVIOR.md` 和r3的 `README.md`。新造型以 `AI_optical_curator_hero.png` 为准，打印以 `AI_print_peak_correct_scale.png` 和r3三阶段特写为准。r2的 `draft_print_bad_disc_scale.png` / `superseded_claw_proportion_study.png`、r3的 `04_recovery_draft.png` 均是弃稿。
2. 先做新AI末端、较大六片盘匣和上部机构的三维源，再校验路径；建议新建兄弟源文件保留旧试制。底座外径2.74、高.670608不变；新建模初值唱片.84、小唱盘.90，约93%直径覆盖。六片储存、抬升、水平转运和大机头的可达/扫掠尚未验证；不能直接整体缩放旧模型就完成。
3. 机头拆成瓷壳、镜筒、真实快门叶片/驱动环、黑光学面、像素发光层、可独立定向的吸附器和可见连接。用户要求原子之心的曲面与机械工艺；别退回细杆+球体的原型外观。
4. `record_player.gd` 现有所有权/安全逆序可复用，但目前驱动三指爪。改成光束承载后，需保留同一片身份、等待落稳再关场、面部与投射器独立姿态、随机待机表演让位于操作。新尺寸必须重新计算/验证，旧解析测试不是新尺寸的穿插验证。
5. 按r3分层制作吸附、解码、构建和回收；实际三维骨架/细丝负责体积，纹理只做强度调制。旧 `record_visuals.gd` 和 `surface.gdshader` 的简单打印是被拒绝的基线，不能仅把新图贴上去就称实现。白金接合边/微粒的峰值与封合一致，完成后清零，颜色改动联动所有光/粒子/局部灯。
6. 保持不同实体控件玩法。`g_operator.gd` 是旧书的遗留浮动面板，当前 `available()` 对record_player返回false。`service.gd` 在唱机模式隐藏tooltip/toast。不要运行 `tools/configure_g_archive.py` 把界面文案恢复为“书页/下方编号”。
7. 完成真实模型后再录制连续EXE演出、做新尺寸的网格扫掠检查、首次特效预热、帧时间、打断与退出检查；逐张对照图稿检视真实截图。用相同take烘焙Blender源动画。用户要求看得到建模/动画过程；旧 `live_record_player.py` 是本机临时预览工具，不是新机器上已运行的服务，不能沿用旧PID。

### 恢复与可重复命令

从仓库根目录执行，机器上路径自行选择，不能照抄本机H盘安装路径：

```sh
git pull --ff-only
git lfs install
git lfs pull
git lfs fsck
```

当前制作环境为Blender 5.2.1 LTS、Godot 4.7.1、Python3.10；源文件和纹理由LFS保存。打开前检查 `.blend/.glb/.png` 不是短文本LFS指针。本轮所有图片已复制进仓库，不依赖上一台机器的Codex临时生成目录。

只为复现旧功能基线时：

```sh
godot --headless --editor --path app --import
godot --headless --path app --script res://../tests/collection/record_player_state_qa.gd
godot --path app --script res://../tests/collection/record_player_take.gd -- --bake-only
blender --background --python blender/collection/bake_g_record_player.py
```

上面的take依赖实际渲染器，`--bake-only`省略截图但不等于无GPU。原始73MB的 `review/G_record_player/record_take.json` 不纳入Git，用上述命令重建；已有烘焙 `.blend` 本身已保存完整关键帧。模型/元数据哈希必须与take一致。Blender重建/烘焙会写指定源，先保存新机器上的人工改动；新AI请另建源，不要盲目重跑旧整机建模脚本。

Windows功能包可用 `tools/build_windows.ps1 -GodotPath <本机Godot控制台程序> -OutputPath <staging路径>` 重建；不要覆盖原B/HELIOS。旧书G_archive系列和原图/失败检查保留为历史追溯；其失败报告/成功报告均不能代表新AI已验收。

提交前在当前工作树复核了Godot 4.7.1无界面导入、`record_player_state_qa.gd`（退出码0）、六张新特效PNG的可读性及两份运行素材副本哈希一致性；Git LFS fsck通过。没有在交接前重做Mac验证，也没有把未制作的新AI/新特效写成已验证功能。

---

## 最新追加：采用球形快门 AI + 光束取片，爪子方向被替代

用户提出机械臂末端用球形 AI 形象，像相机快门一样眨眼、镜头内显示像素表情，以光束悬空吸附唱片；待机可以歪头搞怪。已按这个方向出图，详见 `production/G_record_player/r2/ART_AND_BEHAVIOR.md`。只完成新的图稿与首张专用光学纹理，尚未将这一轮 AI/新尺寸/新观测塔/新特效制作到模型或 EXE。

当前参考 `AI_optical_curator_hero.png`、`AI_print_peak_correct_scale.png`、`AI_iris_personality.png`；`draft_print_bad_disc_scale.png` 唱片误画成整个底座，明确弃用；`superseded_claw_proportion_study.png` 是已被替代的爪式研究。光学图集 `app/assets/collection/art/G_AI/optical_field_atlas.png` 已生成，尚未接线。所有提示词和出处在 r2/prompts.json。

新目标唱片 .84、小唱盘 .90（原 .50/.80），底座仍2.74/.670608，六片任何状态尺寸相同；数值仍须三维布局校验。AI面部与下方吸附器独立万向机构，歪头不能带歪盘；新介质半径/头部体量需重新做路径、可达性、避障和拆解。首先按 r2 建模/特效，不继续修旧爪子。检查最终日志确认旧 `bake_g_record_player.py` 已在停止请求前完成3523帧/111对象烘焙，保存的是旧爪式比例与新实体控件；`blender_bake.json` 已生成，但尚未逐帧视觉验收。它不是新AI版本，也不能据此交付为用户认可的模型。

---

## 最新：用户拒绝首轮唱机的比例、质量和打印特效，正在重做图稿

用户刚明确指出：整台唱机上部太小、唱片太小不能铺满小唱盘、打印建筑时的特效差，整体模型质量完全无法接受。不能以功能通过为完成，也不能将当前 staging 包升级为正式验收版。正在用内置 image_gen 重新建立大体量上部和完整打印特效目标；旧底座尺寸不变。

- 前一条反馈已实现：移除 G 唱机黑色浮动 UI，关闭其 tooltip/toast；实体五控件为编号选片轮、参数滑块、按住演绎压板、转/停拨件、拆/装双向拨件，保留两端电源/退出。滚轮双向选片，六档循环；拆装左右半边可直接点，动作有机械行程与状态灯。
- 新物理控件源 `blender/collection/build_g_record_controls.py` → `G_Record_Controls.blend` 与 `app/assets/collection/record_controls.glb`，140 原始网格合为15刚性组。`record_console.gd` 只驱动机身灯，无 Canvas UI。
- `tests/collection/record_console_native_qa.py` 已在 staging `MagicDesk-Record-Console.exe` 沿真实窗体→桥→实体射线回放全部六件、调节/按住、循环选片、起停、拆装、休眠及持片中退出。记录在 `review/G_record_player/native_console/`。11145 呈现帧，59.10 FPS、P95 21.09ms、全程最大238.91ms（含首次载入）；原生错误0，renderer正常退出0。**这些是功能证据，用户仍拒绝美术结果。**
- `record_take.json` 最新3523帧，保存GLB和metadata双哈希，当前 `.50/.80` 旧比例。`bake_g_record_player.py` 正在烘焙该旧比例源，保留为迭代历史；不可当作用户认可的新精修。正式 `dist/MagicDesk.exe` 尚未替换。本轮未推送。
- 接下来必须先看新的比例与特效图，再实施对应几何/专用素材/时序；同时需要做新尺寸的转运空间校验。最新用户不接受在当前小模型上加几圈光就称为AAA。

---

## 正在制作新唱机（用户已说“按新的这个处理吧”）

正在实施六片实体媒体、固定取片口、双连杆+回转肩部+翻腕夹爪、独立小唱盘、唱臂读取、同盘逐层打印、60 秒一圈的展示。不能再回到书本方案。新模型/代码尚未交付或推送，原 EXE 仍保留。

- 新模型脚本 `blender/collection/build_g_record_player.py`，输出 `G_record_player.blend/.glb/.json`，20 组可拆部件、6 张固定尺寸唱片、6 个花瓣槽。仅复用 G6 的六件藏品，删除整个旧书结构。金色/陶瓷为曲面与实体加工件。
- `app/collection/record_player.gd` 独立状态队列，6 张盘只有 slot/grip/platter 一种位置状态；倾斜盘先抬升 0.55 再翻平，落盘后夹爪和唱臂让开再打印；归片使用原盘。腕部在抬起后恢复旋转角；持片中取消会安全反向归槽。
- 新停放姿态加入肩部回转，PARK 虚拟盘中心为 (.44,1.95,-.30)（Godot），使两连杆横向展开并露出金色关节。臂长 .62/.68，夹爪两节 .185/.145，打开端点 r=.31/y=-.17，夹紧 r=.270/y=-.15。
- `record_visuals.gd` 和 `surface.gdshader` 新增可选 record_print：局部唱盘坐标下逐层构建，上方金属骨架为蓝色档案线，下方实体材质；没有用整件缩放代替打印。实体唱片与打印根挂在同角度 pivot 上，底座与取片机构不跟着慢转。
- 修复过隐藏的零长度打印光线产生零 Basis：record_visuals.segment 要保留最小非零长度。最初 take 因此报错，已停止；最新 take 必须重跑。
- 首轮实际图在 `review/G_record_player/`，已发现原停放姿态太正、唱片细纹闪烁、唱臂缺升降杆；已改肩部 yaw、正面红宝石伺服盖、实际升降杆、少量几何主纹+抗锯齿径向材质。最新模型重建已完成/需看 build_model.log。
- `g_operator.gd` 复用为中文直接选片/参数/动作 UI；唱机版收窄到 572 px，显式停止慢转；实体第 3 控件改成可单击的两档慢转/停转。旋转只控制唱盘，旧 host 自动转保持关闭。Native reset 已针对唱机保持静止。
- `record_player_state_qa.gd` 的早期所有 6 张盘、各阶段退出、唯一性、可达性、60 秒/圈已通过。后来 PARK/yaw/手指长变化需重跑。`record_player_take.gd` 记录实际模型/部件/机构/控件/特效并截 alpha 紧边，最新停止旧错误 take 后尚待重跑。
- 新增 `extract_g_curiosities.py` 可把六件藏品抽成独立 `G_curiosities.blend/.json`，避免最终依赖旧书；尚待执行并将新模型脚本切到该源。
- 新增 `live_record_player.py`：Blender 读取 review/G_record_player/blender_control.json，reload 用追加场景保留旧场景，支持 frame；尚待启动。已有临时可见预览 PID 24352（可能变化），它不会自动同步文件。
- 需要继续：重跑生成/导入/实际 take；记录静态及运动三角网格碰撞（尤其抬片翻腕、夹爪与盘边、唱臂与藏品）；烘焙含打印材质的完整 Blender 动画；执行原生 EXE 输入回放与真实视频/性能检查；最后部署可评估 EXE 与同步 Git。
- 原生关闭 watchdog 从 9 秒改为 14 秒，为安全归盘留出时间；F/B 正常退出不会等待 watchdog。不要用强退代替归位。

---

## 最新方向：取消方形书壳，改为原子之心式自动换片唱机（优先）

用户最新明确认为书页扫描没有吸引力，大块方形书壳没用；希望围绕中间的黑色档案芯片，表达“每片实际拿出来扫描”，认为古怪、原子之心风格的自动换碟唱机更合适。**暂停书本几何、书页翻转与旧书 EXE 交付，不要继续强修方柜。** 六件藏品可复用，但用户此前对精度的批评仍有效。

当前正在用订阅内置生图建立“六瓣换片机”的形态/动作设计，文件放 `production/G_record_player/`。方向：六片黑色档案盘、陶瓷骨架、香槟金关节、仿生拾取爪、细长唱臂；明确链路“选片 → 从槽中取片 → 落到唱盘 → 唱臂读取 → 唱臂退开 → 藏品显现”；换片/休眠将原唱片送回原槽。共享底座尺寸继续固定，默认静止、显式暂停、具名选片与动态动作说明沿用。

用户随后进一步指定：**唱片不撤离；模型像现有切换模型一样，从这张片上逐层打印，打印后与唱片共同慢转。** 已按默认约 60 秒/圈、操作时自动停转、始终可见的停转按钮记录。底座、盘匣和机械爪保持静止。换片先反向打印回收，再停盘、夹取、归槽。对应 MECHANISM_PLAN 已更新，正在补同盘打印分镜。

书本返工文件全部保留作为历史；其测试不代表新唱机已完成。新唱机尚未建模。旧线上 / dist EXE 仍 0.3.1；中间包仅在 dist/staging。任何“已完成”“与原图一致”必须有真实模型与连续运行证据，不能再次只凭功能接口宣称。

---

## 正在返工：G 藏品书（用户拒绝 0.3.1 的视觉与玩法）

本段优先于后文。当前工作尚未交付、尚未提交或推送；正式 EXE 仍为此前 0.3.1。用户明确指出：持续旋转无法直观停止、选页/按钮不明、对孔后只有楼梯回报很差、休眠不像合书；随后要求改成类似自动换碟机的书页档案播放器，每页展示不同内容。又明确批评书像方柜、六件藏品几何与图稿差距巨大，要求金色、精修和完整出入场；最新追问整机“书→读入→展台→藏品”的顺序必须讲得通。

- 已将用户正在运行的旧 G 停转，连续 probe 角度不变；旧 EXE PID 14488（可能变化），QA 控制文件 `review/G_complete/live/commands.txt`。勿再用旧 `--select-only` 最后自动开启旋转。
- 新交互代码 `g_operator.gd`：常驻中文铭牌、旋转/停止、正面、六页选择、参数滑条、按住动作、播放暂停、休眠/拆装/退出；原生鼠标区域已接入，实体旋钮也增加单击换页。默认 G 静止，操作时自动停转。尚未完成新 EXE 的原生回放。
- 新控制器 `g_archive.gd` 继承旧 G 机构接口；按页自动读取，六件不同的实体三维藏品，取消对孔任务。最新加入“前面的页先翻到侧方，让选中页露出 → 展台就位 → 读头扫描 → 重建 → 播放”的有界顺序；旧物件/读头未退完不移动书页。`presentation` 将同组前页停入分层侧架，罩壳开幅已同步加大，必须进行实际网格连续检查。
- 设计基准 `production/G_archive/images/G_archive_flow.png`、`G_six_specimens.png`，均为订阅内置生图。用户不认可当前试制，不得把通过功能测试称为视觉完成。详见 `VISUAL_REWORK.md`。
- 模型链：`build_g_archive.py` → G_archive（被批评的方柜试制，保留）；`refine_g_archive.py` → G_archive_refined（G5，拆除柜墙、圆角厚页、开合弧形书脊、四片独立曲面蝶翼）；`refine_g_specimens.py` → G_archive_detail（G6，其余五件细化）。G6 必须在最新 G5 构建结束后重建。三套 `.blend/.glb/.json` 均保留，不覆盖旧 G_complete。
- G6 内容：钟塔（透空齿轮/指针/钟摆）、机械蝶（四翼/骨架/红釉嵌饰）、帆船（曲面船壳/双帆/浪形支架）、花园（曲面花瓣/驱动件）、星轨仪（嵌套轨道/红核）、阶梯（上行/顶部转接/中央下降/下部转接的连续回程）。新 rig kind `traveller_return` 已接，悬摆幅度已限位，读取出场会先展开各自机构。
- 最后实际渲染在 `review/G_archive/reference_rework/`。`render_g_rework.py` 读取 G5；修复了 Blender 空父级 hide_render 不会隐藏子几何的错误，避免六件叠在一起。`bake_g_archive.py` 也已修复逐级显隐。最新渲染书+蝶已正常，但不能宣称与图稿完全一致。正在 Blender 打开的返工预览使用 `show_g_rework.py`（PID 46152）。
- `g_archive_take.gd` 可传 `--model=G_archive_detail`，最新改成 2351 帧并加入读入/重建/合书顺序断言，尚待运行最新模型。`bake_g_archive.py` 仍写死 G_archive 路径，需要参数化后再烘焙最新 G6。新 `g_archive_native_qa.py` 已写，旧固定 parts==17 需改为新元数据 14。
- 当前注册表指向 G_archive 试制，最终应改到验收后的 G_archive_detail。native 版本号暂改为 0.3.2；仅生成过旧交互中间包 `dist/staging/MagicDesk-G-UX.exe`，不能交付这个包。现有用户 EXE 尚未替换。
- 原有 F/B 必须保留。Apple 暂停，下一款 I 暂不开展。Computer Use 的 Node 内核仍报 os error 3；只用应用自带 native 回放，未声称物理鼠标自动化。

接下来先顺序重建 G5/G6、导入，运行整机动作链录制，检查翻页侧架/封面/展台的穿插，烘焙源动画，再验证新 EXE 的全部具名操作、睡眠闭合和性能。视觉精度仍未获得用户认可，禁止提前报告“完成 / AAA”。

---

## G 专项更新：0.3.1（优先于下方历史记录）

用户要求 F 之后按相同流程制作下一款，本轮推进 G「折维书匣」。后续依次为 I/J/K/L/M/N；没有自动开展下一款。仍只使用订阅内置生图，不调用或探测外部图片接口。

- 视觉目标与素材在 `production/G_complete/`：六阶段分镜、专用 2×2 光学图集、原始提示词和出处；三维记忆浮雕由 Blender 实体轮廓组成。设计图、Cycles 参考与 EXE 实机结果分别标注。
- 新源 `blender/collection/G_complete.blend`，原 G 保留。六片真实通孔瓷页、两扇先侧移再转开的封面、可见伸缩支撑、独立写头、定位销、刻度与书脊。统一底座不缩放，13 组拆装。
- `g_instrument.gd` 独立于 F 的 `play.instrument`，通过 `play.g_instrument` 接入；不要把两款的物理分支混用。G 用有行程限位的刚体运动学及真实世界变换下的射线/孔面交点，接受角 1–3°，不是自由摆或电磁仿真。
- 每页保留折角和记录进度；索引轮支持滚轮/横拖，折角滑块支持 Shift 微调，按住写入、松手续写。换页恢复滑块显示，对准表只读。已有记录不因切页擦掉。
- 发现并修复原生可变帧率下进度停在 0.999960 的问题：写入条件必须 `<1.0`，不能用 `<.999` 提前停止，却又要求 `>=1.0` 才触发高潮。`g_endpoint_qa.gd` 对四种极小剩余量回归。
- `g_visuals.gd`：孔壁焦散、扫描细光、刻纹、写头附近的重力微屑、实体 28 层楼梯/塔柱/拱廊投影，以及回收。28 层轮廓在运行时合为一个网格，用高度控制显现；Blender 保留分层可编辑源。全部材质与实例先在隐藏视口预热。
- 收拢顺序：回收投影 → 退写头/定位销/选页偏移 → 合页 → 合封面；拆解需先合匣，组装回保存的位姿。关闭中途动作正常走归位链。
- `g_visual_take.gd` 记录 1441 帧 / 30 FPS；`bake_g_take.py` 烘焙机构、实体控件、24 个光学素材面、64 个微光实例和声音。先运行 `complete_g.py`，再记录 take，再 bake；不要将没有烘焙的初始源当完整动画。
- 检查资料：`review/G_complete/` 的状态机、终点回归、实际瓷片 BVH 检查；`native/` 是独立 EXE 的原生输入回放、截图、原速视频与最终帧时间。测试通过不等于用户已确认达到 AAA 视觉目标。Windows 构建更新，Mac 未重新导出验证。
- 最终 EXE 记录：G 就位后 59.66 FPS，P95 20.808 ms，最大 27.460 ms；全程含初次载入为 57.82 FPS、最大 236.415 ms。合批前 G 为约 54.69 FPS / 最大 65.999 ms。窗口呈现无错误，正常退出码 0；共享底座保持一份。最终可执行文件 SHA256 为 `E608CC490C3E815381C1C6211BD81AA3B1BC6B6298D88825F85001361C647E01`。
- 当前 Computer Use 的 Node 内核仍报“failed to write kernel assets / os error 3”，没有据此声称已进行物理鼠标自动化；实际 EXE 使用程序自带的 native 输入回放接口。

下一轮首先检查 G 的最终实机图和用户反馈；若继续下一款，按同样的分镜 → 美术资产 → 模型/动画 → EXE 验证流程推进 I「回声海螺」。

---

## F 专项更新：0.3.0（优先于后面的 0.2.x 记录）

用户明确要求先完成 F，再推进下一款；特别追问物理是否正确、说明挡操作、旋钮侧视费劲，以及特效要有与模型契合的创意。当前轮次没有开展 G/I/J/K/L/M/N 的上部精修。

- F 改为真正闭合四连杆：下支点移到 C 形骨架脚部，杆长 0.82 / 1.01 / 0.50，固定支点高度差 1.706。两只配重都有球铰悬挂，重力、惯性、约束反力、预载扭簧与摩擦制动共同求解。
- `app/collection/f_dynamics.gd`：两只悬挂与主轴耦合的 RK4 240 Hz 求解；世界重力 9.81，显示倍率纳入长度换算，展示旋转考虑支点加速。模型是集中质量与刚性轻杆假设，不是材料/制造仿真。详细推导和验证见 `production/F_complete/PHYSICS.md`。
- `f_instrument.gd`：稳定才触发校准，持续操作时不抢先发动；缓慢小幅拖动也可重新触发；失稳或中断时平滑回收。收纳夹爪先控制住悬挂，再折回。旧“朝目标角度弹回”的 F 逻辑已由专用分支替代。
- 用户进一步问到“是否用了拉格朗日钟摆数学模型”。已另建五广义坐标的独立欧拉—拉格朗日验证器：96 组状态全部通过，最大加速度差约 1.97×10⁻⁵。运行时是等价的约束消元，不是套用经典串联双摆轨迹。验证包含运动支点、摩擦与磁力矩，静摩擦/止挡另验；见 `lagrange_equivalence.json` 和 PHYSICS.md。
- 旋钮支持滚轮、Shift 微调、屏幕空间左右拖动；侧视命中增加 9 px 容差，档案入口仍优先。提示需停留 450 ms，在整排控件上方；按下/拖动/滚动隐藏，状态 toast 不与提示重叠。Windows 非焦点滚轮也读取实际 Shift 状态。
- 模型 `F_complete.glb` / `F_complete.blend`：18 组拆装，双悬挂关节、独立刹车盘、同轴连接、可见扭簧与输力管路。接收盘先升起后滑入，反向收回，避免穿过下沿瓷壳。旧 B、F、F_refined 源文件与旧 HELIOS EXE 保留。
- 图稿与实际资产：`production/F_complete/images/` 有完整分镜与“力线示踪 → 悬浮刻度 → 校准回写”创意图；全部为订阅内置生图。实际图集 `app/assets/collection/art/F/field_atlas.png`，专用 PCM 校准声 `calibration.wav`，原始提示词与制作脚本保留。没有调用或探测外部图片 API。
- `f_visuals.gd`：112 个三维实例中包含 28 枚直金属刻度针，其余为细小微屑；有贴图驱动的场线、铅垂测量线、盘面干涉波和沿标尺回写的光点。实际发光接点与局部照明关联。没有把默认粒子当最终美术。
- Blender 动画由 `f_visual_take.gd` 的同一物理数据烘焙，1321 帧、30 FPS；58 个机构/控件对象、112 个场实例，以及场线、图集波纹、回写光点和声音。`bake_f_take.py` 可重复执行，会先移除自身旧的生成场集合。
- 性能处理：F 的点击代理用简化形状，动力学由专用约束求解，不为每个细节烹制三角碰撞；公共底座碰撞形状缓存；全部 F 效果池/材质在隐藏视口预热。首次载入仍需以实际帧时间记录判断，不能只凭平均 FPS。
- 又将公共操作匣的点击形状缓存，并在原生窗口首帧出现前预热操作匣与共享底座材质；`COLLECTION_COMMIT` 时序已细分进载入统计，用以定位首次切换峰值。
- 最终定位到预热后共享底座网格失去强引用，切换时重新读入。保留网格/纹理缓存后，交接 CPU 总耗时从约 801 ms 降到 9 ms。最终录制：全程原生呈现 58.6 FPS（含首次加载，最大间隔约 197 ms）；F 就位后 59.62 FPS、P95 20.52 ms、最大 31.22 ms。没有 `UpdateLayeredWindow` 错误，运动中关闭正常退出。详见 `review/F_complete/final/delivery_report.json`。

验证与运行资料集中在 `review/F_complete/`；`final/` 为最终独立 EXE 的原生输入回放、截图和帧时间，`production/F_complete/index.html` 为单款图稿/实机对照页。技术测试、实际网格检查和视觉判断分别记录，不能把任何一项替代其余项目。

注意：`complete_f.py` 重新建几何后需运行 `f_visual_take.gd --bake-only` 和 `bake_f_take.py` 才有完整源动画。`physical_take.json` 是可再生成的中间数据。Mac 尚未导出/验证 0.3.0；不要把 Windows 证据套用过去。

---

## 2026-09-09 Windows 更新：0.2.2 交互评估版（优先于下方旧 Mac 交接）

用户最新要求：所有图片只用订阅自带内置 image_gen，不调用、查询或探测 apilink/外部图片 API。官方已有 Flare/Sunburst，但当前工具没有型号选择或可核验返回，所有新图只标内置生图。

- `production/interaction_refinement/index.html`：八款结构/控制概念与实际 EXE 画面对照；原图、提示词和 manifest 已归档。不是八款精修完成。
- `dist/MagicDesk.exe`：新的独立 Windows x64 交互评估版；原 `dist/HELIOS.exe` 保留。使用 `tools/build_windows.ps1 -GodotPath <Godot 4.7.1>` 构建，默认不覆盖 B。
- 集合现在在 Windows 正常运行初始化，原生窗体支持实体舱罩、铭牌、滚轮翻页与控制器连续输入。M/N 已通过导出 EXE 的实际入口选择回放；下方“未接入”的旧判断已被本轮证据更新。
- 新控制器由 `blender/collection/Control_Library.blend` / `control_library.glb` 制作，旋转、持续按住、滑杆、摇杆、档位开关、只读仪表各有输入。不是换外形的统一点击。
- 修复新操作匣继承旧匣缩回位置而埋入白色面板；安装点使用保存的固定基准。原生桥 HLS5 帧携带实际输入区域，拖控件不拖窗口。
- K 刻针改为锁定档位，松手后可以再操作手摇柄；M 公共“组装”使用 stow，不误走旧的行星重构动作。
- F 开始逐款实体精修：`blender/collection/F_refined.blend`、`app/assets/collection/models/F_refined.{glb,json}`；原 F.blend/F.glb 不动。新增双齿轮、弧形游标滑座、制动卡钳、轴承、卷边瓷壳、泪滴配重。5 个专用节点由真实控制驱动，GLB 刚体合批 494 → 31 网格；源文件仍保留分件。制作脚本 `refine_f.py` 直接读原源文件，新建兄弟文件，不运行旧整模脚本。
- F 源动画保留旧开合/拆解，并在 385–529 帧增加差动/制动操作演示；553 帧收拢。原 B 源文件、模型、EXE 和公共底座尺寸均保留。

验证：`tests/collection/gesture_logic_report.json` 的 26 项控制因果/机构/拆装回位检查通过；`review/interaction_native/release/interaction_report.json` 的 74 项在导出 EXE 自身窗体输入处理 → TCP 桥 → 3D 射线上回放通过。覆盖八款铭牌、控件命中、按住/释放、K 单鼠标刻写、M 坠入/重构、组装不退出。Computer Use 的运行环境初始化失败，因此这是应用自身输入回放，不能称为人工鼠标录像。

连续实机原速视频：`review/interaction_native/release/review_walkthrough.mp4`，从完整 `native_walkthrough.mp4` 只裁去首尾等待，无加速。真实截图同目录；目录中的 `F_archive_scan.png` 也暴露了当前归档线框仍偏弱的问题，不要据此宣称特效已达标。

本机 RTX 3060，录制期间平均 59.04 FPS，P95 帧间隔 21.71 ms，最长间隔 786.71 ms；统计包含首次装置切换/载入，未定位该最大间隔的具体阶段，不能说全程无卡顿。原生窗口 UpdateLayeredWindow 返回错误为 0。此轮没有重做 B 的蒸汽。

**接下来仍必须做：** F 对照图稿继续完善体积、机构连接与完整招牌演出；G/I/J/K/L/M/N 上部仍为旧第一版，逐款精修；K 图稿按新锁柄补一致性修正；公共扫描/重建光效仍偏弱，操作匣旋转鼓交换仍未完成；首次切换的大帧间隔继续定位。Mac 尚未重新导出或验证 0.2.2，不能把 Windows 证据套到 Mac。

---

## 旧 Mac 交接记录（历史背景）

更新时间：2026-09-09。用户要求先推送 Git，改到另一台设备继续。**这是开发中交接，不是完成或发布。先读本文，再读 AGENTS.md、PRODUCTION_ART.md。**

## 用户最新判断与优先级

1. **M、N 未加入用户实际使用的 App。** 源码注册表虽然列有 M/N，资源目录也有模型，但这不能替代用户可见、可选、可运行的接入结果。接手时必须沿真实 App 的入口确认这两款可见并可切换；未确认前按“接入未完成”处理。
2. **基本上除了 B，其他模型都有各种问题，需要一个一个精修。** 不能把有 GLB、基础开合/拆装、测试通过写成成品完成，也不能只改材质就宣称完成了所有动画。
3. 用户允许使用 **image2.5 sunburst** 出图精修。下一设备先确认该名称对应的可用模型、工具或 API 配置；现有本轮图片使用的是内置 `image_gen`，没有证据表明已调用 image2.5 sunburst。不要混淆或擅自声称已使用。
4. 当前最直接的不满是**切换入口外形和定稿不一致，切换动画/特效、卡牌出现与收缩的演出没有按设计完整交付**。先把这一条公共流程做对，再逐款精修。不要用加文字提示或让用户按 Tab 来替代设计中的实体入口。
5. 首批范围 F、G、I、J、K、L、M、N；原 B 保留。E2/E3 动物替代方案暂缓，A/C/D/E/H 不加入首批。

## 不要丢掉的设计约束

- 同一个 App、同一份真实底座；不得按生成图为每款改变底座大小。原 `BASE_FIXED` 本体外径 **2.740000**，总高 **0.670608**，来自真实 GLB 顶点。不同按钮等附属件可有各自外伸范围，但公共底座外形必须一致。
- 原子之心的复古未来工业/仿生机械方向：奶白瓷壳、镍铬金属、石墨内构、克制的红色细节。用户要求按 AAA 游戏的材质与动效标准制作，避免错位、错误拆解、穿帮。
- **入口是明显的奶白弧形舱罩，带金属包边、接缝和机构，属于底座的一部分。** 之前把它做成薄金属盖板/极隐蔽压条是做偏了。用户明确指出设计里有明显外形。整个舱罩应可点击；不要另加普通菜单按钮或左右箭头。
- 入口压入解锁 → 舱罩开合 → 有厚度、有支撑/铰链的轨道伸出 → 实体烟色玻璃卡牌逐张翻立 → 选中牌读取反馈/沿轨道传光 → 模型收势 → 扫描归档/线框回收 → 新模型重建 → 操作匣就位 → 卡牌和轨道按原路径收回、舱罩闭合。
- 操作匣可以随装置使用不同形状、数量与行为的实体控制器，不要硬套 B 的七圆钮。
- 每款动作与特效必须先有图稿，再制作专用贴图/遮罩/必要序列或 Blender 资产；Godot 负责驱动与合成。概念图不等于已经制成可用素材，更不等于实机达标。

## 当前代码、构建与证据必须分开看

| 对象 | 当前真实状态 |
| --- | --- |
| 原 B | 原有 HELIOS，保留原 GLB 和 Blender 主文件；不要覆盖它们。 |
| F/G/I/J/K/L | 有第一版 Blender/GLB、基础动作与简化特效；用户认为均有问题，逐款返修，未通过美术/完整动画验收。 |
| M/N | 有源码资源和实验逻辑，但用户确认未实际加入 App；交付接入未完成。 |
| 本机 `dist/macos/MagicDesk.app` | 上一版 **0.2.0**，在原设备本地，未纳入 Git。不是本次入口返工后的成品。 |
| 当前工作树 | 版本号已改 **0.2.1**，公共切换流程正在重做，**尚未导出替换 0.2.0，也未完成最新实机回放**。 |
| `tests/collection/REPORT.md` | 旧 0.2.0 的工程报告，245 运行/68 输入检查只是当时的有限技术证据。不能用它反驳用户反馈或证明当前工作树已通过。 |
| `review/selector_rework/r1/` | 本轮切换返工的第一轮真实渲染：可点击舱罩、卡牌部署、扫描、重建和收回流程有中间帧，测试脚本跑过；视觉仍不达标。 |
| R1 之后的最新调整 | 舱罩改为更圆的鼓面、改用绕竖轴开合；修正扫描贴图采样中心；加入透明深度预通道以减少线框内部叠成一团。**这些调整尚未重新回放确认，可能还要修。** |

### 本轮已经承认并纠正的表述

先前把“代码已接入/基础测试通过”概括成“功能已打通/所有模型与动画已做”，说得过满。实际：八款第一版结构与基础开合/拆装有代码，但完整的招牌演出并没有全部按分镜做好。**不要再只报测试数量或锁屏原因，必须展示用户实际 App 中的结果。**

## 各款尚需精修的内容

| 款式 | 已有实验实现 | 精修和验收重点 |
| --- | --- | --- |
| F 拉格朗日天平 | C 脊、连杆、配重、开合/拆装、光垂线 | 造型与图稿差距；制动、失衡、越过平衡点与回稳的独立动作；目前招牌触发不少只是提速/亮度变化。 |
| G 折维书匣 | 六页与封盖、伸缩支撑、光格 | 页片/铰链细节、索引针动作、真正的空间重写演出；不要只有翻开后的一张发光贴片。运行网格按刚性父节点由 510 合并到 74，源 .blend 仍保留分件。 |
| I 回声海螺 | 六段壳、导杆、共振口和波纹贴图 | 螺壳轮廓、内构、喉闸、膜片振动与回声往返的完整动作；目前波纹主要为贴图缩放。 |
| J 汞芽温室 | 三芽、六叶、套筒主干、导管脉冲 | 花瓣/枝叶造型和动作层次；萌发、授光、回流、收芽的独立节奏。 |
| K 星图刻写机 | 双盖、两卷轴、三刻针、星图带贴图 | 实际刻写笔画、针尖接触/抬针、走带和回车时序；目前很多是循环位移/纹理移动。 |
| L 三相窥镜 | 三镜颈、动态对焦和光线 | 头部造型、虹膜、观察/对焦/到位动作；目前主动作与招牌动作区分不足。 |
| M 星噬仪 | 三颗行星公转、内落/拉伸/吞噬、纹理重构的实验逻辑 | **先验证 App 接入**，再精修硬件、三颗行星与吸积效果，不能又变成与 B 重复的蛋形装置。 |
| N 裂隙回廊 | 不规则瓷骨裂口、膜片、喉道、两段互补裁切探针 | **先验证 App 接入**；加强怪诞造型、连通/穿越的清晰感，保证是一支探针穿过去，不能做成普通圆门。 |

## 文件入口

- `app/main.gd`：现有 B 宿主、Mac 透明窗口、输入、公共入口接入。当前集合在 macOS 普通运行模式初始化；Windows 原有导出链不能默认视为也已支持集合。
- `app/collection/service.gd`：注册表、公共舱罩/卡牌、读取反馈、载入/收势/扫描/重铸/收回状态机、操作匣。新状态包含 `reading`、`scan_rise`、`sealing`；`selector_wait` 会先收拢模型，`pending_action` 会等卡牌收回再执行动作。
- `app/collection/module.gd`：独立上部层级、101 个机构采样、可逆开合和拆解路线。glTF 必须用 `Basis(q) * Basis.from_scale(s)`，不能改回全局缩放顺序。
- `app/collection/effects.gd`：八款实验动效。大量招牌动作仍简化，详见上表。
- `app/collection/transition_vfx.gd`、`archive_*.gdshader`、`plaque_etch.gdshader`：本轮新增的扫描圈/发射光束、整模线框、刻线卡牌等。
- `app/assets/collection/registry.json`：声明清单与操作映射；条目存在不等于用户 App 已交付。
- `app/assets/collection/models/{F,G,I,J,K,L,M,N,S}.{glb,json}`：运行资产；`S` 为共用切换机构。
- `blender/collection/*.blend`：可编辑源；`build_models.py`、`geometry.py`、`build_selector.py`、`build_base_frame.py` 为制作脚本。重跑前检查是否有后续人工修改，避免覆盖。
- `concepts/shared_base/机械档案匣.png`、`归档与重铸.png`：原设计参照。图中早期圆形菜单键不是要求恢复的重点，重点是明显的舱罩外形与机械演出。
- `production/selector_rework/入口与卡牌动作.png`：本轮补画的动作对照稿；`prompts.json` 保存内置 image_gen 提示词。
- `app/assets/collection/art/archive_atlas.png`：本轮实际光效素材，2×2 图集。左上线条中心实测在 tile Y≈**0.450**，右下光点 Y≈**0.432**，不能想当然以 0.5 取极窄样本，否则光束几乎不可见。
- `production/batch1/art/`：八款动作图、已有资源清单与提示词；`concepts/cosmic_devices/current_manifest.json` 指向 M/N 最后采用的图。
- `production/selector_rework/baseline/`：返工前的 S 源脚本、GLB、采样 JSON；`production/batch1/baseline/` 保留既有脚本和未合批 G 等基准。

## 最新已知问题，下一步从这里开始

1. **先导入并回放最新 S 和切换流程。** `review/selector_rework/r1` 是最近一次已看过的渲染，但之后圆润舱罩、竖轴开合、贴图中心修正、`archive_depth.gdshader` 尚未重验。不要拿 R1 图冒充当前代码的结果。
2. R1 的舱罩仍像薄弧板、打开像竖起的叶片，与参考的厚圆舱罩不够一致；最新几何就是针对这个差距修改的。
3. R1 扫描光圈/光束太暗（取样中心错误），线框内部多层叠加成橙色团；最新着色器针对这两点改动，需确认透明深度预通道在 Metal/透明桌面窗口里有效且不会错误遮挡。
4. 核对 cowl、轨道、卡牌在**整个过程**的铰链连接、连续移动和干涉，尤其新轨道改成先穿出舱口再向左伸展，旧的收纳报告不能当新版本的动态证明。
5. 基座维持原网格尺寸；新增舱罩和扫描器是公共附属件，需复查其与 B 开合/旋转扫掠以及关闭按钮的关系。`production/selector_rework/helios_sweep.json` 仅为粗采样半径数据，不是完整碰撞证明。
6. 操作匣当前仍主要是收回/送出，**参考中的完整旋转鼓交换尚未实现**；不要用瞬间替换或强闪光掩盖。
7. 完成公共流程后，沿真实用户入口确认所有九款（尤其 M/N）可选可用，再按款逐个精修。不扩展候选范围，不一次把八款都标完成。
8. 更新状态文档与艺术库实机预览，旧 `production/batch1/WORKLOG.md`、`tests/collection/REPORT.md`、`concepts/runtime_preview/` 都含历史阶段内容，本文的最新用户纠正优先。

## 在另一台设备恢复

```sh
git clone https://github.com/cedricxugun/magicdesk.git
cd magicdesk
git lfs install
git lfs pull
git lfs fsck
```

已有 checkout 请先保存本地改动，再 `git pull --ff-only` 和 `git lfs pull`。必须有 LFS 实体文件；仅下载普通 GitHub 源码 ZIP 可能只有指针。

本轮环境：Godot **4.7.1 stable**，同版 macOS 导出模板；Blender **5.1.2**；原设备 Apple M5、arm64。Mac 构建不包含 Intel 架构。Python3、Git LFS、FFmpeg 可辅助检查和视频输出。图稿与已生成资产均随仓库保存，不依赖原设备的 `.codex/generated_images`。

`blender/collection/*.blend` 的外部图片路径已改为相对 checkout，检查记录在 `production/selector_rework/source_portability.json`。这是本次交接的路径整理，不是新的视觉验收；原 `blender/Helios_Incubator.blend` 保持不动。

从 repo 根目录，以下命令里的 `godot`/`blender` 替换为当地可执行文件：

```sh
# 先导入；不会构建完整修正版 App
godot --headless --editor --path app --import

# 正常启动；Tab 可用于诊断，但最终入口必须是可见舱罩
godot --path app

# 回放公共切换序列：实际点击舱罩和卡牌，保存十个阶段截图
godot --path app --script "$PWD/tests/collection/switch_sequence.gd" -- --capture="$PWD/review/selector_rework/next"

# 需要重新生成 S 时才运行；先确认没有人工修改需要保留
blender --background --python blender/collection/build_selector.py

# 从作者定义的源码生成八款；不是常规启动所必需，不要盲目重跑
# blender --background --python blender/collection/build_models.py -- F G I J K L M N

# 原来的技术回归，不能替代视觉验收
godot --path app --script "$PWD/tests/collection/runtime_qa.gd" -- --capture="$PWD/tests/collection/new_run"
godot --path app --script "$PWD/tests/collection/input_qa.gd" -- --capture="$PWD/tests/collection/new_input"
```

`tests/collection/switch_sequence.gd` 支持 Godot 的 `--write-movie <path.avi> --fixed-fps 30` 录制完整渲染序列；**当前尚未录制最终视频**，输出是确定性渲染演示，不是帧率基准或原生鼠标录像。

Mac 打包：

```sh
GODOT_BIN=/Applications/Godot.app/Contents/MacOS/Godot bash tools/build_macos.sh
```

构建脚本已支持 `MAGICDESK_APP_PATH` 与 `MAGICDESK_ZIP_PATH`，可先导出到 staging，验证后再替换正在使用的旧 App。当前 `dist/macos/MagicDesk.app` 与 ZIP 是本机生成产物，**Git 不携带**，另一设备需重新构建。不要边覆盖用户运行的 App 边声称他看的是最新版。

Mac Release 模板不支持用 `--script` 运行外部 QA。检查打包资源时，用同版 Godot 编辑器执行 `--main-pack <App/Contents/Resources/MagicDesk.pck> --script <QA.gd>`；原生 App 的真实点击和连续视觉仍需另验。

## 接手后的第一条工作指令

按最新用户反馈继续修复公共切换机制：以明显的奶白弧形舱罩为实体入口，完成可见的解锁、开合、轨道伸出、卡牌逐张翻立/读取/收回以及扫描归档/重建。检查最新未回放的几何与着色器修改，输出完整连续演示并在真实 App 验证。确认 M/N 可从用户入口实际使用，然后除 B 外逐款精修。可以使用经确认可用的 image2.5 sunburst 出图；不能把现有简化模型/贴片或历史测试数量作为完成凭据。
