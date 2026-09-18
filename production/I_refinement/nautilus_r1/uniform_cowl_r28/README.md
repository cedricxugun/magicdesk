# 口部过渡壳重建与均匀网格候选

当前候选源 `blender/collection/I_nautilus_uniform_cowl_r28.blend`，源SHA256 `dbf35b3da400c04eef239c2a6374518bc368120fb44de0887a7fe1dd7681f823`。组件和最新检查以 `review/I_refinement/nautilus_r1/uniform_cowl_r28/build.json` 及同目录报告为准。构建入口：

```
/Applications/Blender.app/Contents/MacOS/Blender --background --python-exit-code 1 --python blender/collection/build_i_clean_cowl_r23.py -- --config=production/I_refinement/nautilus_r1/uniform_cowl_r28/config.json
```

## 当前完成的结构工作

- R22 `I_nautilus_cowl_rims_r22.blend / 6cae3960`：03/04两片上盖的完整闭合金属端面及实际圆角，随原盖体一起运动。03仍有两处原孔区的旧三角接触，数量与原源一致，不能当整片或AAA验收。
- R23/24重建01/06固定过渡壳，使用真实主体截面、对应的内外弧、明确的口沿封面和共用曲线控制；A、原C1法兰/支柱、内腔承座及所有机构保留。
- R25 `7412e113`处理01的局部精度接缝，最大位移1.1920929e-7场景单位；01/06原始BVH自接触检查为0。
- R26 `83d792f9`重建05活动壳及固定下颊，二者从同一完整新曲面切分，世界Z为1.70±0.002。7个A源姿态和9个盖体姿态所查相交项通过，仍有05的少量精度接触。
- R27 `c67ef38f`继续处理05的5个精度接缝点，最大位移7.4505806e-8；原始自接触尚有2组，独立判别未把它们冒充解决。

这些都是有限结构证据，不等于最终曲面、材质、完整动作或原生App验收。

## 为什么还有新的候选

R21原过渡区存在折回/重叠面；笛卡尔和径向平顺候选分别造成口内穿插或局部过薄，因此 `cowl_fairing_r22` 下4a4f5fa5/7485121e没有作为美术接续。单改自动法线没有消除外观问题。

重新连接以后，实际Godot画面仍有条纹。已用同一源和相机对照完整导入数组、去掉LOD/阴影代理、关闭属性压缩及关闭主光源阴影，均未消除条纹。诊断在 `review/I_refinement/nautilus_r1/clean_cowl_r26/import_comparison/`、`raster_full/` 和 `raster_full_lights_no_shadow/`。无阴影画面仅是诊断，没有作为正式光照。

R28把05及下颊的过渡改为128段周向、48排纵向的均匀采样，前沿为正确的环带封面，最后一排逐边接回原始主体截面。避免把每个极密的截面点都拉成长条三角面。均匀版仍须看实际画面和新检查，不能仅凭生成成功宣称条纹或整体形体已解决。

## 制作与检查注意

`mathutils.Vector` 的相等比较不能作为逐分量严格相同的证明；本轮已改用元组/数组严格比较。两次不安全合并试验被保护断言阻止，没有写回源。接缝修复只针对已有相邻边，并保留最大位移和单精度ULP见证，不做跨薄壁的全局焊接。

原始BVH接触、严格分离/边界判别和视觉观察分开记录。Blender的BVH回调使用三角判定及浮点坐标；不应把数值边界与真实穿插混为一谈，也不能随意把未知项白名单化。[Blender实现](https://raw.githubusercontent.com/blender/blender/main/source/blender/python/mathutils/mathutils_bvhtree.cc)

本轮沿用已有内置生成的 [口部局部图](../mouth_finish_r21/mouth_junction_close_open_r1.png) 和 [提示词](../mouth_finish_r21/PROMPT.txt)，没有调用外部图片API。原目标仍是 `nautilus_states_centered_r2.png`，底座、A安装轴线、原夹持/承力和完整月光资源保持。

下一项先完成过渡面显示及05完整边缘，再继续材料/光影、中央谱面新斜角、完整月光联动、旋转动力/供能和原生集成。主App未更新，Git未推送，尚未锁形或达到AAA。全队列active：I后J/K/L/M/N，G其余最后，B保留。
