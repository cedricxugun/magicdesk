# 圆口朝向、位置与连接：实际模型对照

## 当前实际版本：2026-09-14 / 8b5c91f8

R3的左下侧、斜向前方安装关系已延续到当前完整结构候选，壳体从侧前方连续接向口后；12组内腔座、下支承及三片上盖的实际导向/线性抬升机构已装入。**当前仍未锁形，桌面App未更新。**

| 原先被否定的安装关系 | 当前实际模型 |
| --- | --- |
| ![旧圆口关系](../../../../review/I_refinement/nautilus_r1/cassettes_r2/views/relation_rest.png) | ![当前完整实际模型](../../../../review/I_refinement/nautilus_r1/linear_drives_r20/presentations/8b5c91f8/relation_rest.png) |

仍需返工：口后套环显厚，卷壳接续与展开边缘不够自然、完整；当前内框、金属面和材料也与下方目标存在明显差距。居中谱面在新斜角下偏前左、偏弱，不能只看局部坐标。现有机构通过的有限检查不代表上述视觉问题解决。

![当前展开实际模型](../../../../review/I_refinement/nautilus_r1/linear_drives_r20/presentations/8b5c91f8/relation_open.png)

以下保留R3初次纠偏记录，用于追溯：

这轮是独立形体纠偏，尚未替换桌面 App。新旧模型使用同一底座和同一对照机位；效果图的相机仅能近似对齐，不能据此计算“还原率”。

| 原模型 | 本轮修正 d84b7d87 |
| --- | --- |
| ![原模型](../../../../review/I_refinement/nautilus_r1/cassettes_r2/views/relation_rest.png) | ![修正后的实际模型](../../../../review/I_refinement/nautilus_r1/mouth_relation_r3/presentations/d84b7d87/relation_rest.png) |

圆口移向卷壳左下侧，朝向侧前方，口后瓷壳直接延伸到主体。固定下颊与活动上盖已分开；原来的四组实体机构保留在旧源，新形体的机构配装、内腔承座及边缘工艺继续制作。

艺术目标保持这张图：

![保持的艺术目标](../nautilus_states_centered_r2.png)

本轮完整展开图如下。它加载了全部保留的内腔，仍是未配实体机构的运动候选，不能作为最终精修完成图：

![本轮展开候选](../../../../review/I_refinement/nautilus_r1/mouth_relation_r3/presentations/d84b7d87/relation_open.png)

正、侧、顶视及源哈希在同一版本目录。9姿态所查项通过，整体拓扑仍有分离零件；连续支承、全部组合动作和新斜角下的谱面可读性还未完成。
