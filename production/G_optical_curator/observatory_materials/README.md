# G0 观测塔材质分层：2026-09-10

本轮把已有结构的瓷釉、黄铜、镍、铜、红色搪瓷与暗色嵌件分开标定。没有重新生成或增厚零件，也没有增加碎屑/烟雾遮盖结构。G与全批精修仍在进行，未导出新Mac包。

## 实际修改与对照

- 瓷壳接回已有釉面粗糙度和法线资产，降低统一亮膜感。光学微纹保持微弱，不能期待在小摆件尺寸逐条看见。
- 黄铜、镍和铜分开设置颜色、粗糙度区间及拉丝强度；金属不再统一叠清漆。黄铜更沉，镍保留较冷的反光，铜支承和内部齿轮不再挤在同一明度。
- 红色搪瓷保留独立釉层和反光，维持上一轮天球/红球的交互光。
- `observatory_materials.json` 是统一参数来源；颜色为线性RGB，运行时转换后传入 `source_color`。粗糙度/法线以数据贴图采样，不作颜色转换。沿用已存在的陶瓷/金属资产，本轮没有新生图。

同灯光、同机构姿态、同镜头的实际运行截图：

- [修改前近景](../../../review/G_optical_curator/observatory_materials/before_close.png) / [修改后近景](../../../review/G_optical_curator/observatory_materials/after_close.png)
- [修改前正常镜头](../../../review/G_optical_curator/observatory_materials/before_desktop.png) / [修改后正常镜头](../../../review/G_optical_curator/observatory_materials/after_desktop.png)

这些是实际场景驱动回放，并非已导出App的原生鼠标验收。正常镜头下更需要靠主要材质区分，而非放大纹理噪声。

## 实现与源文件

`curator_visuals.gd` 在复制后的 G0 材质上应用 `observatory_materials.gd`，不会修改共享底座或其他藏品。通用 G 着色器新增清漆粗糙度、镜面强度和粗糙度偏置，默认值保持旧行为。实际材质检查覆盖73个表面、六类材质，观测塔以外受影响表面为0，共享缓存被改写数量为0。

`sync_observatory_materials.py` 带备份更新 `G_optical_curator.blend` 与 `G_observatory_r2.blend`，以对象材质槽隔离其他网格使用者。两个文件的几何/姿态和全部动作关键帧指纹前后一致，原有构建动画节点保留。保存后再次比对5334个机构姿态通过，无缺失贴图。

本轮没有重导GLB。运行时最终材质依赖 **GLB + 材质JSON + 贴图 + 应用脚本**；单独打开旧GLB不会显示本轮最终设置。新源材质已保存，后续如要重新导出组件，应从现有源或显式应用该JSON，不能重跑早期几何生成器丢失当前编辑。完整GPU演出仍未烘焙。

近景11项交互回归通过，包含有图像差异的刻度反馈、蓄力回落、回收清理和原唱片归槽。材质改变后光纹对照为862个指定阈值以上像素；这只是近景可见性证据，不代表操作已经易懂。

## 后续

已完成[正常镜头交互回放](../../../review/G_optical_curator/observatory_interaction/desktop/interaction_qa.json)，11项通过，光弧41个指定阈值以上差异像素。实际画面仍显示时间光弧太细；共鸣的天球/红球变化较明显。下一步处理实际实体控件的命中范围、行程、时间调整反馈与本机App输入，不能用像素计数代替易用性。完成观测塔本轮后，继续另外五件藏品；不要重新从G0建模参考、材质分区或相同交互审计开始。整体G外壳/机械臂材质与完整演出仍需收尾。

## 技术依据

- [Godot PBR 材质与贴图](https://docs.godotengine.org/en/stable/tutorials/3d/standard_material_3d.html)：金属度、粗糙度、法线及各向异性承担不同表面属性。
- [Godot 4.7 空间着色器](https://docs.godotengine.org/en/4.7/tutorials/shaders/shader_reference/spatial_shader.html)：独立的 `CLEARCOAT_ROUGHNESS` 与镜面参数。实际参数在本机4.7.1运行对照，未把文档描述当视觉验收。
