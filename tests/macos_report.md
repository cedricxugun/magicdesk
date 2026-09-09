# HELIOS 1.3.3 — 当前 Mac 本机版本

2026-09-09，Apple M5 / macOS 26.6，Godot 4.7.1 / Metal 4.0 / Forward+。

## 交付

- `dist/macos/HELIOS.app`：原生 arm64，约 311 MiB，运行无需 Godot 或 Blender。
- `dist/HELIOS-macOS-arm64.zip`：相同 App 的压缩备份，约 178 MiB。
- 本地 ad-hoc 签名通过 `codesign --verify --deep --strict`；仅为当前电脑制作，未进行 Developer ID 签名或公证。
- 精确 PCK、可执行文件和 ZIP 的 SHA-256 见 `macos/artifact.json`。

## Mac 适配

Godot 直接通过 Cocoa 透明窗口显示 Metal 画面，不使用 Windows 的 C# 接收程序。窗口保留固定 1920×1400 透明画布，为轨道粒子与蒸汽预留范围；空白处沿用真实模型表面射线检测穿透鼠标。避免动作时重复设置 Cocoa 窗口坐标，解决 Retina 下 1 像素取整偏移。加入中文系统字体，Cmd-Q、系统关闭请求和第七个按钮统一执行收拢熄灯退出。

导入 ASTC 纹理以支持 Apple Silicon 导出；构建从官方通用模板生成后移除 Intel 架构，再签名并打包。Windows EXE 的 SHA-256 与原仓库一致。

## 验证及边界

1. **最终 App 自检：23/23 通过，退出码 0。** 从 App 内实际 arm64 可执行文件传入 `-- --self-test --capture=<目录>`，检查部件、按钮、重组归位、同步开瓣、相机、固定底座、坐标与透明窗口。结果：`macos/selftest/verification.json`。
2. **最终 PCK 动作检查：96/96 通过。** 使用匹配的 Godot 4.7.1 编辑器可执行文件加载 App 内实际 PCK，并运行 `macos_runtime_qa.gd`；覆盖 61 帧喷发缓存与 18 帧待机缓存、GPU 特效预热、六种状态透明截图、开合/过载/拆解/组装、中途打断、休眠/唤醒、旋转/暂停及关闭演出。结果：`macos/final_pck/runtime_report.json`。这是最终资源包验证，不能将执行驱动器描述为 release 模板本身：release 模板没有 `--script` 参数。
3. **本机实际交互：** 正常启动最终 App，用鼠标点击实体开花按钮及组装按钮，并以快捷键触发过载；模型和特效实际可见，组装后程序继续运行。Cmd-Q 单独通过系统输入验证。

动作检查含截图读回，平均 33.54 FPS，中位帧间隔 29.15 ms、P95 39.78 ms、最大 149.64 ms。该数字属于测试过程，不承诺锁定 60 FPS；未做长时间续航、功耗或其他电脑兼容性验证。

重建命令：`bash tools/build_macos.sh`。Mac 操作说明见 `../使用说明-macOS.md`。

技术依据：[Godot Mac 导出说明](https://docs.godotengine.org/en/stable/tutorials/export/exporting_for_macos.html)、[SceneTree 系统退出处理](https://docs.godotengine.org/en/stable/classes/class_scenetree.html#class-scenetree-property-auto-accept-quit)。
