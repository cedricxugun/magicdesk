# 月光：中央谱带、金色读谱与音量

2026-09-13。最新用户位置修正已进入独立开发预览：整条谱带中心为 A 喉口局部中心轴，光学面在触须前方。旧下置布局及 `take_r1` 保留但不再交付。

## 当前可见结果

- [22 秒实际渲染与音频片段](../../../../review/I_refinement/moonlight/central_scan_r1/moonlight_center_r2.mp4)：第一乐章片段、暂停、停止与收回；不是新整机包。首段跳过录音开头约 4.15 秒，完整录音本身未裁剪。
- [中央位置实际图](../../../../review/I_refinement/moonlight/central_scan_r1/centered_views_r2/m1_q32.png)。透视下，触须与前方谱面有正常视差，不能用屏幕截图中的像素重合代替真实空间重合。
- [播放/暂停/收回的时钟记录](../../../../review/I_refinement/moonlight/central_scan_r1/take_center_r2/take.json)。视频 1321 帧、60 fps、22.016667 秒，H.264 + AAC；音频峰值约 -21.8 dBFS，是第一乐章较轻的开头片段。

## 实现

白色真实双谱表从右向左经过固定中心 0.5；当前谱位亮金，经过部分淡金。开头/结尾用透明空白补足窗口，不复制末页或把播放位置推向边缘。未开始读谱时保留白色；暂停不推进谱位，扫描转为低亮。

专属光纹先由内置生图生成，再映射到 Blender 制作的四条光学承载网格。三条短光路来自实际 `IAM_TineRoundedAxial_0/1/2` 的实测前端，汇聚在谱面中心；第四条覆盖两行谱表。驱动只修正端点的真实膜片位移，不把整束光跟着触须平移。glTF 的 V 翻转已按导入网格核对。两个实体投射器保留下方已检查的安装点。

播放器默认从 -16 dB 改为 0 dB，去掉额外衰减；未改系统音量、未压缩钢琴动态、未更换或重编码录音。完整三乐章样本峰值依次约 -13.6、-5.2、-2.2 dBFS，见 `volume_review.json`。完整时长仍约 16:01。

当前全曲录音/谱本映射仍是 `estimated_requires_musical_review`。中心位置固定和颜色正确不等于全曲逐音精确；此次没有把算法候选整批宣称为音乐校准通过。

## 图稿与专属资产

全部为 **built-in image_gen**，未使用外部图片 API。

- [扫描分镜](scan_states_r1.png) / [提示词](PROMPT.txt)：功能/色彩参考。下置位置已被用户的居中要求覆盖，生成谱面仅为示意，运行时继续使用真实 LilyPond 谱面。
- [光纹素材](../../../../app/assets/collection/art/I/moonlight_candidate/central_scan_r1/filament_mask.png) / [提示词](MASK_PROMPT.txt)：金色在实时合成时赋予，原素材为灰度光纹。
- 来源、哈希、限制见 [art_manifest.json](art_manifest.json)。

## 范围与接续

源：`blender/collection/I_central_scan_optics.blend`；布局/组件：`app/assets/collection/art/I/moonlight_candidate/central_scan_r1/`。当前哈希见 `review/I_refinement/moonlight/central_scan_r1/build.json`。

`qa.json` 覆盖三乐章 212 个边界/位置采样、缓存、暂停与真实触须端点；`mount_check.json` 为 9 个 A 源姿态的实体投射器检查，两个安装销与内套的声明配合单列；不涵盖全部整机结构。居中后 `controller_qa.json` 已重新通过，覆盖准备完成后播放、真实谱面点击、暂停、跨乐章跳转、淡出中重启与停止后收回。最后的音频测试等待混音线程完成停止，已无退出时的 Ogg 残留警告；这不是听感或全曲同步验收。

当前日常 App 和用户已打开的 C3 原生包未替换。独立新鹦鹉螺形体视图已接中央布局，但新主体还处于未锁定形体阶段。下一项先继续新主体与展开内部，随后把中央读谱/音量带入新的完整原生候选；包装时必须包含 `i_moonlight_scan.gdshader` 和专属光纹，不能漏资源。
