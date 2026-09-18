# R56 连续录制的退出清理

R54在仍播放时退出出现Ogg资源遗留。最小音频复现确认涉及 AudioStreamPlaybackOggVorbis、OggPacketSequencePlayback、OggPacketSequence 和 AudioStreamOggVorbis；停止后留混音循环释放则不出现该警告。证据在 review/.../cap_lower_trim_r55/cleanup_evidence。

当前录制脚本先完成并记录所有展示帧，让最后一帧经过MovieWriter，再停止音频并留8个处理帧释放。正常演示不插暂停/恢复或自动收壳。原始AVI含9个清理尾帧，它们必须通过 **tools/audio/export_i_presentation.py** 排除；该工具只保留从时间0开始的声明帧数，不剪中段，并拒绝超出预期范围的大量多余帧。

使用步骤：

1. `i_nautilus_mechanism_take.gd --music-review` 默认连续片段；暂停/恢复/收壳测试必须显式 `--test-pause-resume`。
2. 用 `export_i_presentation.py --raw RAW.avi --take frames/take.json --out FINAL.mp4` 导出。不要直接把带清理尾帧的AVI整段转码当展示。
3. 用 `verify_i_movie_capture.py` 核对导出片段。

短复录330帧/11秒和完整复录1890帧/63秒均通过相应音视频检查；verbose日志没有再出现ObjectDB泄漏/资源仍占用的警告。仍有Metal的RGB→RGBA格式转换提示，不声称日志零警告。完整片段对原15/17/20秒及后续音轨窗口进行源录音匹配，展示结束仍在播放，清理停止位于截取范围之外。

本轮处理的是录制器退出路径，不是主App原生退出或全曲逐音验收。主App生命周期须另行验证。
