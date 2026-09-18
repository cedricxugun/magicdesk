# F 2026-09-11 复修中

当前最新：日常Mac已更新为PCK9c09d6ce...，含本轮F控制、光效、引导和默认正面停稳；原生基本输入已通，详见HANDOFF顶部与review/macos_current/f_guidance_native/。F仍在材质/细节精修中，不称AAA完成。下方为按时间追加的历史制作记录，其中旧“锁屏、未入日常包”状态已被本段覆盖。

## 已做

- 90组20秒实际求解器对照，15组原参数均无持续止挡，稳态角度约-47.26到-37.36度。未采纳仅凭弹簧零位跨度而缩小力度的猜测；物理方程和力系数未改，源hash仍为2b2f1c2b9bd9a23f19d572d63675cadfc329bac5d9233f2aa2073f48079330bc。
- `lighting_and_controls.png` 是内置生图复修方向：中置零位、制动压板、三档磁偏置、微弱调节示踪与一次校准高潮。图中文字“mass compensation”不采用，实际是弹簧预载；图上的公共旋转图形不能覆盖已实现的独立右侧圆形全息入口。图稿不是精确齿数或装配证据。
- `f_instrument.gd`：碰旋钮但不改变值不再清空已有稳定进度；调节机构尚在移到目标位置时不能校准；需停手至少0.35秒并真正稳定，夹着刹车不能算合衡；失衡进度平缓退去。中断后不再把已消退场标成equilibrium。专项反馈检查通过；四连杆/悬挂/制动/回收/18组拆装回归也通过，最新脚本已补退出清理。
- `F_Refined_Controls.blend` / `f_refined_controls.glb`：独立F控件，不改通用库、G库或底座。轴孔、压板导销、拨杆球铰/横轴、拆装摇杆间隙有真实几何。125姿态固定件/活动件交检初轮通过；刻字版最终源需再刷新散列报告。
- F控制旋转方向已对齐：向右调预载顺时针，正磁偏置向上，正角误差指针向右、中央为零。表内琥珀灯呈现等稳/已校准，不以指针最边缘表示成功。
- 铭牌首轮像悬空小白卡，已改成按真实共享底座/操作匣表面投影的刻字；实际GPU首次投影17270个顶点均命中。字形是Blender中可编辑文本资产，Godot只负责贴合安装。最终源同步需导入GPU导出的贴合网格，不能只复制平面文本原型。已缩小字高并上移，避免跨到底边金属缝；最终刻字版17259顶点全部命中。
- 灯光/光效A/B：`review/F_complete/revision_20260911/lighting/`，同一物理姿态冻结比较。B候选为24/25/4三光、环境0.35、阴影尺寸0.35、SSIL半径0.30；光效分项乘数在review.json。已选择B照明+D光效写入F配置，但尚未导出新F App。`f_visuals.gd` 新增可选tuning字典，缺省值1保留旧表现；F元数据已显式采用本轮分项值。

## 接着做

1. 看最终刻字版近景，检查实际底座安装、舱罩开合/牌架扫掠、F旋钮/压板/拨杆/中心表针输入；源控件只测了其自身，不能代替安装验证。
2. 确认F独立照明和分层光效参数，检查弱待机→调节→制动→稳定→高潮→回写→取消/关闭；对照新图，不仅调整一个总亮度。
3. 从保留的 `F_complete.blend` 复制新的编辑源，接入独立控件和贴合后的文字；录制精确运行时take再烘焙核对。不要重跑早期complete_f.py覆盖保留的源。
4. 做本机独立包（原生鼠标待解锁），完成开发检查点后转I/J/K/L/M/N，G其余最后。AAA仍为目标，不能把任何检查通过写成美术验收。

## 最新接续补充

