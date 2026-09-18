# 当前 Mac 喉口预览包

用户要求“出个新包我看看”。已从首片修正版独立派生三片联动源，保留新轴向触须、完整 GPU 拓扑与同一口沿；第三片入口转向加长后修掉局部自接触。

- 源：blender/collection/I_tongue_set.blend
- 组件：app/assets/collection/components/I_tongue_set.glb
- 运行：app/collection/i_tongue_set_driver.gd，逐片复用 i_tongue_fields.gd。
- 生成/精确哈希：review/I_refinement/part_a_mouth/shutter_r2/tongue_set/build.json。
- 当前包：dist/macos-review/MagicDesk-I-Preview-777613d0.app
- 当前压缩包：dist/macos-review/MagicDesk-I-Preview-777613d0-arm64.zip
- 构建与原生查看记录：review/I_refinement/part_a_mouth/shutter_r2/tongue_set/native/。

三片有错峰卷入、逆序伸出。源网格封闭/正体积，以及本轮源动画采样的六张薄层互相、对其他表面、自表面接触均通过限定检查。包只放入当前查看所需资源，Apple Silicon arm64，独立暂存项目导出；主工作 registry 与日常 MagicDesk 未覆盖。打包入口 tools/build_i_mouth_review_macos.py。

用户可点击部件或空格开合、拖拽旋转、滚轮缩放，L 循环、R 复位视角、Esc 退出。应用窗口按当前屏幕 backing scale 定大小，内有“仅喉口部件、尚非完整海螺”的提示。此查看器不是完整 I 或全 App 的新正式版本；传动机匣、归位承座、完整外壳和月光模块仍待制作/整合。

已实际启动导出的 .app 并通过 CUA 看见原生窗口、中文说明和点击后全展开的三片。签名/压缩包校验通过；其余键盘、拖拽和滚轮不要当作已做完原生验证，具体边界见 native_check.json。命令行诊断参数需放在 Godot 的 `--` 分隔符之后；正常打开不需要任何参数。

接下来继续三卡匣的完整承座/导向/电机与传动、各部件连接及多角度精修。源/接触通过仍不是全动态/全部固定零件配合或 AAA 验收。
