# 组合响应、源到 GLB 形变及实测开口

当前仍为独立 `I_diaphragm_response`，准确哈希见 review/I_refinement/part_a_mouth/shutter_r2/diaphragm/checkpoint.json。没有替换日常App或已交付777613d0包。

## 修正一处漏检和实际碰撞

原手动行程检查修改自定义属性后只调用view_layer.update，未显式标记驱动对象更新，部分依赖图没有刷新。之前“九幅值无新增接触”的证据不足，不能继续沿用。检查现在对驱动调用update_tag，并断言实际location或形变权重与请求值一致。

刷新后发现头部在正向受压行程与固定轴颈前缘相碰。当前将固定轴颈前缘后退0.013场景单位，留出头肩的±0.006行程，保持轴向孔座/触须和三片路径。已重新做实际受压正面观察。旧 `suspension_f3a5fec3.mp4`保留为旧源的隐藏外罩机构演示，不能作为这次轴颈修正后的整机证据。

## 当前独立证据

- `suspension_check.json`：九个真实刷新幅值，全部随动悬架对固定结构、自交、压座间隙。设计配合的弹簧后端/悬边接触保留。
- `combination_check.json`：17个三片开度×5个膜片行程，所有薄片对随动/形变悬架表面。包括源驱动实际值断言，不是假设属性设置成功。仍不覆盖连续扫掠或完整拆解。
- `source_suspension_points.npz/json` 与 `glb_geometry_check.json`：八个行程、四个形变网格和中心头部，实际Blender求值顶点与GLB二进制POSITION/形变增量/节点变换双向比较。支持稀疏accessor，参照[Khronos glTF 2.0](https://github.com/KhronosGroup/glTF/blob/main/specification/2.0/Specification.adoc)。不是GPU法线或原生输入验收。

## 开口测量与接续

`measure_i_aperture.py` 从实际六张薄片的求值表面做轴向射线测量：口径半径0.735，固定中心排除半径0.095，射线结束在护网前。33个开度用128×128网格，五点另以256×256交叉核对。当前闭合仍有约64.7%的这一定义下的可通过投影区域；初段转向时稍收窄，全开接近100%。这是护网前的投影遮挡率，不含护网孔隙、压损或实际声学导通率。

`app/assets/collection/art/I/diaphragm/aperture_profile.json`保存来源组件哈希及采样。`i_acoustics.gd`新增显式绑定实测曲线，出流与共振计算共用该曲线；未绑定的历史模块保留原行为，主App没有暗中改为新机构。`measured_acoustics_qa.json`验证初段形态、一次释放/延后回声及quiet取消，旧i_acoustics_qa也已回归。当前只是独立计算通路，还未与实体控制/声音/新膜片整机串联。

下一步把当前A部件响应、真实开度和声学事件在同一个独立实机查看器串起来，验证交互先后及正面可读性。继续A艺术工艺与完整表现，再B螺壳/C内芯及原选完整海螺和月光模块。全目标不缩减。