- 原生Mac测试进程已终止，日常包本身仍是G2/全息入口版本，没有本轮F。共用全息控件的实际导出PCK已用匹配Godot引擎运行输入/资源检查通过；仍不是OS鼠标检查，需用户手工解锁。
- 刻字实时投影实测73.637ms。已离线保存5份贴合后的Mesh资源 (`f_console_mounts/`)，校验实际底座/操作匣曲面、控件安装姿态与原字形顶点/索引。缓存失配会重新真实贴合，不能用旧坐标硬套。Mac预热现与主viewport MSAA一致，并预热F控件/缓存；实测本次缓存路径12.025ms、0射线。这是局部准备耗时，不是60FPS验收。
- `console_runtime_qa.json`：实际Godot拾取5控件、拨杆轴心、上拨为正、旋轮正向顺时针、零误差中央/正误差向右、底座单实例及尺寸。`console_clearance.json`最新源125姿态交检通过。实际舱罩/牌架扫掠仍要补。
- `lighting_profile_qa.json`检查F独立配置、G配置和B恢复，不再要求F回到B照明。`instrument_qa.json`和`calibration_feedback.json`通过，退出清理已修，无需凭检查数宣称视觉完成。
- 已复制原 `F_complete.blend` 到 `F_refinement_candidate.blend` 并替换候选内的CTRL控件为新FCTRL GLB。原源SHA为1b003807a70a3be8d9b0385cfdd9b9758022b58bd29a30364ebfe0c21728db01，未修改。原文件来自Blender5.2，本机5.1.2有兼容性警告；只操作隔离副本，需校对几何/变换后才能晋升。
- `f_visual_take.gd --bake-only --revision`已扩展为新take：机械/控件30FPS，FX每2帧（15FPS采样，非性能测试），记录真实固体、光点、光带分段、竖直束、接收波、回写点、局部灯和硬件发光值，同时记录world_poses、moving_names、真实灯镜发光值及刻字完整网格。最新记录正在/已由同一命令重录，查看full_take/报告和运行日志。
- **下一步写独立的F候选烘焙器**：消费上述take与candidate，不运行旧 `bake_f_take.py`（它会直接写主F_complete且近似重算特效）。可用本机验证过的 `Action.fcurve_ensure_for_datablock(obj,data_path,index=...)` 加 `keyframe_points.add/foreach_set` 批量写轨道，减少逐点插入耗时；插值与静止段必须保真。对新候选校验local/world姿态、控制器、贴合字形、收势/拆装，再渲染与导出。

## 候选烘焙已完成（本次最新）

已新增 `bake_f_revision.py` / `verify_f_revision.py` / `render_f_revision.py`，只写隔离候选。1321帧、385个动画数据块、316个光效对象，使用捕获的实际光点/光带分段/竖直束/接收波/回写与金属实例；不是重新猜路径。刻字按完整记录网格重建，不能对不保证同序的glTF顶点盲目按索引覆盖。当前候选f71474d2...，77时刻local/world/控件/光效/强度与全部字形数据校对通过，详见full_take/candidate_bake.json和source_verification.json。

关键修复：dummy renderer的MultiMesh getters会返回默认值，导致初次headless录制的可见刻度在源中消失。已让f_visuals缓存同一份实际GPU写入数据，录制不再依赖dummy读回。真实Metal对照gpu_capture_parity.json验证308实例，28枚刻度均不同位。旧37M take/旧21faf9...烘焙只是错误中间产物；现已重录重烘焙。baker含非塌缩/非零峰值校验，并从实际GLB取倒角后原型。

Blender隐藏viewport对象不会刷新matrix_world，验证器因此对无父对象的所有光效检查matrix_basis，显示时再核对world；不是忽略隐藏姿态。源预览已查看，但它的光带仍偏白粗，预览灯能量比例40及硬件光路/后处理差异均明确留在报告，不可当成与Godot逐像素相同。原主源与日常App均未替换为F新版。

接续仍需实际底座/舱罩/牌架扫掠、全演出/取消、源效果匹配、独立Mac包和原生输入。旧bake_f_take.py仍不可直接运行覆盖主源。

## 安装扫掠补查

`f_selector_clearance_take.gd`直接导出当前Godot导入物理网格和世界变换，排除运行时光学Quad；`check_f_selector_sweep.py`对101打开比例的舱罩/滑轨/实体铭牌与F五个控件做实际网格包围盒分离检查，结果通过；本次无需进入窄相BVH。见installation/selector_sweep_check.json。它不验证固定安装配合、上部与底座、所有控件操作组合或连续体积；仍须按范围继续补查。

## 起势取消补查与修复

新`f_cancel_rise_qa.gd`先通过真实机构获得校准，再在上升初段收回。修前峰值从0.02695反升至0.15788（15个增亮帧）；修后冻结取消时的peak/crest后衰减，0增亮帧。独立visual_charge保留视觉连续性，避免逻辑charge归零时骤暗；实际Metal中draw_gain从0.62115首帧到0.58016，1秒归零并成功收纳。前后JSON与GPU截图均留存，未用手动设置peak_time的假状态。

