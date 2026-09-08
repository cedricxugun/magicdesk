# 当前交付：HELIOS 1.3 / P1 + P2 + R3

更新于 2026-09-08。

已完成：70组独立部件，7个物理按钮，完整开合/过载/拆解/组装/关闭；液压机构101档和动画中段无穿壳；面光源与金属/珐琅材质校准；底座拉丝、边缘磨损与接缝油痕；原生Windows逐像素透明显示，模型空隙可以点透；固定镜头与固定桌面像素位置；单EXE打包。

最新单EXE：dist/HELIOS.exe，2026-09-08 20:43 导出，352,092,160字节。此次打包包含下述最新实时材质、物理蒸汽缓存、闪电美术与R3粒子轨迹。

用户选择P1整圈高压蒸汽＋P2赤红核心，并以R_赤色日冕.png的R3宽椭圆飞行轨迹为本轮参考。Mantaflow三维密度缓存已接入：开蛋环形高压蒸汽、碰地铺开卷起、独立待机逸散和旋转历史尾迹；蒸汽接受当前核心红光。状态门控与首次GPU预热验证通过，过载/启动/关闭不会凭空重放地面喷气。

R3飞行亮粒：12粒上限，半长轴2.20–2.48m，白红柔芯和红色光晕，1.12秒长尾迹。强揭露/过载使用9通道分叉放电，包括核心下方金属接点到3个真实高压端子的长电弧；稳态单路间歇放电。外壳12处原有红色标志条、内侧导光槽、核心支柱和底座灯随状态响应。

原生显示验证（tests/R3_release_native/）：2146帧无空白帧，无UpdateLayeredWindow错误，窗口句柄不变；透明/实体鼠标检测全部通过，开合与拆解时底座按钮漂移0像素，第7按钮退出完成约3.77秒。重复双击测试只保留1个应用实例、1个隐藏渲染工作进程。原生DIB backing启动时一次预分配，动作期间分配次数恒定，实际窗口继续只显示alpha裁剪范围。

RTX3060实测平均50.58 FPS，帧间隔中位19.24ms、P95 23.45ms、最大43.72ms；未声称稳定60 FPS或零延迟。真实EXE截图为tests/R3_release_native/native_open.png及native_overload.png，完整实机录制为review/R3_desktop_demo.mp4。设定图仅供方向对照，不作为实现验证。

陶瓷已更新为无纤维的4K光滑釉面贴图，并同步主Blend/GLB。金属的全局油污和过重AO已减弱，保留局部接缝、拉丝和边缘磨损。六片开合节奏已统一，同步到Blender与Godot；tests/synchronized_petals.json与更新的animation_sweep.json已通过，无穿插。

最终源码：blender/Helios_Incubator.blend，app/，native/。build脚本为tools/build_release.ps1，输出dist/HELIOS.exe（内置渲染EXE，首次运行解包到LocalAppData/HeliosIncubator/runtime）。
