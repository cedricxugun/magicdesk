# 喉口护网金属工艺细化

当前独立候选 `I_mouth_finish.blend / I_mouth_finish.glb`，来源为已保留的 `I_front_guides`。沿用已有喉口细化图/卡匣图的金属工艺方向，以及 `production/I_refinement/part_a_mouth/material_r2/` 的内置生图专属拉丝法线；没有新调用外部图片接口。

## 实际改变

三层护网保持原孔位/名义孔径、层间位置、父级缩放和拱面公式。每孔由16段改48段，孔口做0.00065场景单位微倒角，增加金属边缘反光。表面新增独立Guard/Recess材质，复用已生成并烘焙的镍拉丝法线，按护网UV铺设，弱化至0.16，保留不同层的明暗与粗糙度差异。

首轮平滑所有面导致孔周围“枕状”波浪反光。最终使用加权法线让宽阔板面保持平整，细小倒角仍有连续高光。归位槽仅平滑切线连续面，原顶点/索引和位置不改。

## 重要错误记录

新建指纹读取代码首轮误用了 `foreach_set`，污染工作副本的形变键；随后已纠正为 `foreach_get` 并从原 `I_front_guides.blend` 重新读入制作。坏工作副本的哈希与原因保存在 review/.../metal_finish/rejected_working_copy.json，未被接入或交付。原始种子源与先前App没有改变。当前构建比对Basis、全部形变键及索引；字节归一化仅将浮点正负零统一，不能忽略坐标变化。

## 实际验证与范围

- 构建：`blender/collection/build_i_mouth_finish.py`；新源/GLB/孔位/材质/保留几何指纹在 `review/I_refinement/part_a_mouth/shutter_r2/metal_finish/build.json`。
- 源采样、硬件间隙和源到导入姿态检查，分别在 geometry_check、hardware_check、source_poses、runtime_pose_qa；须匹配当前源/组件哈希。
- 实际相同studio配置的两侧REST/MID/OPEN、孔口/导轮/归位槽近景在 `studio/`。
- `before_normal_weights/` 为修法线前的波浪反光候选，不是最终效果。

局部观测已改善孔口折线、板面反光和不同金属层的区分。仍不能称完整A美术或AAA：外部保持环、后部支撑、膜片响应和整套演出仍待精修；完整海螺主体、B螺壳/C内芯及主App整合也未完成。用户收到的777613d0预览包没有重导出。
