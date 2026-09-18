# 海螺口同步五线谱与完整音乐（贝多芬月光全曲已选）

2026-09-12 用户提出：运行状态在海螺口滚动五线谱，与谱面对应的音乐同步，播放完整作品；询问海相关经典曲目和月光曲时长。用户随后回复“用月光曲吧”，承接刚才推荐，确定贝多芬《月光奏鸣曲》Op.27 No.2完整三个乐章。具体录音、谱本、逐音/小节时间映射尚未选定，不声称已经实现。

设计建议：保留原始逐片开壳和可见连续内芯；喉口前沿内部显现一条薄的曲面谱带，当前小节清楚，演奏到的音符短暂点亮。钢琴使用高/低音双谱表，正常桌面尺度只显示局部连续小节。内芯不被不透明大屏遮盖；壳片随乐句缓慢起伏，音叉/膜片承担较快响应。闭合、暂停、切换的声音与谱面同步收束。此方向需另做原图约束下的运行状态效果图。

工程路线：可读数字乐谱决定真实音高/时值/排版，选定完整录音配小节/音符时间映射，音频播放位置为主时钟并补偿输出延迟；避免单独累计动画时间漂移。古典演奏自由速度不能靠固定BPM或随机装饰音符冒充同步。可选另一条路线是同一演奏数据同时生成钢琴音频与谱面，但实际音色、踏板和乐句质量必须听验。AI出图只制作谱带外观/材质/演出，真实可读乐谱采用确定性排版。

查到的时长实例：贝多芬Op27No2三个乐章5:15+2:19+7:38=15:12（Harmonia Mundi目录；具体录音会不同）；德彪西Clair de lune DG赵成珍视频5:33；拉威尔海上孤舟乐队版TSO标7分钟；德彪西大海LA Phil约23分钟。月光曲需区分贝多芬奏鸣曲全三乐章与德彪西单曲；不能把第一乐章当作完整奏鸣曲。

来源：
- https://www.harmoniamundi.com/wp-content/uploads/pdf/beethoven-complete-piano-sonatas-HMX2908880.93-en.pdf
- https://www.deutschegrammophon.com/en/composers/claude-debussy/videos/debussy-clair-de-lune-450760
- https://www.tucsonsymphony.org/program-notes/ravel/barque-sur-ocean/
- https://www.laphil.com/works/la-mer
- https://docs.godotengine.org/en/stable/tutorials/audio/sync_with_audio.html

实现尚未开始。最终音源和谱本另选；联网预览链接不是可打包的App资源。
