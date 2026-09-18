> 最新接入与限定检查已到 ../scan_caps_runtime_r43/README.md。下文保留R41最初独立试作状态。

# R41 小型读谱镜片端头——尚未接入

内置image_gen局部工艺图：scan_tip_detail_r1.png；完整提示词：PROMPT.txt。只有局部端头参考，不改变主壳、三根触须位置或共同底座。

源 `blender/collection/I_scan_cap_r41.blend`，SHA 7f75d8fbb1608da067b673868ca0c51c620a0cf10731fed4ec6ff51c6555a422；组件 `app/assets/collection/art/I/scan_caps_r41/cap.glb`，元数据同目录cap.json。

以真实 IAM_TineRoundedAxial_0 网格光线采样形成金属压圈背面，三颗旧球头逐顶点相同；外径小于原圆头，保留红色球体与杆身。新件有金属压圈、暗色密封圈和琥珀镜片。全部原A坐标/三角/变换保护；各新件源自接触与对原球头相交检查为0，背座采样见review/I_refinement/nautilus_r1/scan_caps_r41/seat_samples.json。

**未完成**：新件互相接触/间隙、实际材质近景、三个球头运行时绑定、光束起点从旧球极点移至新镜片前表面、源位姿/动作验证与卸载清理。当前R42谱面预览尚未包含这些端头，不能声称接入或验收。后续保持用户最新的全透明谱面要求，禁止恢复黑底。
