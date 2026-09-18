# G1 材质与运行时源同步

2026-09-10。G1候选完成一轮材质分区及完整机械/封合源同步，主G和Mac包仍未替换。

## 实际修改

Godot候选原来统一给金属加清漆，同时没有保留红色搪瓷和眼部的独立釉层。本轮通过 `butterfly_materials.json` 分开瓷釉、黄铜、镍、深色金属、红色搪瓷及镜片；粗糙度、法线强度和涂层各自设置。G0与G1共用 `finish_profile.gd` 的参数应用逻辑，各自保留独立配置和作用范围。

同一运行姿态/灯光的实际对照：[修改前近景](../../../review/G_optical_curator/butterfly_r2/materials/before_close.png)、[修改后近景](../../../review/G_optical_curator/butterfly_r2/materials/after_close.png)、[正常镜头](../../../review/G_optical_curator/butterfly_r2/materials/after_desktop.png)。这一轮针对材质覆盖造成的受光差异，照明沿用现有G配置。

六类设置作用于G1的54个表面，其他藏品与共享缓存没有被改写；G0的73表面隔离回归也通过。仅材质检查的无声场景不再启动循环背景音，避免Dummy音频退出时残留播放实例；正常App仍按原行为播放音频。

## 可编辑源已同步

- `sync_butterfly_materials.py` 带备份同步独立蝶源与候选中的G1材质，几何/姿态和原有动画指纹保持一致。数值遮罩重新绑定相同源修订，图像内容未因材质同步而改形。
- `prepare_butterfly_source.py` 从当前完整主G源复制出隔离候选，替换其G1；主G源散列保持不变。运行网格装配脚本不再覆写动画源。
- 重新记录3859帧完整运行时流程，覆盖六片/六件、读取、构建、动作、回收、拆装与中途退出。其他四件藏品仍是待精修模型，这个回放不代表它们美术完成。
- `bake_butterfly_candidate.py` 写入145个对象的机械、表情与实体控件动作，G1八个翼片材质绑定对应遮罩与成形/回收进度。
- 保存后的5805个机械姿态采样通过，位置误差0、最大基误差约4.77e-7；430个控件姿态采样通过，最大基误差约1.19e-7。未发现缺失节点或贴图。

[完整候选源](../../../blender/collection/G_butterfly_runtime_candidate.blend)现已不再是静态装配。[源封合渲染](../../../review/G_optical_curator/butterfly_r2/full_take/source_panel_seal.png)、[源展开渲染](../../../review/G_optical_curator/butterfly_r2/full_take/source_play.png)用于核对姿态、材料与封合。Blender的光照/反射与Godot配置并非逐像素等价；运行时唱片细槽着色、光丝、微粒及动态文字仍属于实时合成层，不能把这些源图当作全部GPU效果的一致输出。

证据入口：`full_take/take_report.json`、`full_take/blender_bake.json`、`full_take/source_animation_report.json`，均位于 `review/G_optical_curator/butterfly_r2/`。实际候选十项回放检查在材质同步后再次通过，包含部分成形取消和原片归槽。

## 下一步

在独立Mac检查包中使用候选G条目，验证实际桌面尺寸、选择入口、展开/振翅/收拢、取消和帧时。可在忽略目录中的项目副本覆盖G条目导出，主注册表保持到候选检查完成。随后决定是否将这一轮G1推进到主开发资源，再接下一件藏品。

不重复材质分区或机械/封合烘焙；也不要把源比对或脚本通过写成AAA或原生性能验收。
