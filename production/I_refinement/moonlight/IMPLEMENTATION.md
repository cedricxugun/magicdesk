> 2026-09-13 最新接续：current_mouth/README.md。已接到当前IAM喉口原生预览；下文保留旧独立模块制作记录。历史full_take已finished/passed，不重启旧会话39781或PID98222。精准音乐对齐仍未验收。

# 月光全三乐章：独立乐谱和播放候选（2026-09-12）

本轮已有真实源谱排版、展开顺序、录音候选、估计对齐数据和独立音频控制。尚未接入日常App的I；海螺口部结构、全曲谱带投射、音符高亮、实体控制及三乐章机械演出未完成，不能说音乐海螺已交付。

## 已执行

- `tools/music/prepare_moonlight_scores.py` 用独立 LilyPond 2.26.0 将保存的Mutopia源转换为现行语法，生成连续SVG与MIDI；原始源未覆盖。
- 保留一/三乐章全部音符内容、展开volta反复；第二乐章补入书面 `Allegretto D.C.` 所要求的返回段，返回段不重复内部反复。该演奏顺序仍需与选定录音逐段听验。
- 旧 `override-auto-beam-setting` 无法由convert-ly自动迁移，改为quarter-note triplet grouping的beatBase/beatStructure配置。仍有旧排版源留下的指法/连线警告，需继续校勘，不把编译成功称作乐谱终审。
- 给原SVG音符写入pitch、score moment、duration、bar与voice，并抽取位置。`tools/music/extract_score_metadata.py` 保留少数不产生可见字形的合并音符为visible=false，未凭空补假符号。
- Godot会漏掉SVG原始text；改用LilyPond Cairo backend将所有字体轮廓化，且序列化必须保留`xlink`前缀，否则Godot丢失use引用字形。三个乐章首段PNG已实际看图，包含谱号、调号、音符、休止、三连音数字和动态记号。只是截窗预览，不是全谱逐页视觉验收。
- Paul Pitman/Musopen三段音源候选齐全；第三乐章采用Commons元数据指向的Archive原MP3，约256kbps。FFmpeg全文件解码无所报错误，不代表音质听验。
- `tools/music/align_moonlight.py` 以录音CQT chroma与展开MIDI估计score-quarter到recording-time的映射。三个候选在review目录；状态始终是estimated_requires_musical_review。自由速度、踏板、反复与延长音存在匹配歧义，不冒充逐音精准同步。
- `app/collection/i_music_transport.gd` 是未绑定主模块的Node：完整三乐章顺播、声音时钟、暂停/恢复、前后seek、跨乐章、结束/停止。素材和候选warp在`app/assets/collection/art/I/moonlight_candidate/`。

## 证据

- `review/I_refinement/moonlight/notation_inventory.json`：1183 / 1062 / 6734个音符头记录（含连音与少量不可见合并字形，不能当MIDI发声音符数）。展开后小节号范围1–69 / 1–141 / 1–264；包含弱起和反复展开编号，不能说第二、三乐章原谱就是这么多小节。
- `engraving/build.json` / `engraving/engraving*.log`：三个源编译结果及警告。
- `review/I_refinement/moonlight/alignment*_candidate.json`：精确输入哈希、时间轴和候选对齐；任何乐谱或音源变更都要重新核查输入。
- `review/I_refinement/moonlight/transport_check.json`：实际Godot/Dummy音频，暂停不走时、暂停中倒退、恢复、跳到各乐章结尾后自然换章、最后结束一次、重新播放/停止均通过。测试跳转到结尾，不是全16分钟验证。
- Godot解码器报告三段长度335.769226 / 131.552658 / 493.688171秒，合计961.010056秒，约16分01秒。Librosa/FFprobe对MP3末尾时长略有差异，音频播放时钟以实际Godot流为准，末尾静音不强行用另一解码器时长延长。
- 真正不跳转的全长实时播放检查已另启动，写`review/I_refinement/moonlight/full_take.json`，日志`/tmp/magicdesk-music-full-take.log`。只有status=finished且passed=true才能算这一项完成；Dummy输出仍不是听感/原生界面或谱面同步验收。

## 工具与复现

独立工具包来源/哈希在lilypond_toolchain.json，当前位置`/tmp/magicdesk-lilypond/lilypond-2.26.0/bin/lilypond`；当前Python环境`/tmp/magicdesk-music-venv`，依赖版本在requirements-music.txt。Homebrew安装因已有`/opt/homebrew/opt/freetype`真实目录冲突而停止，未删除/覆盖该目录；后续不要重试清理该目录，使用独立包。

1. `python3 tools/music/prepare_moonlight_scores.py --lilypond <独立lilypond路径>`。
2. 对每个生成的moonlightN-staff.ly执行 `lilypond -dbackend=cairo --svg -o <engraving/moonlightN-cairo> <source>`，保存日志。
3. `python3 tools/music/extract_score_metadata.py`；再运行`tests/collection/i_notation_render.gd`生成真正可见字形预览。
4. 用requirements-music环境执行`tools/music/align_moonlight.py --movement N`，再逐段听验/修正，不直接提升候选warp为最终。
5. `tests/collection/i_music_transport_check.gd`为短控制检查；`tests/collection/i_music_full_take.gd`为约16分钟完整解码/时钟检查。

## 下一项

先核对仍在跑的full_take进程/报告。继续制作全谱分块和紧凑口部投射：保留真实音乐符号，长演奏说明/指法可单独作详细查看，不能用缩得不可读的大谱页填口部。至少逐段对照真实录音核查开始、反复/Da Capo、慢下/延长音、乐章尾；粗估DTW不能承担最终同步质量。

并行于音乐素材的主模型方向仍是R9之后修口部过宽平环、实际深度与连续内芯可见性，之后全部机构连接/动作/取消验证。保持原始选图与真实共享底座。I后J/K/L/M/N，G其余最后，B保留；目标未完成。

## 全长检查修正

首个Dummy长测在225秒墙上时间只有约217秒音频进度，说明Dummy线程存在约3.8%的输出步进延迟。原先曲长+20秒会在尚未播完时误报，故保存full_take_dummy_clock_trial.json/log，主动停止PID97784，改为20秒无音频进度和1.25倍曲长+30秒硬上限。新session39781/PID98222于03:13:12+08开始，接续需查同一进程与新full_take.json；仍非真实扬声器/听感或同步验收。