F声音现在遵守collection_no_audio，退出时stop并释放stream。最新无窗口取消测试不再泄漏calibration.wav播放对象。日常Mac仍未包含此F修复；其他反向/取消场景与源效果匹配继续。

## 反向与上部避让补查

`reversal_qa.json`覆盖半开收回再开、持刹车收回后释放重开、半拆反向再开、自由运动进入拆解后完整组装。使用控制器driver值，没有同时开合/拆解，局部杆长误差2.3e-7，三个跟踪支承原点最大单步位移0.03092，最终home一致。该位移统计不等于所有顶点无穿插。

`verify_f_clearance.py --revision`读取隔离候选，54操作/停车姿态下两悬挂和接收盘对弧形框架及共享底座/面板18网格无面交叉；证据upper_base_clearance.json。原主源未动，全部零件、连续碰撞、原生输入仍不在此证据范围。

## 独立检查包与演出视频

`dist/macos-review/MagicDesk-F-review.app` 已生成，独立bundle id `com.cedricxugun.magicdesk.freview`，打开后Tab选F。PCK9c70769b...，native/build.json和packed_checks/pack_binding.json绑定实际包。匹配引擎读取PCK的控件脚本检查通过；这不是原生鼠标验证，CUA再次遇到锁屏。日常App与F主源未替换。

movie/F_refinement.mp4是实际Metal逐帧录制再编码，1280×1082、30fps、1321帧、44.033秒，无声。可看完整打开、偏置、制动、校准、回收、18组拆装/回位，已检查关键峰值和拆解帧。不是实时性能测试。新增f_visual_take.gd --revision --capture-movie，电影数据在独立movie目录，不覆盖canonical full_take。不要直接对动态调整桌面窗口使用--write-movie；第一次相对输出路径写入失败且初始尺寸不一致，未采用。

## unshaded预览匹配实验

`f_atlas_color_probe.gd`与`probe_f_atlas_color.py`用同一127/63/25/255恒色小纹理、4档增益、黑背景/AgX做实际Metal/Cycles对照。Metal中EMISSION=0与6000完全同输出；Blender旧等效图额外乘1+6gain是错误的。修成unshaded颜色/alpha并转换颜色提示后，平均RGB误差从0.12478降至0.00306。见optical_probe/comparison.json，不将此局部测试扩写为完整场景/其他后端一致。

已通过sync_f_optical_preview.py修正候选中真正使用的4个atlas材质（注意不能按固定名称误改旧的未使用材质），光片只供相机看，不额外参与Cycles间接光/反射。候选现237f4690...，baker也已更新，重新渲染和变换校对通过。source_peak仍有整体观感差别，灯光预览比例40与透明合成/后处理没有宣称完全相同；运行App与原F主源未受此修改。

## 收纳休止路径

`idle_effect_before.json`/`idle_effect_qa.json`测量5×300次单独fx.tick：原约0.56ms/次，新约0.0009ms/次。完全inactive才跳过112实例/84光带更新，仍保留弱参考材质；重启清旧速度/方向并按当前位置初始化。唤醒、再收回、取消及实际Metal308实例一致性回归通过。测量不代表整帧/原生FPS。

完整take与候选已刷新并校对，源b9118b3e...；独立检查包PCKadedd8bc...，包内检查也刷新。旧9c707...包已保存备份。日常版/主源未晋升；原生仍因锁屏未验证，先前44秒录像不作为此休止优化的验证视频。

## 亮/暗背景合成

`f_lighting_review.gd --backdrops`在应用自身Canvas下放置不透明白/暗色背景，实际Metal渲染保持原照明，保存canvas_white/dark.png。不是系统桌面输入验证。白底下细光线/亮金属刻度更淡，需与暗底一起判断。新增foil emission_scale默认1，0.30仅对照实验（canvas_low_foil_*），尚未采用或更新检查包。

## 2026-09-11 切换延迟

原生CSV逐阶段分析发现长单帧阻塞，见switch_latency/native_stage_analysis.json。修正_prepare中的暖机MSAA/AreaLight配置不匹配，真实时间B/F/B检查通过；缓存已热，不能当冷启动A/B加速证据。F10.726秒中仍有归档首次使用1.968秒长帧待处理。新改动未导出检查包，不影响当前源烘焙。

独立Mac检查包已于本轮更新为PCK db057a516d8a...，包含公共全息contrast_r2与暖机配置修复；真实PCK控制器检查通过。旧live原生证据绑定adedd8bc，不能算新包验收；日常App仍未替换。
