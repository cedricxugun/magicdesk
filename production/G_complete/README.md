# G · 折维书匣

延续《原子之心》的复古机械语言：釉面奶白瓷片、镍铬书脊、暗色轴套与红色拨件。玩法围绕“选页 → 对孔 → 按住刻写 → 重建记忆”，不是换形状的普通按钮。

| 实体控制器 | 操作与反馈 |
| --- | --- |
| 索引轮 | 滚轮选 1–6 页，也能横向拖动；选页机构让当前页前移 |
| 折角滑块 | 滚轮/横向拖动；Shift＋滚轮微调；中点为标定角 |
| 写入压板 | 按住刻写，松手暂停；写满后形成三维记忆浮雕 |
| 对准表 | 只读，显示所选组三页的真实孔位/准直质量 |
| 拆装拨杆 | 左拖拆解；右拖回收投影、退写头、合匣并重组 |
| 最右 X | 安全收拢、熄灯并退出应用 |

提示停留后才出现，位于整排操作区上方；操作中隐藏。切换不同页不会覆盖另一页的角度和部分记录。

- 设计分镜：[G_motion_vfx.png](images/G_motion_vfx.png)
- 实际光学素材：[optical_atlas.png](../../app/assets/collection/art/G/optical_atlas.png)
- Blender 源文件：[G_complete.blend](../../blender/collection/G_complete.blend)
- 可运行 Windows 应用：[MagicDesk.exe](../../dist/MagicDesk.exe)
- 数学与验证范围：[MECHANISM.md](MECHANISM.md)
- 实机图稿对照：[index.html](index.html)
- 原速 EXE 演示：[G_showcase.mp4](../../review/G_complete/native/G_showcase.mp4)
- 最终帧时间与退出验证：[delivery_report.json](../../review/G_complete/native/delivery_report.json)

先运行 `complete_g.py` 生成新的独立模型，再运行 `g_visual_take.gd` 记录实际机构与效果，最后用 `bake_g_take.py` 烘焙源动画。原 `G.blend`、B、F 及其原有源文件均保留。所有本轮生成图只使用订阅内置生图；不标注无法验证的后端模型名称。

Windows 实机视觉与功能证据独立记录，不以测试通过等同于达到 AAA 成片水准。Mac 本轮尚未重新导出验证。

最终录制的 G 运行阶段约 59.66 FPS，P95 20.808 ms，最大间隔 27.460 ms；含首次载入的全程最大间隔 236.415 ms。13 项原生操作检查、10 项连续状态检查、4 项可变步长终点回归全部通过；实际瓷片网格的 165 个采样时刻未检测到叶片/封面穿插。F 原有机构回归也通过。
