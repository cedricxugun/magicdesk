# 薄片边缘法线与拉丝坐标修正

仍使用 `I_diaphragm_response.blend / GLB`、既有三片路径和专属镍拉丝素材。没有重做形体、增加新装饰或改变共同底座。本轮修复的是动态着色丢失源材质细节的问题，依据原有图稿与同姿态源材质对照。

## 两次对照揭示的问题

旧 shader 以整张薄片的解析法线覆盖所有顶点，原来边缘的平滑法线也随之消失。实际同相机渲染能看到：StandardMaterial 的细亮边缘在动态版本里变成平面、表面缺少工艺层次。

首次检查还发现动态切线/副切线不正交，局部归一化点积达0.677。导入UV的V方向虽与参数w相反，Godot导入后的切线坐标也保留相应约定；不能凭UV方向直接翻转贴图。只把坐标正交化的独立候选保留在 `app/review/i_tongue_frame_candidate.gdshader`，它不足以恢复被丢掉的边缘法线，没有作为最终修正。

## 已进入开发运行时的修正

`i_tongue_fields.gd` 为每个顶点存入静止参考坐标架：CUSTOM0包含切线和原始方向符号，CUSTOM1包含参考法线。采用Godot要求的PackedFloat32Array格式，共新增约1.97MiB顶点数据。原位置、索引、UV、实际厚度与运动纹理均不改，继续保留完整拓扑且不使用REST自动LOD。

`i_tongue_fields.gdshader` 在每个动画姿态求当前坐标架，将原有NORMAL/TANGENT/BINORMAL从静止坐标架旋转到当前坐标架。因此原有边缘法线、拉丝方向和材质层次一起随片运动。沿用原有纹理读取数量，没有为静止参考再增加一套逐顶点纹理读取。保留 imported-LOD 诊断模式的显式旧路径，实际当前喉口使用新路径。

## 证据与边界

- `review/I_refinement/part_a_mouth/shutter_r2/foil_frame/baseline.json`、`orthogonal_candidate.json`：实际导入网格和UV的只读审计。
- `attributes_qa.json`：六张薄片各12274顶点、73632索引；新增属性后仍有真实表面。位置/索引/UV与源完全一致。法线/切线与**原有无LOD的ArrayMesh重建**逐字节一致；源到这个既有重建过程本就有约0.00013的法线编码误差，不能声称所有源属性字节不变。
- `transport_float_r2/` 与 `final_shader/`：实际Metal、同一灯光/相机/纹理的源REST、旧动态材质和新动态材质对照，以及25%/50%展开视图。REST近景恢复了源的边缘高光；原候选近景全图RGB RMS差约8.90，新坐标架版本约0.00745（8位量纲）。这只是同源同姿态渲染差异，不能当作与概念图的还原度或艺术分数。
- `current_mouth/controller_qa.json` 已补真实薄片表面检查，并回归完整月光的等待、暂停、跨章、收谱/合口。它仍不替代原生完整16分钟、精细谱位、听感或整机验收。

初次CUSTOM属性误传成字节数组被Godot拒绝，造成空网格，旧控制时序测试却仍打印true。该轮无效，错误日志和拒用说明保留于 `custom_array_trial/`；随后修正格式，并补实际表面/顶点/索引检查，再重新渲染验证。没有把错误试验导出给用户。

此项不是完整A美术或AAA验收。口沿工艺、后部结构和整套运动仍需继续收敛，再处理B螺壳、C连续内芯和原选完整海螺。月光完整三乐章与真实谱面保留。

实现参考：[Godot spatial shader坐标与法线接口](https://docs.godotengine.org/en/stable/tutorials/shaders/shader_reference/spatial_shader.html)。


## 本机新版

`dist/macos-review/MagicDesk-I-Preview-1d4b2301-e54f5593.app` 与同名-arm64.zip（129,842,887字节）。已实际看到新边缘高光，开合输入包含部分展开时反向；点投射器播放、点谱面暂停，51.618817秒处音频/谱位冻结且膜片归位。当前仅此预览运行，四个旧预览已正常退出，文件保留。

证据 `review/I_refinement/part_a_mouth/shutter_r2/foil_frame/native/`。这是有限原生操作和外观验证，不是连续全部动作视觉验收、完整16分钟原生听验或全App性能。日常主App没有替换。
