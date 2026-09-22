# R78 · 先纠正机身与底座，不继续放大检修原型

用户2026-09-21指出模型与底座连接有问题，最新生成图也不对。本项优先于R77后续拆壳。R76局部螺纹/动画的技术结果保留，但不作为整个机构合理或美术完成的证据。

## 已确认

恢复普通装配姿态后，当前连接仍是R1造型阶段的圆台与四个贴合承托块。源码注释明确是shape-study interface。新实际审阅installed/与只读installed_audit.json确认：三个承托块贴02瓷壳，另一个贴03后壳；上表面采样间隙约.00015–.00020场景单位，没有发现这四处表面穿插。**表面贴合不是连接机构完整**：目前没有把四处接点做成机身内部金属骨架到基座的明确锁固路径。前方两根R18支杆连接口部夹环，不能冒充全部机身固定。

R76分镜还将已整体抬升.45、支撑件退开的检修准备姿态标作READY FOR OPERATION/SEALED，这是错误表达；图中假螺钉/旋转箭头也不正确。该图降为拒绝的历史稿，不能继续作为整机连接或正常运行姿态的美术目标。

## 修正方向

保留共享BASE_FIXED外径、层数、按钮及机身整体安装位置。仅重做其上I专用适配器与机身下方真实接口：基座固定法兰→定位/锁固座→短而宽的承力座→内部金属骨架。外瓷壳是可拆覆盖件，不把可拆02/03当唯一承力件。正常装配时接缝与锁固可读；检修先解除锁固，有独立承托/明确的爆炸展示状态之后才能整体抬升，不能漂浮还标正常运行。

先做对应安装关系的局部设计图；图只是设计提案，不取代真实三维尺寸和扫掠检查。新的结构需要验证接点、壁厚、锁固访问、活动罩包络和拆壳顺序，不能把生成图重新当几何真值。未经这些检查不覆盖R76或主AppR68。

## 当前可复查

- `review/I_refinement/nautilus_r1/coupling_repair_r76/installed/01_installed_closed.png`
- `review/I_refinement/nautilus_r1/coupling_repair_r76/installed/03_support_front.png`
- `review/I_refinement/nautilus_r1/coupling_repair_r76/installed/04_support_rear.png`
- `review/I_refinement/nautilus_r1/base_connection_r78/installed_audit.json`

这些是现有源的诊断图，不是修好的模型。新候选需要另存，尚未发布。
