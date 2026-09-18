# R57 接回主App前的实际接口盘点（只读，尚未接入）

本次从当前工作树确认：`app/assets/collection/registry.json` 的 I 仍指向 `models/I.glb` 和 `I.json`。当前R55海螺是独立身体组件 + A口部 + R43光学附件 + 独立音乐/膜片控制，不是可直接替换这个旧GLB的同名资源。

`app/collection/module.gd::setup` 按旧 `data.parts/controls/motions` 名称找节点，`_collect` 会为多数网格创建三角拾取体，并把所有 StandardMaterial 改成通用 surface.gdshader。直接改registry资源路径会丢掉专用材质/动作绑定，并可能卡在大量细节三角碰撞构造，不能这样宣称接入完成。

`app/collection/i_runtime.gd` 还是旧面板/虹膜/压缩腔的独立驱动；不能让其旧节点表驱动R55。当前 `i_moonlight_controller.gd` 可处理A音乐行为，但主module尚未实例化当前完整组合。现有演示直接加载新组件和专用驱动，不证明App路径可用。

接入需新增明确的I组合适配层，保留当前几何/材质，绑定Body开合、A口闸、音乐/谱面、腔室与镜片；复用真实公共底座/机械选择入口和已约定控制区。需要补本机实际点击、切换/取消、停止与回收，以及退出音频资源的检查。不可覆盖其他款或把新模型直接塞给旧元数据。

这只是接口盘点，未修改registry、未打包App。当前制作继续cap_lower_trim_r55/README.md；完整目标不缩减。
