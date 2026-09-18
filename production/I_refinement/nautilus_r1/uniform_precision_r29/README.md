# 当前可继续的均匀曲面候选 R29

源 `blender/collection/I_nautilus_uniform_precision_r29.blend`，SHA256 `e5fe156116bf32345f5383ebeeed1ef587b3e977eba3cb5819a45e100bc61245`；组件 `app/assets/collection/components/I_nautilus_uniform_precision_r29.glb`，SHA256 `13ba552a80eb801fa2060993950e91b132a093da30dab60b9929351d85bbf3cd`。证据入口 `review/I_refinement/nautilus_r1/uniform_precision_r29/checkpoint.json`。

R28把05过渡改为均匀网格之后，实际Metal画面中的大面积条纹消失；R29进一步修复一处相邻精度点，世界位移1.4901161e-8。01/05/06与固定下颊的原始BVH自接触为0，实际渲染三角、七个A源姿态×开/闭盖、九个盖体姿态及源保护通过各自范围。其余旧零件和03旧孔区接触不包含在“四块壳自接触为0”的结论里。

![当前实际闭合](../../../../review/I_refinement/nautilus_r1/uniform_precision_r29/presentations/e5fe1561/relation_rest.png)

![当前实际展开](../../../../review/I_refinement/nautilus_r1/uniform_precision_r29/presentations/e5fe1561/relation_open.png)

[12秒组合动作与途中反向](../../../../review/I_refinement/nautilus_r1/uniform_precision_r29/video_e5fe1561/coupled_structure_r1.mp4)：真实Godot渲染，先开口闸后抬盖，关闭顺序相反。这段只检查结构，没有音乐音轨或完整音乐交互。

**仍未完成整机美术。** 下侧过渡、05前沿工艺、整体材料和内部细节仍需继续；新斜角的中央谱面与金色扫描、完整月光、转动动力/供能、原生App及其他模型尚未完成。没有把有限几何检查当成AAA验收，形体未锁定，App未更新，Git未推送。

R30前沿金属收口试制位于 `production/I_refinement/nautilus_r1/front_cowl_rim_r30/README.md`。已有实际圆角及图像，但自接触未清，不替换本版。

沿用内置生成的R21口部局部图与其PROMPT，没有新增生图或外部API。之前R26的无LOD/代理、无压缩和无主光阴影仅是诊断；最终条纹改善来自均匀采样，不能继续把它归因于关闭阴影。
