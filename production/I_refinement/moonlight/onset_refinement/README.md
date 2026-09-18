# 月光时间校准：参考源审计、收尾局部修正与音源净化

2026-09-13，本轮没有更换正在展示的aefeda46原生包。开发数据已更新，后续导出会带入；完整三乐章、真实谱面和原录音文件均保留。

## 时间参考必须与谱面相同

旧全曲映射以LilyPond输出MIDI tick/PPQ当谱面quarter轴。第一/第二乐章的抽查尾部一致，但第三乐章末尾，谱面同时出现在q1050/q1052的高音和弦，在MIDI里出现在q1050.7135417/q1052.7135417。原始谱面元数据没有这个偏移，不能直接将MIDI演奏时刻当排版坐标。

`audit_score_reference.py`保存真正排版notehead的quarter/duration与MIDI尾部差异。注意谱面notehead还可能包含连音延续/装饰音组，不能把每个头都称作重新击键。`align_engraved_score.py`给出了以谱面时间轴为参考的独立和声DTW候选，但静态延音/重复段仍有歧义，未整条推广。

## 起音候选与实际采用范围

`refine_moonlight_onsets.py`对实际录音计算88键音区CQT与起音特征；保留旧映射作为时间搜索先验，动态规划维持顺序。稀疏事件扩大搜索范围，瞬态能量权重用于避免把低能量延音误当琴键起音。相关方法背景见[AudioLabs音乐同步](https://www.audiolabs-erlangen.de/resources/MIR/FMP/C3/C3_MusicSynchronization.html)。该方法不是带人工真值的精确对齐证明，候选分数不能冒充音准/同步通过。

实际看过记录音高能量、谱面和弦组成和独立宽带起音峰后，仅应用以下四个清楚的收尾锚点：

|乐章|谱面quarter|原时间|局部修正时间|
|---|---:|---:|---:|
|1|270|323.837602|324.661406|
|1|272|328.384003|327.680000|
|3|1050|485.120292|484.704943|
|3|1052|486.964460|485.668571|

时间单位为该乐章原录音秒数。参见 `review/I_refinement/moonlight/onset_refinement/tail_anchors_review.png`，绿色对应局部修正。仅重建第一乐章q268以后、第三乐章q1048以后的映射，保留进入点与原终点，其余全曲映射保持原样。新文件 `alignment1_tail_r2.json` / `alignment3_tail_r2.json`，旧文件不覆盖。状态仍estimated_requires_musical_review，没有宣称全曲逐音精确或听感验收。

`i_moonlight_tail_alignment_qa.gd`确认真实transport在四个录音时刻返回对应谱面quarter；暂停/恢复、跨乐章自然结束、当前喉口控制也已回归。它证明软件使用了局部修正，不是全曲音乐正确性证明。

## 第三乐章MP3净化

原MP3在完整ID3v1标签后多了36字节HTML注释。`clean_moonlight_mp3.py`只去掉这段非音频尾注，原文件保留，不重新编码。FFmpeg整段解码的174182400字节PCM完全一致。

Godot原文件解出21771648帧，净化后解出21772800帧；共有帧完全相同，后者恢复1152帧很弱的尾部（约26.12ms，峰值0.00003361）。净化后的Godot时长493.714294秒与完整PCM数量一致，不能把旧错误元数据时长当基准。证据在 `review/I_refinement/moonlight/mp3_clean/`，包含初次“时长必须相同”试验及后续实际AudioStreamPlayback整段解码对照，未隐瞒差异。

开发manifest已改为 `pitman_movement_3_clean.mp3`，保存original_audio/sha。全曲Godot时长961.036179秒，仍约16:01。音轨内容没有被裁剪，时间校准坐标保持录音原时间轴；已交付aefeda46包尚未更新。

## 接下来

继续核对装饰音、重复路径与其他弱起音片段；不能整批将新候选自动转为已校准。随后回到A整体艺术与B螺壳/C内芯，确保音乐功能始终服务于正确的海螺形体。全队列和共享底座约束不缩减。
