# G1 瓷片分区封合

2026-09-10。当前实际候选已把贯穿整翼的直切改为分区封合，主G注册表和Mac包仍未更新。

[约10秒实际候选回放](../../../review/G_optical_curator/butterfly_r2/runtime/panel_seal_review.mp4)展示构建、展开、振翅、收翼及退去。固定30FPS、1040×940近景录制，不是原生输入或实际运行帧率测试；原片完整归槽另有候选检查记录。

## 本轮制作

`bake_butterfly_seal.py` 读取已经保存的蝶源，在翼片平面上烘焙到真实翼脉、包边和嵌片座投影的距离场，并扣除实际金属半径。它生成两张512×512的数值贴图，不修改模型几何或原有动作，也没有重新调用图片API。

- `app/assets/collection/art/G_AI/butterfly_upper_seal.png`
- `app/assets/collection/art/G_AI/butterfly_lower_seal.png`
- 参数、边界、出处与哈希：`app/assets/collection/butterfly_seal.json`

先显现金属框架，再让瓷釉从每个分区边缘向内封合，红色嵌片最后出现。后翼略晚于前翼；回收相反。G1的退去过程放慢到1.9秒，其他藏品保持原时长。没有引入随机噪声或抖动粒子遮盖边界。

初版从翼脉中心线计算，刚开始封合时侧缘会细碎闪出；改为从金属的投影宽度起算后，零距离区域连续，去掉了这轮近景里观察到的条纹。

沿用前一轮内置生成的[有效分镜](fabrication_storyboard.png)与[提示词](fx_prompt.txt)，本轮补的是由真实模型烘焙的数据资产和运行合成。

## 检查与范围

- `butterfly_seal_field_qa.gd` 校验884个导入贴图的翼脉采样，位置、V方向与数值采样对应，最大边界值0。
- 最新 `candidate_qa.json` 十项通过，含完全成形后展开、连杆双端连接、球杯朝向、先收翼再回收、部分成形取消和原片归槽。退出日志没有资源泄漏告警。
- 原G0七项输入回归通过；本次未改其参数范围或演出时长。
- 视频从本次实际候选录制中按帧裁出，不是概念动画；录制范围及原始帧号在 `video_review.json`。
- 最新实际图包含 `build_55.png`、`build_70.png`、`build_85.png`、`return.png`。旧直切图以 `_before_panel_seal.png` 保留，不混作当前结果。

这些结果不是AAA或全款验收。仍需核对候选与Blender的材质/光影、正常桌面尺寸的可读演出，完成整段运行时/特效源同步和Mac原生验证。后续已同步3859帧机械/表情/控件和封合源，见 `MATERIAL_SOURCE.md`；GPU光丝/微粒等实时层不包含在源烘焙范围内。

最新接续已到独立Mac候选检查，按 `MATERIAL_SOURCE.md` 与队列继续。
