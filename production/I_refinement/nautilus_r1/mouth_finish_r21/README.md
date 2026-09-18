# 口部连续过渡：R21独立形体候选

当前源 `blender/collection/I_nautilus_mouth_cowl_r21.blend`，SHA256 `5a8effb92113503a863187cec3d00766c71c603e4bc92014439a3927f01ee599`；组件 `app/assets/collection/components/I_nautilus_mouth_cowl_r21.glb`，SHA256 `dd6d8923e1cd5e596fb2baf7642830e24c52235c65a91dc13429b172e31811ed`。有限检查入口：`review/I_refinement/nautilus_r1/mouth_finish_r21/checkpoint.json`。R20源8b5c91f8保留。

## 本轮实际改动

口部A的安装原点、朝向、内机构和居中谱面安装关系均未改。把原有01/05/06和固定下颊的口后曲面向前延续，最大轴向延续0.215场景单位；前端从A局部深度约+0.257移至−0.050。数值来自3D源，不是从生成图读取。

形体映射沿口部轴向单调展开，原顶点与结构保留；实际源分裂法线跟随映射，再对过渡区做有限平顺。前沿和身体端边界保持，安装硬件、原A/C1后法兰、内芯、两条金属支承、三组机构和真实底座都在保护集合内。

早期R3的独立 `IN1_MouthShoulder` 只是一层外形肩套，无子级硬件、无运行时绑定；实际承力在原A/C1法兰和支柱。延续后的主体瓷壳已取代其外形过渡作用，因此该重复套层退出当前候选。原实物口沿、固定载体、锁扣、后法兰与支承全部保留。删除不是对夹持/承力件的豁免，旧源可追溯。

## 设计与实际模型

本轮局部图采用 **built-in image_gen**：

![局部连接设计](mouth_junction_close_open_r1.png)

[完整提示词](PROMPT.txt) 与 [来源清单](art_manifest.json) 已保存。它仅细化口沿/连续下颊/完整包边，不能替代原目标 `nautilus_states_centered_r2.png`。图中的触须长度及新增扣件位置不作为数值依据。

| R20实际模型 | R21实际模型 |
| --- | --- |
| ![R20闭合](../../../../review/I_refinement/nautilus_r1/linear_drives_r20/presentations/8b5c91f8/relation_rest.png) | ![R21闭合](../../../../review/I_refinement/nautilus_r1/mouth_finish_r21/presentations/5a8effb9/relation_rest.png) |

![R21实际展开](../../../../review/I_refinement/nautilus_r1/mouth_finish_r21/presentations/5a8effb9/relation_open.png)

[12秒实际组合动作](../../../../review/I_refinement/nautilus_r1/mouth_finish_r21/video_5a8effb9/coupled_structure_r1.mp4)：先开A再抬盖，关闭顺序相反，包含途中反向。它没有音乐音轨或完整音乐交互，不是新的App。

## 检查与限制

四个修改壳体的实际渲染三角所查项通过；9个外盖源姿态，以及7个有真实几何变化的A源姿态×闭盖/开盖的相交检查通过。源保护与当前哈希一致。实际Godot已回放组合顺序，并保存同相机图与短片。这些不涵盖每个连续时间点、全部运行时变形、体积包含、载荷或全场景验收。

**当前仍不是最终成型曲面。** 独立套筒感减弱，但口后仍有拉伸/凹折感，前上盖及其他活动片的尖端、切口和包边未达到图稿工艺。有限平顺没有解决全部曲面问题，不能把它称为精修完成或AAA。下一轮要用更平顺的成型曲面和完整边缘重构替代局部补丁，保持前口、主体接口与实际安装座的关系；随后继续中央谱面斜角、完整月光联动、旋转动力/供能、材料灯光和原生。

失败候选保留：d4b3c9fd延续壳面与旧白肩套相交；d086195e/f4075946额外薄镍套仍有局部冲突，未被采用。`iterations`及`blender/collection/checkpoints`保留源和报告。旧formed_loft属性在当前源大部分已丢失，部分布尔新面默认0，不能按字段值盲目选区；当前采用实际口部坐标范围并验证保护集合。

未锁形，未用户艺术验收，主App未更新，Git未推送。全队列继续active：I后J/K/L/M/N，G其余最后，B保留。
