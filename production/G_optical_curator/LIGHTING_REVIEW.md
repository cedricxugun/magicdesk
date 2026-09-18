# G 光照与光学面第一轮复查

2026-09-10，继续全批精修队列中的 G。对应 `review/G_optical_curator/lighting/`。本轮只解决一部分光照和光学面可读性，不代表 G 的模型、材质、特效和操作已经完成。

## 实际发现

主场景先建灯，再由 `quality_lighting.gd` 重新标定。因此真正的基线是环境强度0.50、三灯能量24/34/4、HDR0.32、面光源软阴影尺寸0.65，不能只读 `main.gd` 中较早的初值。

对同模型、同姿态、同镜头分别关闭 SSIL、软阴影、灯的镜面分量及阴影，随后测试主辅光平衡和光学面反射。对照脚本保存实际基线，并在各变量测试前还原它，避免误把其他参数变化归因于单项开关。

- 这张机头近景中关闭 SSIL 影响很小，不能据此把噪点全部归因于 SSIL。
- 直接关闭灯的镜面分量虽然让眼睛对比鲜明，但金属也失去质感，因此不采用。
- 降低光学屏的镜面/清漆反射可以压住覆盖眼睛的白色高光，同时保留壳体和金属的反光。实际差别见 `06_balanced_candidate_head.png` 与 `08_coated_optical_candidate_head.png`。
- 主辅光重新平衡后仍保留实时阴影；还需继续检查展开内部、读取、构建和回收时的遮挡与高光，不能只凭正面静态图完成光影项。

## 已接入

`app/assets/collection/lighting_profiles.json` 存放 G 的专属灯光和光学面参数。`collection/lighting.gd` 捕获原 B 的真实标定，在模型间平滑过渡，未配置的模型恢复原标定，不把 G 的灯光永久留给 B/F。

G 当前采用环境0.40、三灯20/22/3、软阴影尺寸0.065、SSIL范围0.25；光学面镜面0.20、清漆0.10、粗糙度0.22。它们是当前经对照选择的工作参数，不是通用标准。

`lighting_profile_qa.gd` 检查 G 应用、被打断的过渡、F恢复与B往返还原；实际机头已再次渲染。`sync_curator_optical_material.py` 只同步现有 Blender 动画源中的光学材质，保留已有3805帧动画，避免为改涂层重跑模型生成器。

## 资料与接续

已查阅 [Godot 光源/阴影文档](https://docs.godotengine.org/en/latest/tutorials/3d/lights_and_shadows.html)：阴影偏移过大/过小分别可能导致脱离和自阴影，面光源的软阴影和材质支持也有限制。文档为 latest，所用参数已在本机4.7.1实测，其他描述不可直接视为本机已验证。

[Godot 环境文档](https://docs.godotengine.org/en/latest/tutorials/3d/environment_and_post_processing.html) 将 SSIL 定位为间接光补充；其范围、采样和模糊参数需要随场景检查。[PBR材质文档](https://docs.godotengine.org/en/stable/tutorials/3d/standard_material_3d.html) 用于后续粗糙度/法线/遮蔽通道检查。

下一步继续 G 的其他状态和六件藏品对照，尤其是轮廓与设计的匹配、金属加工和瓷釉工艺、专属特效。F 的力度与操作问题已记在 `production/F_complete/review_20260910/INTAKE.md`，待 G 收完后开展。
