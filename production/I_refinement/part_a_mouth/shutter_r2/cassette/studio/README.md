# 喉口独立查看器：软阴影与光层次

当前源仍是 `I_front_guides.blend` / GLB；本轮没有改模型、形变数据或材质。实现为 `app/review/i_mouth_studio.gd`，仅接入独立喉口查看器源码，打包脚本已包含新依赖。没有改全局主 App 配置，也没有替换用户收到的旧 777613d0 预览包。

## 实际对照

在同一源、相机、灯光下分开比较关闭 SSAO、关闭法线贴图、关闭阴影、增大 normal bias、硬阴影、TAA。内衬的颗粒主要来自软阴影过滤；关闭法线不消除，增加 normal bias 无显著改善。关闭阴影只是定位，最终保留三盏真实阴影。参见 review/.../shutter_r2/finish_audit/。

进一步测试 LOW/MEDIUM/HIGH/ULTRA、4K/8K阴影图分配、光源阴影尺寸、全网格、空间超采样与TAA。TAA静态干净，但当前形变片的动态边缘和细孔变软；同姿态运动帧/稳定帧差异有独立记录，未将TAA静态结果当动画质量。最终采用 HIGH 软阴影过滤、4x MSAA、原生渲染比例、不启用TAA。微小阴影颗粒仍可在极近处看到，本轮不是彻底消除所有噪点或AAA验收。

本机 M5、1200×1000、短时关闭vsync的同一动态回放中，LOW/MEDIUM/HIGH/ULTRA帧耗时中位数约13.4/14.7/15.1/20.8ms，HIGH P95约16.7ms。它是局部场景端到端帧间隔，不是GPU独占时间，也不证明高DPI原生整机/全App性能。原GPU计时接口全返回零，已明确标记不可用，不能说0ms。

主光/补光/轮廓光改为8/4/5，轻微暖主光、冷补光，环境光0.40。保留原光源位置/面积和阴影尺寸，不用透明阴影来提亮。已有材质在这套独立灯光下更易区分；这不等于材质制作已完成。实际REST/MID/OPEN和导轮/归位槽近景在 `review/I_refinement/part_a_mouth/shutter_r2/studio_r1/`。

## 来源与接续

- 诊断：tests/collection/i_finish_audit.gd、i_finish_quality.gd、i_finish_motion.gd、i_finish_spatial.gd、i_finish_filter.gd。
- 最终本轮查看：tests/collection/i_studio_review.gd；studio_r1/review.json、checkpoint.json。
- [Godot 4.7 Light3D](https://docs.godotengine.org/en/4.7/classes/class_light3d.html)：PCSS、bias和blur的作用。
- [Godot 4.7 RenderingServer](https://docs.godotengine.org/en/4.7/classes/class_renderingserver.html#class-renderingserver-method-positional-soft-shadow-filter-set-quality)：过滤质量是RenderingServer级参数，因此当前只在独立进程使用，不能直接在主App逐模型调用并影响其他模块。

继续 A 工艺/材质、膜片声学演出及整体原图对照。A尚未完成，不能跳过B螺壳/C内芯或把局部渲染提升叫完整海螺还原。
