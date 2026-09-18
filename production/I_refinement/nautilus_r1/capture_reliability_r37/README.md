# 整机录制稳定性与音画验证

模型仍是R36源e2a425d9、组件ec22caae，本轮没有改变模型或系统锁屏安全设置。

**当前已验证：[完整整机25秒音视频](../../../../review/I_refinement/nautilus_r1/chamber_motion_r36/take_e2a425d9/whole_final_r17.mp4)。** r16/r17连续两次均为实际解码750帧、25.000秒，分别57/59个采样点处于窗口不可绘制状态。暂停/停止音频静音、播放时钟漂移≤约0.040秒、抽查音频波形相关性0.995且偏移−0.008秒；最终帧匹配闭合截图。它不是全曲逐音校准或最终美术验收。

## 定位结论

逐帧诊断发现：窗口报告visible=true但window_can_draw=false时，处理帧仍增加，实际绘制帧不再增加。录制器仍写入上一张画面，等待frame_post_draw的动作协程则不再前进。PNG对照共留下3077帧，最后10帧文件哈希完全一致，而动作停在第35步，证据在 `review/I_refinement/nautilus_r1/capture_reliability_r37/duplicate_frame_proof.json`。

Godot主循环将自动绘制放在窗口可绘制等条件下，而MovieWriter的add_frame处于该条件之外，这与实测相符。[引擎主循环](https://raw.githubusercontent.com/godotengine/godot/master/main/main.cpp)

换Vulkan、关闭额外局部补光、改PNG输出、将窗口置顶或只调整动作更新阶段，都不足以解决这一机制；它们未被当作成功修复。是否由遮挡、窗口状态或系统环境触发不可绘制，不能仅凭本轮日志进一步断言。

## 当前录制方式

- 使用 `OS.has_feature("movie")` 识别录制模式。已用本机引擎确认，get_cmdline_args中录制参数已被过滤，不能用它判断。
- 在正常process_frame阶段更新动作，关闭此测试进程的自动渲染循环，设置视口UPDATE_ALWAYS；每个动作步明确调用force_draw(false, 1/30)，不等待依赖窗口可见性的自动绘制回调。[RenderingServer接口](https://docs.godotengine.org/en/stable/classes/class_renderingserver.html#class-renderingserver-method-force-draw)
- 固定录制视口为1040×940，与视频一致，避免方形截图和视频比例不同。初始画面先准备好，结尾不提前删除模型；由引擎退出时统一清理，防止最后写入空帧。
- 录制时用解码音频位置驱动谱面/腔室，不再叠加实时时间与输出延迟补偿。普通App播放默认逻辑保持，204项旧谱面回归通过。

录制命令无需额外--force-capture：

```
/Applications/Godot.app/Contents/MacOS/Godot --path app --rendering-driver metal --audio-driver Dummy --fixed-fps 30 --write-movie /absolute/versioned/path.avi --script res://../tests/collection/i_nautilus_mechanism_take.gd -- --report=res://../review/I_refinement/nautilus_r1/chamber_motion_r36/build.json --music-review --take-out=res://../review/path/to/action-records
```

保留--trace-frames供诊断；--diagnostic-auto-render可复现旧路径，不用于交付录制。模型、主光源阴影、膜片实体动作、真实谱面和局部导光都保留。

## 验证与边界

验证工具 `tools/audio/verify_i_movie_capture.py` 检查：实际解码/容器帧数、动作步与强制绘制调用对应、暂停/停止静音、播放时钟漂移、选定原录音片段的波形相关性，以及最终帧与闭合截图是否一致。内部Engine.frames_drawn和Godot结束日志不完整统计显式绘制，不能用其数字当视频帧数。

验证结果以 `review/I_refinement/nautilus_r1/capture_reliability_r37/checkpoint.json` 为准。r10/r12曾通过帧数但实时补偿产生超过0.1秒的时钟漂移；r14/r15修正了音频模式，但最终清理空帧检查失败，均不是最终媒体。旧whole_r1至r9问题录像和日志保留；没有静默覆盖已打开的视频。

这是当前整机演示录制路径的修复，不是完整三乐章逐音校准、原生鼠标交互、最终材质或AAA验收。当前R36模型的旧第七片3对基线自接触、05收边、下侧过渡、内部工艺、转动动力/供能与后续模型仍在队列中。没有新App或Git推送，全目标active。
