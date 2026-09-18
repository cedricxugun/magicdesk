# R55 对应下颊金属收口

当前源 `blender/collection/I_nautilus_lower_cap_r55.blend`，SHA **31f87c61f1835a18b8b065eb2f2ec2270a2ab3632f1a331d23036a876d158176**；组合 `review/I_refinement/nautilus_r1/cap_lower_trim_r55/build.json`。在R53上增加固定的 `I55_CapMetal_Fixed05`，与随05抬起的 `I53_CapMetal_05` 对应。

下件同样从实际Z=1.698截面生成，圆角朝轮廓内部收，背面贴合原固定下颊。它有封闭体积，不是贴线；原1233个网格及上件几何、法线、UV、材料、形变与变换保持。R51着色、R40导光、R43镜片和全透明谱面保持。

## 证据与范围

- build_check.json：2884顶点、5764三角面，正体积、自接触0、背面采样修正0、接口平面数值重叠0。闭合时到上托边的垂直间隙约.002。
- static_neighbors.json：对原组件实际导出的身体网格逐件检查，仅排除贴合的父壳，静态邻件无所查相交。
- cover_sweep_check.json：九个盖体姿态中，上下件及周围组件无所查相交。
- mouth_clearance.json：七个A求值姿态和开/闭盖，对新下件检查通过。
- light_qa.json：十二片实际导入膜片缓冲与R36相同，同输入响应保持；导光状态/释放保持。
- views/trim_fixed05_assembled_top.png 是装配近景；isolated图仅检查新件本身。已看整机和装配视图。

当前只完成成对的水平收口，曲面衔接、完整弯曲包边、部分尖折和整体材质仍未完成。不是AAA/用户验收；主App未更新，全模型目标active。

原视觉依据仍为 mouth_finish_r21 局部工艺图，无新增生图。下轮继续实际可见的曲面/弯曲边，同时主App接入必须遵循 native_integration_audit_r57 的现有接口盘点，不能直接替换旧I.glb。

最新连续视频：`continuous_r56/paired_trim_continuous_r56.mp4`，实际1890帧/63秒。源录音从头连续播放，空白谱面透明；录制清理尾帧不进入影片。详见 ../capture_cleanup_r56/README.md。
