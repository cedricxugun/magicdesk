# G1 机械蝶实时候选：2026-09-10

新机械蝶已经进入独立运行候选，并完成一次真实场景/控件驱动回放。**主G注册表和Mac包仍使用旧蝶**；最新分区封合见 [PANEL_SEAL.md](PANEL_SEAL.md)；材质/光影、完整源与原生验证仍待完成，未通过美术验收。

## 图稿与资产

内置 `image_gen` 生成的[构建/回收分镜](fabrication_storyboard.png)、[完整提示词](fx_prompt.txt)和[出处](manifest.json)保存在本目录。参考为已经制作的真实蝶模型。分镜前两格把完整翼缘亮得太早，实际实现改为先支承、再翼根向外推进。

34条路径、928个线段来自保存的Blender翼脉、包边、嵌件边界、胸部及栖架曲线。它们随实际翼节点运动，沿用已有内置生图光纹 `field_strands.png` 进行合成，不用随机线条替代模型结构。五组MultiMesh合成这些路径；供能收敛为脚座附近两条，微粒和光斑同步减弱。

## 已实现

- `assemble_butterfly_candidate.py` 创建 `G_optical_curator_butterfly_candidate.glb/.json`，仅替换候选里的藏品1。主G GLB/JSON与当前完整动画源未被覆盖。
- `butterfly_drive.gd` 使用与独立源相同的四连杆闭合解，正确转换Blender Z-up到Godot Y-up。连杆局部朝向保留球杯开口向下；没有用缩放杆长追目标。
- 成形时蝶翼保持收拢；完全成形后限速展开。按住时约0.8秒蓄力，松手约1.4秒回落；收拢状态下按住会先展开到可振翅范围。
- 完整展示后的回收先经过1.2秒收翼阶段，再从翼尖回退；半途成形取消直接反向收束，原唱片不被特效销毁。
- `butterfly_fabrication.gd` / `butterfly_trace.gdshader` 和G表面着色器为四翼分别设置局部生成进度。上翼略先于下翼，支承先于翼面，光纹领先实体边界。
- 修掉播放器与RefCounted驱动器互相引用的循环；最新回放退出未再出现初轮的资源/RID泄漏告警。

## 实际证据与边界

[实际候选截图](../../../review/G_optical_curator/butterfly_r2/runtime/)包括构建20%/55%/85%、展开、振翅与回收。这是同场景底座上的检查近景，不是生成图，也不是已导出的Mac App。

`tests/collection/butterfly_candidate_take.gd` 十项检查通过，覆盖封合后展开、按住/释放、收翼后回收、原片归槽、部分构建取消和光纹清理。实际节点两端最大误差约1.34e-7，球杯朝上轴点积为1.0。报告 `candidate_qa.json` 记录检查范围；它不代表特效品质、完整碰撞极值、原生输入或性能验收。

`G_butterfly_runtime_candidate.blend` 已完成3859帧机械/表情/控件与G1分区封合同步，见 [MATERIAL_SOURCE.md](MATERIAL_SOURCE.md)。光丝/微粒等实时层仍未烘焙，主G源和Mac包未替换。

## 下一步

1. 整翼硬切已由模型烘焙的分区封合替代，见 `PANEL_SEAL.md`；不重复这一轮封合资产制作。
2. 材质分区和源同步已经完成一轮，直接从 `MATERIAL_SOURCE.md` 的独立Mac候选检查继续。
3. 完成实际桌面尺寸、原生输入、取消及性能检查后再决定主G资源替换。
4. 不重复重建翼背/四连杆，不重新生成同一张分镜；G和全批精修仍在进行。
