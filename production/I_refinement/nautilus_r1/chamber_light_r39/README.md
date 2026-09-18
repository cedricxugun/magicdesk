# R39 开壳导光可读性修正

当前接续组合：R36 主体与真实膜片动作 + R38 主体材料 + R39 **layout_r3 / channels** 导光。源 e2a425d9，组件 ec22caae；几何、机构、口部、居中谱面和真实底座不变。新独立预览已验证，**主 App 未更新**。

## 用户问题与修改

用户指出开壳后内部光带不够亮，部分没亮。旧版发光量直接乘各频段能量，轻奏或高频弱时一整组接近熄灭；图像光纹采样也在光带边缘偏离亮芯。旧图本身的横向亮芯是连续的：1254 个横向样本最小约 0.957、均值约 0.982。当前槽中心对应的旧采样均值约 0.345；数据在 channels/mask_audit.json，不能把纹理检查当成全角度几何覆盖证明。

采用已有腔室响应图及 R35 内置生成的专属 conductor_mask.png，不新增外部生图。开壳基线 .16，播放基线 .45，再叠加原录音频段响应；约 .20 秒过渡。暂停回到微亮，闭合门限后材质发光和三盏带阴影局部灯严格归零。频段为零也不会使某组导光熄灭。物理膜片仍只由录音驱动，照明基线不产生形变。

前两个候选提高亮度却让整片金属边过白，保留其 views 作为失败对照，不采用。当前第三版将原光纹亮芯移至框边内侧 q=.045，限制在半宽 .026 的细槽范围，发光强度 20，色比 1/.38/.065。流动只调制音乐增量、不压灭基础亮度。原镍筋、金属框、机械遮挡与真实孔洞保留；没有把整片金属改成发光板。仍需后续工艺与全角度审视，不声称所有几何接头连续或无瑕疵。

## 当前文件与证据

- 组合描述：`review/I_refinement/nautilus_r1/chamber_light_r39/channels/build.json`
- 配置：`app/assets/collection/art/I/chamber_light_r39/layout_r3.json`
- 运行时：`app/collection/i_chamber_music_response.gd` 与 `i_chamber_conductor.gdshader`
- 实际组合截图：`channels/views/relation_chambers_quiet_music.png`、`relation_chambers_open_idle.png`、`chambers_quiet_close.png`
- 视频：`channels/take_r1/light_music_r1.mp4`，实际 750 帧 / 25 秒。第一乐章片段，含开壳/播放/暂停/恢复/收谱/合壳。
- `channels/light_qa.json`：十二组导光，三乐章录音频段采样与零高频输入，开壳/暂停/闭合，释放后材料恢复；相同输入下膜片与 R36 对照的最大差为 0。旧 R35 音乐及 R38 材料 QA 也重新通过。
- `channels/take_r1/validation.json`：解码帧数、动作/绘制步、暂停/停止静音、抽查录音相关性约 .9954、偏移 −.008 秒和最终闭合帧一致性通过。MovieWriter 控制台计数 741 不等于实际文件 750；以实际解码为准。
- `channels/runtime_snapshot/` 与 checkpoint.json 留存本轮确切运行时及哈希。旧 layout/layout_r2 不作接续入口。

本轮解决导光的亮度逻辑与细槽表现，不是全曲逐音、原生操作或 AAA 验收。继续第七膜片旧基线接触、05 收边/下侧过渡、内部工艺/材质、动力供能、完整月光与中央扫描校准，再接原生。I 后 J/K/L/M/N，剩余 G 最后，B 保留；全目标 active。
