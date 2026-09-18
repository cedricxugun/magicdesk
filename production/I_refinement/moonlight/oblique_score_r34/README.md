# 当前整机斜角下的居中月光谱面

主体仍采用R29 `e5fe1561`，没有接入未通过的前沿收边。光学源 `blender/collection/I_oblique_score_r34.blend`，SHA256 `2a82f42dc8cbb4727843425b0ff9787d9527d458d422b85db4e487751c4b6611`；布局在 `app/assets/collection/art/I/moonlight_candidate/oblique_score_r34/layout.json`。精确来源及范围读 `review/I_refinement/moonlight/oblique_score_r34/checkpoint.json`。

## 实际结果

[25秒带音频整机片段](../../../../review/I_refinement/moonlight/oblique_score_r34/take_r1/moonlight_whole_r1.mp4)：口闸/上盖开启、第一乐章从录音4.15秒处播放、暂停、恢复、收谱与按序合壳。截图和真实transport时钟记录在同一目录的frames。750个动作帧，编码751帧/30fps；完整时长25.033秒。

![实际整机中央读谱](../../../../review/I_refinement/moonlight/oblique_score_r34/whole_view/views/relation_music.png)

谱面仍以A口部轴心为中心，宽由1.16改为1.42，高由0.40改为0.50；源局部深度从中心−0.435收回到−0.348，扫描面为−0.352，保留在实际触须前方。实际两个投射器、支架、螺钉和触须位置保持，三条光路仍从真实尖端连接到中心。

金色扫描复用原内置生成的 `central_scan_r1/filament_mask.png`。素材核心在1254像素图中仅约10列明亮像素，原映射到整机时太细；现在在专属网格上采样其中央14%宽度，形成可见金色扫描。颜色仍由既有扫描材质合成，未用新随机粒子替换。白色未播放、淡金已播放和中心亮金沿同一真实谱位变化。

布局的scan_gain=1.8、score_gain=1.35、filament_u_span=0.14仅作用于此候选，其他布局默认值保持1。shader/driver增加可选参数。不是重新编码音频或提高系统音量；完整三乐章仍由0dB播放器加载，谱时精度仍标记 `estimated_requires_musical_review`。

## 验证范围

新布局204个三乐章首尾/跨贴图采样通过，中心谱位、透明补白、缓存、暂停时钟和膜片移动后的光路端点检查通过；旧布局212采样回归通过。真实导出AAC在播放/恢复段非静音，暂停/停止段为数字静音，详见 `take_r1/audio_check.json`。演奏片段平均约−36.8/−34.4dBFS，是第一乐章轻奏，未据此声称全曲听感通过。

这25秒证明当前组合下的片段行为，不代表完整16分钟演奏测试、全曲逐音校准、全部音乐联动、鼠标原生操作或AAA验收。后续补实际内部声学响应、最终材质光影、完整收边、转动动力/供能和原生集成。

本轮未新增生图，沿用已经存在的内置中央扫描设计/光纹与真实LilyPond谱本；未调用外部图片API。无新App、无Git推送，完整队列继续active。
