# MagicDesk · 桌面机械装置

**跨设备继续开发先读 [HANDOFF.md](HANDOFF.md)。Windows 0.2.2 交互评估版现已包含九款集合、新控制器和 F 首轮机构精修；M/N 已通过导出 EXE 的入口回放。八款最终美术仍未完成，Mac 尚未重新导出本次版本。**

[运行 Windows 交互评估版](dist/MagicDesk.exe) · [设计图 / 实机对照](production/interaction_refinement/index.html) · [原速实机演示](review/interaction_native/release/review_walkthrough.mp4) · [本轮制作状态](production/interaction_refinement/README.md)

点击底座左前白色舱罩展开实体铭牌，滚轮翻阅并点击选择。新控制器支持按住、拖动、旋转、档位与摇杆；悬停查看对应手势。右侧双向拨杆左推拆解、右推组装，最右 X 收拢退出。原 `dist/HELIOS.exe` 保持原版，以下保留其说明。

本机 Mac 开发构建 0.2.0 已接入 B 孵日器与 F/G/I/J/K/L/M/N 八款装置，共用固定底座、机械铭牌机关与透明桌面窗口。动作分镜、实际贴图资产、Blender 源文件和验证记录见 [首批制作记录](production/batch1/WORKLOG.md)。以下 HELIOS 说明也保留为原有 Windows 版本基准。

以复古科幻机械为方向制作的可交互三维桌面摆件。上部机械旋转展示，底座固定；支持六瓣同步绽放、核心过载、70组零件拆解与重组，以及收拢熄灯后退出。

![实际 EXE 过载画面](review/final_star_peak.png)

[查看 A / B / C / D 四款装置设计图与制作状态](concepts/README.md) · [查看特效设计图库](review/vfx_variants/README.md)

## 运行

先安装 Git LFS，再克隆并取回大文件：

```powershell
git lfs install
git clone https://github.com/cedricxugun/magicdesk.git
cd magicdesk
git lfs pull
.\dist\HELIOS.exe
```

Windows x64；运行已打包 EXE 无需安装 Godot 或 Blender。模型、贴图、三维蒸汽缓存、EXE 和演示视频使用 Git LFS 保存，GitHub 的普通源码 ZIP 可能只含 LFS 指针。

| 快捷键 / 从左至右按钮 | 功能 |
| --- | --- |
| 1 | 唤醒 / 休眠 |
| 2 | 绽放 / 闭合 |
| 3 | 核心过载与放电 |
| 4 | 分解组件 |
| 5 | 重新组装 |
| 6 / 空格 | 上部旋转 / 暂停 |
| 7 | 收拢、熄灯并关闭 |

拖动底座移动摆件，拖动上部手动旋转。使用 Windows 原生逐像素透明显示，透明区域可点透；开合时镜头不缩放。重复启动会唤起已有应用。

[最新版完整演示](review/final_choreography_demo.mp4) · [蒸汽修复演示](review/steam_fix_demo.mp4) · [详细使用说明](使用说明.md)

### 当前电脑的 Mac 版本

2026-09-09 本机 Apple M5 原生 arm64 开发构建：双击 `dist/macos/MagicDesk.app`，无需安装运行依赖。点击环沿压条或按 Tab 展开机械铭牌，滚轮或索引滚轴翻阅，点选装置；不同上部配各自操作匣。Mac 使用 Godot / Metal 直接呈现透明窗口；Cmd-Q 先收束再关闭。构建命令为 `bash tools/build_macos.sh`，输出 App 和 `dist/MagicDesk-macOS-arm64.zip`。旧 `HELIOS.app` 和 ZIP 保留。

此版本面向当前电脑，使用本地 ad-hoc 签名。见 [Mac 使用说明](使用说明-macOS.md) 和 [本机验证记录](tests/macos_report.md)。

## 项目结构

- `concepts/`：四款桌面机械装置的原始设定图、方案说明、动画规划与完整提示词，供选择下一款制作。
- `app/`：Godot 项目、实时材质、动画状态逻辑、蒸汽与红色电气特效，以及完整运行资源。
- `blender/Helios_Incubator.blend`：可编辑模型、材质、分件层级和600帧演示动画；同目录保留建模、校验与流体烘焙脚本。
- `native/`：Windows 原生透明窗口、输入桥接、单实例控制和单文件打包源码。
- `tools/`：构建、贴图、音效、流体数据转换工具。
- `dist/`：可直接运行的单文件 EXE、说明和第三方许可。
- `review/`：最新实际画面、演示视频和设计参考；参考图不代表程序的实际渲染输出。
- `tests/`：机构穿插、蒸汽时序、透明点击、单实例和帧率的验证记录。

已提交生产使用的 Mantaflow 三维密度缓存，包括高压喷发与待机逸散；省略可重新生成的原始 VDB、转换中间文件、Godot 导入缓存和历史失败版本。运行与导出无需重新模拟蒸汽。

## 从源码构建

验证环境：Godot 4.7.1（安装同版本 Windows 导出模板）、Windows x64、.NET Framework 4.x x64 编译器。编辑模型使用 Blender 5.2.1；运行与导出不需要 Blender。部分建模辅助脚本需要 NumPy / Pillow。

```powershell
.\tools\build_release.ps1 -GodotPath 'C:\Tools\Godot\Godot_v4.7.1-stable_win64_console.exe'
```

也可设置环境变量 `GODOT_EXE`，或将名为 `godot` 的可执行文件加入 PATH。输出为 `dist/HELIOS.exe`。可直接在 Godot 中打开 `app/project.godot` 编辑；原生透明桌面效果应通过打包 EXE 验证。

历史验证记录可能含原制作机器的路径；不影响生产运行。Blender 主文件是当前模型的编辑源，建模辅助脚本保留制作过程，运行整个早期建模流程可能覆盖后续人工调整。

## 当前验证结果

1.3.3 将开花收尾合为连续行程，去掉84%开度的停顿；星群在过载高潮共同加速、拉长尾迹并外扩，高潮期间不再随机消失。高位陶瓷阀与长管移到两瓣之间，11个开合位置避让检查通过，待机蒸汽同步到新出口。见 [最新动作与高阀修复记录](tests/final_choreography_report.md)。

1.3.2 将过载光效与7秒机械过程对齐，3–4秒为高潮；修正低位陶瓷端子的位置和形状，中心转环与核心改为先对齐再分层抽出。按钮按真实帽面命中，组装与关闭的提示分开；全开、中途展开、中途拆解、过载四种状态下组装后继续运行均已验证。见 [机构与交互修复记录](tests/mechanism_fix_report.md)。

1.3.1 修复了物理蒸汽错误使用花瓣变速曲线、在开启约0.85秒时近乎停住的问题。物理蒸汽和待机逸散现在按真实时间连续播放。透明轮廓裁剪从 Godot 主线程转移至原生接收线程，并复用图像缓冲，避免每帧扫描浮点颜色和频繁回收大数组。

RTX 3060 连续三次开合实测平均59.86 FPS，中位帧间隔16.66ms、P95 18.26ms；三次打开期间大对象回收次数均未增加。完整测试仍有少数单帧波动，最大32.13ms，不承诺所有设备始终锁定60 FPS。数据见 [修复说明与证据](tests/steam_fix_report.md)。R3宽轨道粒子、机械端子放电、现有模型清晰度和蒸汽密度保持不变。

第三方环境光来自 Poly Haven（CC0）；Godot 等第三方许可见 [THIRD_PARTY_NOTICES.txt](dist/THIRD_PARTY_NOTICES.txt) 和 [资源来源](app/assets/THIRD_PARTY.txt)。
