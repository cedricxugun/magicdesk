> 当前接续（2026-09-13）：三片、卷轴承座、前导轮与归位槽的独立候选已推进至 `cassette/front_guides/README.md`（从 cassette 目录读取时为 `front_guides/README.md`）。本页下方是对应旧源的历史状态；主 App/完整 A 尚未完成。

# A 首片卷收舌片：真实动态候选，仍未完成 A

**最新：先看 RASTER_FIX.md。** 用户指出的破面感已用实际着色 A/B 定位到自动 LOD，运行时固定完整拓扑；中心改轴向孔座/触须。新视频及源/渲染器哈希在 review/I_refinement/part_a_mouth/shutter_r2/tongue_probe/feedback_take.json，旧 tongue_roll_cycle.mp4 保留为反馈前记录，不再覆盖。

当前只驱动第 0 片及其背层，另外两片保留 R2 闭合形态。先做这一个卡匣的实际空间、回收和连接；不能将单片成功当成三片/整机完成。原始斜叠外观与共享底座约束保持，主 App I 未替换。

## 当前源与实际预览

- 源：blender/collection/I_tongue_probe.blend；生成入口 build_i_tongue_probe.py，路径定义 i_tongue_path.py。每次重建有源哈希校验和检查点备份。
- 运行组件：app/assets/collection/components/I_tongue_probe.glb；运动纹理在 app/assets/collection/art/I/tongue_probe/。
- 准确源/组件/纹理哈希：review/I_refinement/part_a_mouth/shutter_r2/tongue_probe/build.json。
- 实际 Metal 视频：同 review 目录下 tongue_roll_cycle.mp4，6 秒、1200×1000、30 FPS、无声；来源和视频哈希见 take.json。
- feed_00/16/32/48/64 与 returned_rest 是正常部件视图；stored_cassette_diagnostic 隐藏口沿/内套，仅供看内部，不是整机 OPEN。

## 已做

薄片带永久保留导带，经过转向/压平导向、向内避让的后通道进入卷筒。导带夹在卷筒上，卷筒转动并随卷径在小范围内平移；导带/前后层始终保留，不用缩放、透明或隐藏完成收纳。前后薄层有真实厚度与卷层间距。

内部承载环已开实际通道，后导向向内弯以避开瓷壳，未扩大外口沿。平夹片曾在关键姿态中点擦到下一层卷材，改为贴合卷径的弧形保持片后重查。Blender 自定义进度首版被整数化，已明确保存 float 并用时间曲线期望值核验。

源中保留 257 个密集姿态；运行时用从源烘焙的逐行位置/方向/截面数据重建现有网格，GLB 不再装入全部变形目标。图像是数值资产：禁止 sRGB 转换、有损压缩、透明边修复或自动 3D 压缩。Godot 绑定时逐纹理核对完整 RGBA32F 字节哈希，并以 UV2 数据重建全部 REST 顶点作校验。不是以程序图元替代正式视觉设计。

## 当前检查及其边界

- geometry_check.json：46 个源动画前进/保持/回程时刻，网格封闭/正体积，薄片对全部场景表面、前后层相互、非相邻自表面未测到交叉；进度值与预期相符。
- interpolation_check.json：另外检查全部 256 个姿态区间中点，使用运行时卷筒/滑座插值；当前同样未测到上述接触。
- field_contract.json：序列化运动数据与求值后的 Blender 顶点核对，最大顶点误差约 1.86e-7 场景单位；滑座/卷筒插值误差在当前阈值内。不是原图还原率。
- runtime/review.json：实际 Metal、导入后的数据哈希和模型状态；take.json 对应真实捕获视频。

这些仍不是严格连续碰撞证明、材料弹性/应力验证、全部固定零件配合、原生输入或美术验收。当前图稿只作为视觉/机构方向；生成图的卷筒大小并非可测 CAD 数字。

## 下一步

先把相同路径/数据制作流程扩展到其余两片，按原来的斜叠关系安排错峰卷收和逆序复位，检查三片与三卡匣之间的全部动态空间。随后补齐真实轴承机匣、滑座导轨、电机/传动、末端归位承座与细节材质，不能把目前裸露卷筒和简单法兰称为 AAA 完成。

继续 A 的完整开合、取消/反向、膜片/弹簧响应与同角度美术对照。A 对齐后再做 B 螺壳、C 连续内芯与正确整机，之后接回月光三乐章和真实谱面；无需逐阶段用户审批。

失败记录保留：first_pass、morph_backend、flat_retainer。不要用旧通过/失败报告覆盖不同源版本的结果。
