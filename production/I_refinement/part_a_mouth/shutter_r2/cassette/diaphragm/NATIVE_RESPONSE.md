# 统一喉口响应原生预览

当前可运行包：`dist/macos-review/MagicDesk-I-Preview-1d4b2301-5fcbfb3b.app`，同名`-arm64.zip`约91MB。它是当前Mac的独立喉口预览，含三片、导向/归位机构、精修护网、膜片悬架、新灯光和统一响应逻辑；尚无音频/正式声场VFX，也没有完整海螺。旧777613d0包保留，主App不变。

`i_mouth_response_rig.gd`把实际2.6秒开合、实测开口、蓄能和膜片回弹连起来。用户松开后保持压力，真实三片到释放姿态再触发一次发出响应，之后安排较弱的回声。关闭会取消待发/待返回事件，卸压和膜片恢复后才收拢；中途重新打开不会复活旧回声。原声学引擎新增显式外部开度输入，未绑定的历史模块保留原来的逻辑。

查看器操作：点击或空格开合，按住H蓄能后松开发出响应，E完整单次演示，拖拽旋转，滚轮缩放，R复位，L开合循环。失去焦点时若正按住蓄能则取消，避免卡住按键。此查看器检查操作不是主App最终实体控制器。

## 实际发现与验证

联动测试涵盖30/60/144Hz、释放后回声、回声前取消并重新打开、释放前重新按住、卸压后关闭，保证声学开度跟实际薄片一致。报告：review/I_refinement/part_a_mouth/shutter_r2/diaphragm/rig_qa.json。

第一轮原生包220448e8的拖动仅靠event.relative，Computer Use实测拖拽被误判点击。当前5fcbfb3b改为事件位置差，并在松开时补算位移/阈值，解决误触；同时支持Mac PanGesture缩放。已在实际导出的新包里看见旋转到背面而开度保持不变，滚轮距离3.7→3.404，R恢复3.7，E完成一次发出/一次返回并归位，点击收拢。手动长按H、焦点丢失取消仍不记作已原生验收，代码级时序测试与真实输入证据分开。

构建、代码、源、GLB、PCK、ZIP哈希和原生观察：`review/I_refinement/part_a_mouth/shutter_r2/diaphragm/native/`。ZIP校验、arm64架构、签名核对通过。已保存native_closed.png与最终诊断状态。包ID为com.cedricxugun.magicdesk.ireview.response；多个历史测试包共享此ID时，Computer Use应使用当前完整app路径，避免歧义。

构建命令：`python3 tools/build_i_mouth_review_macos.py --report review/I_refinement/part_a_mouth/shutter_r2/diaphragm/build.json`。包名同时包含源与代码短哈希，不覆盖已打开版本。构建门检查源几何、组合动作、GLB形变及rig检查；签名不是艺术验收。

接续仍是A整体工艺/表现、声场与音叉的专属素材和动作顺序，然后B螺壳、C内芯、正确海螺主体与月光三乐章。没有把这次独立预览叫完整I或AAA成品。
