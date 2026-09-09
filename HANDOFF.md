# MagicDesk 接手说明

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
