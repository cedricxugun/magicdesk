# 当前喉口的回声可见反馈与声音候选

本轮以内置image_gen补当前喉口的DEPART/TURN/RETURN分镜与独立灰度波峰贴图，原文件/提示词/哈希在本目录及art_manifest.json。分镜图的出射箭头方向生成错了，不能当空间真值；实际出射严格沿喉口Godot局部-Y，返回沿+Y。硬件、底座及模型源未因生图改动。

## 实际资产与实现

- `I_echo_wavefront.blend` / `wavefront.glb`：独立浅碗形光学载体，UV包覆专属crest_mask，不是Godot默认粒子或程序正弦圆环。
- `i_echo_presentation.gd` / `i_echo_wavefront.gdshader`：同一波包向外、略扩张、减弱并返回；中央透明，保留深度测试，未关场景遮挡。首版透视放大越界，当前传播0.42场景单位、扩张0.82→0.94，避免在参考相机中出框。
- 三个触须依次亮起，回程逆序；真实小范围局部光补口部，不用大面积glow或震屏。
- `send.wav` / `return.wav`：离线原创金属模态提示音候选，算法、参数和峰值在tools/build_i_echo_audio.py和audio_manifest.json。不是第三方录音，也不声称已做主观听感/最终音频验收。
- `i_mouth_response_rig`将新局部演示的回程延迟设为1.35秒；声波位置、返回音和膜片二次回弹共用acoustics事件时钟。旧未绑定模块仍用原延迟。

## 操作与检查

关闭将波包标记为取消并0.20秒淡出，声音也淡出；重新打开不复活旧波。已实渲验证发出/转折/返回和取消+重新打开，证据在review/I_refinement/part_a_mouth/shutter_r2/echo_r2/runtime。rig的30/60/144Hz行为检查随新时序重新通过，旧声学引擎回归通过。

`i_echo_audiovisual.gd`用Godot MovieWriter记录实际3D音频混合与画面。录像器取项目初始画幅，动态改变窗口不能据此改变录像画幅；最初1200×1000渲染被写为1040×940，候选存在比例改变，已统一为1040×940重新记录。早期echo_candidate/echo_candidate_1200及echo_response_d8e78848不得当最终可视交付。

当前画面仍偏细，效果强度与声音质感需要继续检查；源码已接到独立查看器并补打包依赖，但**已交付的5fcbfb3b原生包保持无音频/无此轮声场**。本轮演示不是完整I、月光播放或AAA验收。继续正常原生场景的声画检查与A工艺/艺术收敛，然后B螺壳/C内芯/正确整机。
