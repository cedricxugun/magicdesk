# R90 声腔骨架与导光网络交接

2026-09-22 Git 工作检查点。当前可编辑源为 `blender/collection/I_r90_acoustic_network_r5.blend`，SHA256 `29eeed37d405bdd6e7982395bda921db53dfc3d6c01c7fe0a2ce23598d590444`；上部组件为 `app/assets/collection/components/I_r90_acoustic_network_r5.glb`，SHA256 `2bbbc6f7ce05d67a34c715c0958ec94ddf913b380dca44e4c7c489d96d09c271`。

当前源包含 R88 成型后支撑和 R89 十二声腔，新增贴合内壁的连续金属骨架、凹入导光槽、真实框口接头和绕过紧固轴的环形分光座。共 44 段实体导光网格，连接十二声腔。r5 修正光条与壳体、两密封座、三接头的局部干涉。`I90_ACOUSTIC_BACKPLANE` 分组供后续检修设计使用，分组本身不是完整拆装动画。

## 证据及边界

报告入口 `review/I_refinement/nautilus_reset_r82/network_r90/built_r5/build.json`，运行布局 `app/assets/collection/art/I/r90_network/r5/chamber_layout.json`。

- `network_contacts.json`：新增网络对旧固定件的三膜片极值、光条对壳体/机械紧固件所查接触为空。特意形成的浅层内衬接合单独排除；不证明所有新件互相、连续运动或整机无干涉。
- `contact_check.json` 与 `installed_contact_check.json`：13 外甲姿态、13 身体/音乐内芯姿态的限定检查；内芯承接平面为明确列出的设计配合。
- `runtime_morph_qa.json`：1440 个实际导入形变见证最大世界误差 0，暂停回稳通过。
- `network_runtime_qa.json`：29184 个实际 UV 顶点、12 个声腔入口相位、停止/暂停保持与闭合复位通过。不是音频逐拍或性能认证。
- `open.png` 为实际 Blender 图；`native/state_03.png` 为实际 Godot 不透明独立工作室图。后者早于最新导光对比度调整，不能当成新亮度最终画面。

最后增加 `guided_network` 分支，增强流动光头与暗底的对比，网络增益 3.8、暖色 `[1,.38,.065]`，旧布局默认保持。随后的 Movie Maker 录制没有产出有效影片：接手检查时进程已结束、raw.avi 为 0 字节，且无完成回执。原因未确认，不能称录制通过；无效 raw 不上传。下轮先验证新亮度的真实动态及录制脚本，再继续美术。

## 月光与控制

完整月光三乐章音源及 R82 光学内芯保持。网络随实际作品时间推进，暂停/停止时展开中的光波保持，收拢后复位。手动蓄压/回声尚未接入新网络，当前真实控制映射和拟议检修顺序见 `CONTROL_CONTINUITY.md`。勿把旧全局调频/喉口配置误当现在的五个控件。

主 App 注册项仍是 R68；本次没有新 EXE。当前是独立 R90 候选，不是完成的整机。后续优先：新导光动态与材质验收、压力/回声联动、实体控制器和完整可逆拆装、主 App 集成、透明桌面与帧率验证；随后按 `production/REFINEMENT_QUEUE.json` 原队列继续。AAA 与所有剩余款目标保持 active。

## 在另一台机器继续

先安装 Git LFS 并执行 `git lfs pull`，打开当前 r5 Blender 源。Godot 项目是 `app/project.godot`；首次运行需导入资源。独立预览脚本 `tests/collection/i_r82_combined_render.gd` 的默认入口已切到 r5；可传 `--report=res://../review/I_refinement/nautilus_reset_r82/network_r90/built_r5/build.json --studio-polish --temporal-polish`。

概念图 `network_concept_r1.png` 使用订阅内置生图，提示词与来源记录同目录；只作造型/工艺方向，不是尺寸或结构认证。当前数值输入为 `paths_r3.json`、`plate_parameters_r4.json`。历史构建脚本可能依赖未携带的中间 Blender 源，跨设备应从当前可编辑 r5 源继续，不能假设全部历史流水线可从零重放。
