# R53 05下沿圆角金属托边

当前源 `blender/collection/I_nautilus_cap_trim_r53.blend`，SHA **bafc0dc8234fb234d16db0a0e946857705026a777e7a42d92016cd74c8bf1a99**；组合 `review/I_refinement/nautilus_r1/cap_trim_r53/build.json`。新增独立闭合 `I53_CapMetal_05`，直接作为05壳片的子件随动。R51全部旧几何/法线、膜片形变、导光、透明谱面与镜片保留。

由真实Z=1.702收口面提取轮廓，约束三角化生成嵌套圆角带，圆角向轮廓内部收；背面射线贴合源面。新件有实际体积和圆角轮廓，不只是改材质或贴线。当前只完成这段水平下沿，不是完整弯曲包边/金属内衬。

## 检查

- build_check.json：2956顶点、5908三角面，闭合正体积，自接触0；背面采样修正0、接口平面数值重叠0；闭合时到固定下颊的垂直间隙约.003。1232个旧网格的几何/法线/UV/形变/材质/变换保护。
- cover_sweep_check.json：九个实际盖体姿态，新托边随05参与完整组件与其余部件检查，无所查相交。
- mouth_clearance.json：七个求值A姿态及开/闭盖，托边对A检查通过。
- light_qa.json：实际12膜片缓冲与R36相同，播放响应/灯光状态保持。
- views/trim05_assembled_underside.png 是实际装配近景；trim05_isolated_underside.png 明确隐藏了其他部分，只检查新件自身，不作整机成品图。

原图仍为 mouth_finish_r21/mouth_junction_close_open_r1.png 及既有提示词，本轮无新增生图或外部图片API。工具链：Python3.12独立环境，Shapely2.1.2（约束三角化）和NumPy2.5.3；生成工具 tools/geometry/build_i_planar_trim_r52.py，原始截面与网格JSON在 cap_profile_r52。运行App只使用导出的GLB，不依赖此几何工具环境。

下一项是固定下颊的对应收口及其余弯曲边，不把这一段当完整包边。保留全部F/I/J/K/L/M/N/最后G目标，仍未AAA或原生验收，主App未更新。

## 最新演示规则

用户指出演示音乐暂停再继续。默认音乐演示已改连续播放，暂停/恢复/收回只能显式使用 --test-pause-resume。最新视频与验证见 ../continuous_demo_r54/README.md，不能继续把旧25秒功能测试当正常播放展示。
