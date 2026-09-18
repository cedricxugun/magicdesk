# R38 主体材料候选

源仍为 R36：`I_nautilus_chamber_motion_r36.blend` / e2a425d9，组件 ec22caae。没有重建几何、改变口部关系、移动机构或调整共同底座。

`app/collection/i_finish_r38.gd` 根据 `app/assets/collection/art/I/finish_r38/profile.json` 为当前主体实例复制材料：奶白瓷壳增加清漆层、镍件降低暖色染色、青铜更克制、膜片更深且更哑光。既有内置生图派生的拉丝粗糙度接入腔室导光 shader；来源见 asset_provenance.json。没有新外部生图，没有覆盖共享源材质。

`review/I_refinement/nautilus_r1/finish_r38/qa.json` 检查实际材料组数量、十二组拉丝转接、停止/释放后材料保持、共享实例和网格/变换不改。静态同机位对照在 baseline/views 与 views。`take_r1/material_music_r1.mp4` 实际 750 帧 / 25 秒，validation.json 检查通过局部音频、动作步、暂停和最终闭合帧。

随后用户指出开壳后内部光带偏暗且部分未亮。继续入口为 ../chamber_light_r39/README.md；R38 原视频保留为修改前的材料证据，不作为最新导光表现。主体曲面折痕、收边、工艺仍未完成，不能把材料覆盖或局部检查称为 AAA。无新 App。
