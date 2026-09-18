# G 光学馆员：当前制作状态

2026-09-10，从 `9dbc527` 接续。本轮仍未获得用户视觉认可，没有新 Mac App 导出或 Git 推送。

当前独立源为 `G_optical_curator.blend/.glb/.json`，加载入口为 registry 的 G。原 B/F 与旧 G 源保留。最新规范、实际范围、检查与限制以仓库 `HANDOFF.md` 顶部为准；机头详细设计见 [head_service/README.md](head_service/README.md)。

已实施三瓣瓷壳与真实开口、球铰机头、真实快门驱动、表情/待机、电路/散热内部、29组分段拆装、连续读取杆和六片原唱片的取放。观测塔有一轮几何补充，另外五件藏品尚未精修。

实际检查文件：

- `review/G_optical_curator/head/`：当前机头近景与固定30FPS动作检查视频。
- `review/G_optical_curator/service/`：整机固定镜头拆装、机头内部近景和布局/三角网格检查。
- `state_qa.json`、`connection_report.json`、`sweep_report.json`、`transfer_fingerprint.json`：功能、连接、原片转运及非拆解姿态比对。
- `blender_bake.json`：3805帧、137个对象的机械/表情/实体形成/实体控件动画已存入可编辑源；GPU光丝/微粒未宣称已烘焙。
- `source_animation_report.json`：保存后的源动画与实际运行姿态比对；`source_service.png` 是 Blender 源检查，不能冒充 App 截图。

当前仍需继续：整体材质工艺与布光、机头内部精致程度、每一件藏品、完整构建/回收效果、GPU特效对应的完整源动画、最终原生 App 输入/帧时/发布验证。工程检查不能替代美术验收，不能称为全套完成或 AAA 达标。

观测塔 r2 独立组件已进入主G开发资源，当前进度以 `observatory_r2/IMPLEMENTATION.md` 和精修队列为准。其他五件、整体材质/演出和原生验收仍未完成。

观测塔时间调节与共鸣反馈已完成一轮运行时修改，见 `observatory_interaction/README.md`。九个源机构和控制台灯光已同步，新GPU光层尚未烘焙；接下来做表面工艺/材质分层及正常桌面尺寸的输入可读性。

观测塔六类表面材质已分开标定并同步两个源，见 `observatory_materials/README.md`。正常镜头下时间光弧仍太细，下一步先做实体控件反馈/可读性和原生输入，再接藏品1；全G尚未完成。

已有独立Mac检查包 `dist/macos-review/MagicDesk-G-review.app`，G0原生鼠标和正常退出通过，旧App未替换。小字、42–44 FPS快照及完整源特效仍待整G收尾；下一件瓷翼机械蝶。详见 `observatory_controls/README.md`。

G1瓷翼机械蝶已有独立结构/541帧源动作，见 `butterfly_r2/README.md`；翼背、驱动固定支承、全机构净空、候选接入与专属构建路径仍待继续。当前App仍是旧蝶。

G1翼背、球接/轴承固定支承和真实唱片落座已做一轮，55硬件姿态及120唱机组合表面检查通过；下一步生成运行时适配/按翼形成路径并接独立候选。主App仍是旧蝶，详见 `butterfly_r2/README.md`。

G1已有独立实时候选、模型路径驱动的构建/回收及十项场景检查；硬切边界未达标，完整实时源尚未烘焙，主G/旧Mac包不变。下一步从 `butterfly_runtime/README.md` 的瓷片封合视觉修正继续。

G1直切已改为模型翼脉遮罩驱动的分区封合，保存约10.17秒实际候选近景视频；继续材质/光影、完整运行时源同步及Mac验证。主App未更新，见 `butterfly_runtime/PANEL_SEAL.md`。

G1六类材质与3859帧机械/表情/控件、分区封合源已同步并核对；候选源不再静态。下一步独立Mac候选验证，主App仍旧蝶。见 `butterfly_runtime/MATERIAL_SOURCE.md`。
