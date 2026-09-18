# I 双半笼检修 R7（动作原型，未成品）

先读DESIGN_CONTRACT.md和内置生成的split_cage_storyboard.png。图稿/提示词/出处已入本目录，仅用内置image_gen，无外部图片API。图中某些横置储气器和底座/按钮漂移不作为尺寸依据；实际源仍保留本机模型坐标与共享底座。

## 为什么改变路线

R6尝试为后壳做内侧槽，但部分位置会削薄外壳，因此没有保留这些切削。最终R6改了脊梁截面/颈部与径向连接，源ee02667f...、组件1b098ff0...，外壳没有新增让位槽。进一步检查确认原储气器向尾部平移退出会穿过闭环骨架，继续微调停放点无法解决该约束。R6作为探查源保留，不能当作几何验收版本。

## 当前实际来源

blender/collection/I_service_r7_motion.blend SHA625a46f1de761e2bbb9e3d230ad1547695b85abf5fcaab7efb3c50856c67307c；app/assets/collection/components/I_service_r7_motion.glb SHA81c5b2958bcae2956b909ac08520654db677b33e876766b49d31809dfbc1157c。R5已完成的制造细节源849ee7ae...保留。R7切分/换父级后的连接与间隙必须重新验证，不能直接沿用R5的通过结果。

当前为30组服务动作：前盖分成12个半片操作节点，后盖随对应半笼运动；14条闭环腔肋分成28个半圆肋，纵轨、套筒和支架随其所属半笼运动。跨缝铜导体按原路径分段，实体接点尚待制作。前盖先沿导杆轴退出，再随半笼打开，避免单独漂在储气器上方挡路；骨架打开后声学匣依次退出，储气器先脱开0.065，再从中央开口升出。

左右运动枢轴沿用现有上支承位置（Blender局部坐标±0.24、0.10、1.46，Y轴），开角±0.65rad；这是运动约束定位，**不代表真实转动轴套/法兰已制造完成**。固定下支承保持。当前完整展开图runtime/340.png为Metal原型回放，不是AAA成品图。

## 证据边界

review/I_refinement/service_r7/runtime/review.json：实际Metal1000帧包括压力恢复、检修、中断/反向和回装；12个源时刻、每时刻30个服务组加12个操作半片节点的姿态对照最大误差5.96e-7，所测状态门槛无违例。56块新切分壳/肋网格检查为封闭正体积。reservoir_exit.json：在内笼已经静止打开的0.86..1区间，以201个样本检查储气器对两半笼及所带壳/支架/导体，没有发现面交叉；不覆盖其他移动声学匣、早期解锁、连续扫掠体积或还没建的铰链/接头。

**整机clearance.json仍false。** 当前初始24个组对、11个检修时刻76条时刻/组对接触记录；分组/结构改变，不能和旧版计数直接比较为品质提升。完整展开时仍有后壳与固定上支承/密封环接触。前盖半片、半圆肋、导体分缝也缺正式锁扣/法兰/接点。不得自动把这些初始相交都当作合理配合。

## 接续优先项

1. 按新分镜制作真实上铰链/轴套/出板支座，保持已有枢轴基准，补后壳围绕支承的正式开口、金属收边和运动让位；避免转动轴套被固定撑杆穿过。先解决runtime展开时后壳0/1与固定支承的实际接触。
2. 做半笼分缝法兰/锁销及收回动作，铜导体分缝真实接点、前口密封环分段与退出；关笼前必须复位，不能只有几何半片无锁定结构。
3. 修储气器鞍座与导针/后端盖/橡胶壁的固定配合和释放路径，以及膜片到前端轮毂的真实连接；补全实际连续扫掠、取消与反向测试。
4. 继续主I模块、真实控件/声音/状态解释、完整材料/光照和独立Mac原生检查，再按队列J/K/L/M/N、G其余推进。主I和日常App仍未替换。

## 运行入口

新源使用i_runtime_rig_r7.json（12个前盖操作节点）及i_service_rig_r7.json（30组，包含旋转）。i_runtime.setup第三参数/body_rig、第二参数/service_rig可选，默认旧版保持；i_service.apply支持四元数旋转与旧平移路径。inspector现在按最近的服务祖先分配网格，避免嵌套半笼/壳片重复计入。

Godot回放使用i_service_runtime_review.gd，传--component=res://assets/collection/components/I_service_r7_motion.glb、--reference-dir=res://../review/I_refinement/service_r7/、--service-rig=res://assets/collection/i_service_rig_r7.json、--body-rig=res://assets/collection/i_runtime_rig_r7.json和对应--out目录。源检查inspect_i_service_r4.py接受-- --review-dir=review/I_refinement/service_r7。不要用默认R4/R2绑定检查R7后误报缺节点，也不要重建早期R1覆盖当前源。

公共运行时新增旋转/可选绑定后的R5回归见review/I_refinement/service_r7/r5_regression/review.json；旧默认路径仍通过同一服务状态/源姿态回放。
