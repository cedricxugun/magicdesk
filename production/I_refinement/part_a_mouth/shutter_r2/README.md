> 当前接续（2026-09-13）：三片、卷轴承座、前导轮与归位槽的独立候选已推进至 `cassette/front_guides/README.md`（从 cassette 目录读取时为 `front_guides/README.md`）。本页下方是对应旧源的历史状态；主 App/完整 A 尚未完成。

# A 喉闸 R2：斜叠闭合形态候选，开合机构尚未实现

**最新动态接续：cassette/README.md。** R2 本体仍是 REST 参照；从它独立派生的 I_tongue_probe 已实现首片卷收/展开和卷筒随动，其余两片尚未接入。真实视频、接触和源/运行时数据检查在该入口；不能把单片当完整 A 或主 App。

原图中的主要特征是长弧形叶片斜叠、左下露出护网，不是同心等角扇叶。六片/九片同心候选已在内部对照中否定为美术基准，见 WHY.md。这不是用户对 R2 的艺术验收。

## 当前图与实际源

- shutter_motion_r2.png：以内置 image_gen 从原始 I 选图补出的 REST / MID / OPEN 部位目标。提示词、来源与图哈希在本目录；生成图中的运动并非已验证工程结构。
- blender/collection/I_part_a_shutter_r2.blend，SHA256 `57c4df16b87b38b690b692a1372c06054cec6380715c5118286ae285ae2d8511`。
- app/assets/collection/components/I_part_a_shutter_r2.glb，SHA256 `5b6d1a8edff86b8a16a295cc5424cebfeb33a09ab1dd3378c9e5e099a3ac89e6`。
- 生成入口 blender/collection/build_i_shutter_r2.py。读取受哈希校验的旧 A 源，保留已改善的口沿/护网等，删除旧同心喉闸及驱动；输出独立 R2，不覆盖主 App I。每次重建前备份已有 R2。
- review/I_refinement/part_a_mouth/shutter_r2/runtime/rest.png 与 rest_oblique.png 为实际 Metal 闭合图。grille_diagnostic_shutters_hidden.png 只是隐藏喉闸的结构检查图，**不是 OPEN 动画**。

## 已实际改变

三组弧形薄壳斜叠，每组有外皮和背层；具有实际厚度、不同根部位置和后方承座。口沿用连续圆弧截面，前方红色夹扣可见并带真实螺钉槽。护网等比放大，圆孔保持圆形。material_r2 的内置生图镍拉丝，经 Blender 烘焙为微法线/粗糙度，未将带颜色的扫描图直接当金属底色。

口沿内侧锯齿黑白斑块通过隐藏部件/禁用阴影的诊断确定为瓷壳与直筒金属内套相交。R2 以真实瓷壳的射线交点采样内壁截面，构建径向退让 0.002 场景单位、厚 0.006 的内衬。原相机、原灯光下已去除该斑块，未用关阴影掩盖问题。旧图保留于 liner_before/ 及 diagnostic_*。

## 验证范围

rest_geometry.json 当前 scoped_passed=true：所有网格封闭且正体积，REST 叶片相互、叶片对所列固定部件、金属内套对两片瓷壳未测到表面交叉。源、GLB、检查报告、Metal 图哈希已对齐。

这不覆盖完整关节配合、所有零件体积包含、动态扫掠、运行性能或原生输入。薄壳/根部当前只有 REST；没有收纳驱动，也没有闭合→OPEN→回收动画。护网隐藏图不能代替实际运动。

## 继续只做 A

1. 同原图/本轮部位图继续核对三张主叶的曲线、遮挡比例、边缘厚度、金属/瓷釉反光；仍未艺术定型。
2. 在保持该识别特征的前提下求实际收纳空间和驱动路径。不能将双端固定的弧板直接绕中心转，也不能缩放消失、穿过护网或直接隐藏。先用可测 3D 轨迹检查，再制作真实导向/枢轴与动作。
3. 同一相机检查 REST / MID / OPEN；连续动作、反向/取消、源/运行时姿态与全部连接一起验证，再补膜片/弹簧共振。
4. A 对齐后才去 B 螺壳和 C 连续内芯，正确主体后接回已保留的月光完整三乐章和真实谱面。

共享 HELIOS 底座未修改，主 App I 未替换。全队列仍 active，不新增逐阶段用户审批。
