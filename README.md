# MagicDesk · HELIOS 孵日器

以复古科幻机械为方向制作的可交互三维桌面摆件。上部机械旋转展示，底座固定；支持六瓣同步绽放、核心过载、70组零件拆解与重组，以及收拢熄灯后退出。

![实际 EXE 过载画面](review/native_overload.png)

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

[42秒实机演示](review/R3_desktop_demo.mp4) · [详细使用说明](使用说明.md)

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

RTX 3060 的已打包版本实测平均约50.6 FPS，2146帧无空白画面，透明点击与关闭通过；并非稳定60 FPS承诺。R3粒子使用跨两侧花瓣的宽椭圆长尾迹，强放电连接核心、机械触点与高压端子，蒸汽接收核心颜色并按开合状态播放。

第三方环境光来自 Poly Haven（CC0）；Godot 等第三方许可见 [THIRD_PARTY_NOTICES.txt](dist/THIRD_PARTY_NOTICES.txt) 和 [资源来源](app/assets/THIRD_PARTY.txt)。
