# I R11：独立形体候选，尚未定型

用户已明确否定R9宿主。当前从原选海螺重建饱满壳体和侧前方口部，没有加载旧锥管主体。辅助图closed_form_reference.png由内置生图生成，prompt.txt和art_provenance.json保留；其SIDE不是严格正交图，不可据图上的任意形体漂移修改真实底座。

当前源：blender/collection/I_conch_r11.blend

SHA256：2af199dc2ad0efbd0854875c59af72fbbf0373301d49c04e5087d304bfa14999

组件SHA256：a156a337315e293ab38ae0a7d0e78cf56d1ab240ddad4126255b466f2857da86。

首轮渲染仍有尖锥顶部、层体不鼓、口部未接合等问题。已作第二轮形体修正：更圆润的半幂体量、分层鼓起、锥形孔和深口沿过渡、中央轮毂让位。仍不能称为已还原原图；主App未替换，也未重新接音乐。

按用户要求采用制作流程V2：先读 production/workflow_v2/DESIGN_TO_MODEL.md。shape_contract.json 明确是 unlocked_candidate_not_art_accepted。通用测量脚本已按求值后的真实顶点产生 measured_shape.json；固定相机1024×1024的正/侧/背/顶中性图和独立剪影在 review/I_refinement/conch_r11/fixed_views/。图中数值是候选实测值，不是原图给出的目标，不意味着形体正确。

当前实测D=2.740000，闭合总高=1.2883D，口沿外径=0.6555D。必须继续对照原选图的体量、轮廓、曲率、口部关系；目标轮廓未锁定，因此没有“还原度分数”。

重做阶段有六块壳、弧形快门和简单支承，但壳体展开、全部连接/厚度/碰撞、快门驱动槽和源/实时全动作未验收。不要根据局部数学封闭/尺寸上限通过去继续堆零件或宣布完成。下一项用固定视图修正形体，再锁正确的几何基准，然后制作分件/机构/表面。

音乐、真实谱面与完整播放检查保留在 moonlight/，无需重做音源；主体正确后接回。全队列仍I→J/K/L/M/N→G其余，B保留。
