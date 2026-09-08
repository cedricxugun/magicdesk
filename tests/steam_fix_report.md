# 开蛋蒸汽卡顿与节奏修复 · 1.3.1

测试机器：RTX 3060，1920×1400固定三维视口，Windows原生逐像素透明显示。保留模型、抗锯齿、物理密度缓存、体积采样质量、蒸汽浓度与现有光效。

## 查到的具体原因

1. 物理蒸汽错误使用了花瓣动画的变速时间。`choreography_time()`为抵消原始开瓣曲线做逆变换，在显示时间0.85秒附近让模拟时间速度骤降至接近0；缓存中的50毫秒流体过程被拉长到约604毫秒，产生“冻住后再加速”的观感。现将蒸汽与待机逸散改为真实秒时钟，机械仍保留3.5秒开瓣节奏。
2. `Image.get_used_rect()`在Godot主线程逐帧扫描完整图像。实测扫描中位耗时10.584ms，发布整帧合计12.18ms；同一测试GPU渲染中位仅8.253ms。现将原RGBA交给原生接收线程，直接检查Alpha字节并裁剪，主线程不再执行颜色扫描。
3. 原生端每帧分配大像素数组，使40秒测试出现约331次第2代GC。现复用有界像素缓冲；显示、异步截图与录像都持有帧引用，只有所有使用者结束后才回收数组。裁剪始终保留Alpha为1的浅蒸汽像素和2像素边距。
4. 调整Godot读回分块为512像素、staging块为4096KB，减少完整画面读回的分块工作。预载按钮音效，并取消机械动作中无意义的设置文件写入。

## 实测

相同全套按钮测试的A/B：旧路径47.48 FPS；仅把Alpha裁剪移至原生端后59.13 FPS。对应数据：`stutter_baseline/bridge_summary.json`、`native_crop_only/bridge_summary.json`、两目录中的`performance.json`。这些全功能检查含Windows命中检测和截图，其个别峰值不应直接当成日常播放成本。

修复后的独立连续开合测试关闭截图与Windows网格命中审计，保留实际按钮输入、完整渲染和透明合成，连续打开三次：

| 打开次数 | 5秒内显示帧数 | 帧间隔中位 | P95 | 最长间隔 | 打开期间第2代GC增量 |
| --- | ---: | ---: | ---: | ---: | ---: |
| 第一次 | 300 | 16.635ms | 18.193ms | 32.128ms | 0 |
| 第二次 | 299 | 16.631ms | 18.599ms | 22.438ms | 0 |
| 第三次 | 300 | 16.677ms | 17.945ms | 23.014ms | 0 |

全程59.86 FPS，帧间隔中位16.66ms、P95 18.26ms，最大32.13ms。尚有少数单帧波动，不宣称零卡顿或跨设备始终锁60。数据在`steam_wall_final/`。

三次开启的0.85–1.15秒关键区间共54个连续采样，物理缓存时间与动画显示时间增量之比均为1.0，原来的近零速冻结已消除。

最终已打包EXE加录像的全功能检查：2513帧、0空白帧、0透明合成错误；透明区与实体点击全部通过，窗口句柄保持不变，底座漂移0像素，关闭完成约3.79秒。结果见`steam_fix_release/native_verification.txt`，实际录像见[steam_fix_demo.mp4](../review/steam_fix_demo.mp4)。

## 参考与方法

- [Godot官方：管线编译卡顿与监测](https://docs.godotengine.org/en/stable/tutorials/performance/pipeline_compilations.html)。本项目已有管线预热；这次使用分段计时确认主要问题在本地时间映射和CPU扫描，未凭“第一次出现”直接归因于shader。
- [Godot官方Image实现](https://github.com/godotengine/godot/blob/master/core/io/image.cpp)：定位`get_used_rect`与`get_region`的扫描和复制路径。
- [Godot官方：StreamPeer.put_data](https://docs.godotengine.org/en/stable/classes/class_streampeer.html#class-streampeer-method-put-data)：该调用在数据发送完成前会阻塞。
- [Godot官方：RenderingDevice异步读回](https://docs.godotengine.org/en/stable/classes/class_renderingdevice.html#class-renderingdevice-method-texture-get-data-async)：异步调用仍有带宽和在途帧成本。
- [Godot官方：staging分块配置](https://docs.godotengine.org/en/stable/classes/class_projectsettings.html#class-projectsettings-property-rendering-rendering-device-staging-buffer-texture-download-region-size-px)。
- [Godot论坛：Compositor纹理保留与性能讨论](https://forum.godotengine.org/t/optimizing-keeping-rendered-texture-to-the-next-frame-in-compositor-effect/143864)。用于排查方向，最终改动依据本项目计时结果验证。

## 复查方式

先构建开发主程序，再运行像素边界测试：

```powershell
.\native\build_native.ps1
powershell.exe -NoProfile -File .\tests\test_native_alpha_crop.ps1
```

已导出的EXE支持诊断参数：`--steam-test --profile --diagnostics=绝对输出目录`会执行三次开合并保存原生帧间隔及GPU/CPU分段数据；不带这些参数是正常交互模式。`--self-test`负责独立的功能与透明点击检查。
