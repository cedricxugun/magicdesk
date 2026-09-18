# F 分件表面处理

当前启用app/assets/collection/f_finish.json，只作用于F_complete元数据指向的上部；B/公共底座和其他装置不套用。黑色摩擦片采用无清漆的粗糙非金属，齿轮/转子凹槽保留发黑钢质，壳体黑漆与红漆分开处理，镍铬/钢/铜保留各自反射，瓷壳使用瓷釉层。没有重绘贴图或改变UV。

Godot将清漆作为基础材质上方的一层较小高光，适用于漆面；各向异性影响沿切线方向的高光形状。参数不是品质证明，取舍以本机A/B为准。[Godot官方材质文档](https://docs.godotengine.org/en/stable/tutorials/3d/standard_material_3d.html#clearcoat)

对照在review/F_complete/revision_20260911/finish/：A_original与B_finish使用相同镜头/姿态/照明；C_chrome_no_normal仅诊断，未采用。去掉镍铬法线后滴锤大片明暗仍在，不能称为法线问题已修复。源source_gear.png也保留类似反射，源/实时灯光与透明后处理仍非像素一致。

sync_f_finish.py为576个候选源材质槽建立8类分件材质；对象级材质链接避免改共享网格材质，完整几何/姿态/动画曲线指纹未变。候选SHA c68b3712...，原b9118b3e...已备份，原F_complete.blend未动。运行GLB保持89353552...；元数据仅新增finish_profile，旧take元数据哈希依然指向旧版本，不要手改哈希或无理由重烘焙。未来需要重新bake时必须先重新采集take；当前源材质补丁由source_sync.json独立证明。

本机日常包3f5387ca...已包含分件材质，实际PCK验证摩擦/漆/钢材质不互相共享、控制器与刻字正常。基本原生输入代码与已验证9c09d6ce包逐文件相同；不将旧原生照片改绑到新包。

近景发现差动齿圈为早期倒角方块齿，下一步按GEAR_INTAKE.md修正齿形/啮合，再继续其余精度与I/J/K/L/M/N。当前仍不是AAA完成。
