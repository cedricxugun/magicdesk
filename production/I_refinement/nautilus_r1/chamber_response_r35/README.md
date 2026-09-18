# 腔室导光随月光响应：R35光效候选

当前源 `blender/collection/I_nautilus_chamber_response_r35.blend / 2c885198dc995facded4026ccca758172d3d370fd065318b9d5edc9360e75bb8`，组件和运行时哈希见 `review/I_refinement/nautilus_r1/chamber_response_r35/checkpoint.json`。从R29实际源派生，所有顶点、实际渲染三角、材质槽、角点法线和变换保持，只给十二个实际声学框添加专属导光UV2；R30–33未通过的收边未接入。

## 设计、素材与实际演出

沿用 [腔室响应设计](../chambers_r1/chambers_and_response_r1.png)，新制 [导光光纹](../../../../app/assets/collection/art/I/chamber_response_r35/conductor_mask.png) 来自 **built-in image_gen**，[提示词](MASK_PROMPT.txt) 和 [来源清单](art_manifest.json) 已保存。图中错误的关闭喉片不作为模型依据；居中读谱与当前A继续保持。

光纹映射到已有声学框的曲面边缘，金光沿实际框体移动；没有生成漂浮粒子或改变机构位置。为周围金属增加三个小范围、开启阴影的点光源，能量随录音变化，关闭或停止后衰减至零。原工作灯和HDRI保留。

[25秒带音频实际回放](../../../../review/I_refinement/nautilus_r1/chamber_response_r35/take_r2/chamber_music_r2.mp4)：第一乐章从录音4.15秒开始，包含开口/开盖、谱面和腔室光响应、暂停/恢复、先收谱再合壳。

![实际播放中的腔室响应](../../../../review/I_refinement/nautilus_r1/chamber_response_r35/take_r2/frames/frame_270.png)

首次光效偏弱，已保留 `take_r1`，当前为 `take_r2`。没有覆盖之前已打开的视频。该回放是第一乐章片段，不是完整三乐章回放或原生鼠标验收。

## 真实音频数据

从已验证哈希的三乐章录音提取55–350、350–1500、1500–5000Hz三个能量带：11025Hz采样、1024点窗、220样本步长，完整记录分别16828/6594/24743帧。三个乐章共同参考分位数归一化，附带25ms上升和160ms回落包络。提取脚本为 `tools/audio/build_i_chamber_bands_r35.py`；记录来源与归一化参数在 `app/assets/collection/art/I/chamber_response_r35/response_bands.json`。

这是真实录音能量，用于视觉响应，不是逐音识别，也不验证乐谱对齐。十二框目前按分组响应三个频段；大小/频段更精细的艺术编排仍可调整。运行时使用现有播放器的同一local_clock，暂停不推进时钟，跳转直接读取对应位置。

完整三乐章仍加载，播放器保持0dB；旧未配置腔室数据的manifest正常返回零频段，不改变旧布局行为。对齐状态仍 `estimated_requires_musical_review`。

## 当前验证与剩余工作

`qa.json`覆盖三个录音的插值/跳转、十二材质分组、暂停时钟、停止/关盖收暗、网格资源不变及带阴影的受限点光源。首次QA误把平滑响应视为瞬时到位已修为充分稳定后检查；清理测试资源引用后退出不再报告泄漏。真实视频中的暂停/恢复/收谱阶段另有时钟与强度样本。R34居中谱面回归另存staff_regression.json。

**本轮仅完成腔室光效接入，未制作十二片内部膜片的音乐实体形变。** 当前还有05收边自接触、下侧过渡、材质/内部工艺、完整月光逐音校准、转动动力/供能、原生App和全部后续模型；不能称完整I或AAA。源几何保护也不代表旧模型所有缺陷都已解决。

没有新App或Git推送。接续使用本目录与HANDOFF顶部；完整队列active，I后J/K/L/M/N，G其余最后，B保留。
