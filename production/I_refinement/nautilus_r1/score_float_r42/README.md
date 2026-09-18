# R42 用户明确要求无黑底的悬浮五线谱

用户指出黑底没有悬浮感、科幻感。此前为可读性加的暗色底板撤销，不再采用R40 .88背景方案。

当前配置：`app/assets/collection/art/I/light_score_r40/score_refined/layout_float_r3.json`，optical_backing=0，score_gain=1.7。当前实际组合：`review/I_refinement/nautilus_r1/score_float_r42/build.json`。真实刻谱、居中1.20×.72几何、光线连接、月光资源和R40导光保留，空白区域完全透明；抗锯齿笔画采用修正后的直通透明度混合，白色未读谱、金色已读谱和窄金色扫描保持。

运行时默认背景也改为0，默认采用正确透明混合。历史显式背景配置只用于保留旧证据，不能再次作为当前视觉入口。

已看同一实际相机的整机与近景：`review/I_refinement/nautilus_r1/score_float_r42/views/relation_chambers_quiet_music.png` 和 `score_readability_close.png`。后方实体孔板与三根触须现在透过谱面空隙直接可见，没有矩形底板。本轮未重新录制视频，R40旧视频仍有黑底，不作为当前谱面演示。主App未更新，整体工艺/全曲与原生等仍未完成。

R41端头镜片为独立试作，见 ../scan_caps_r41/README.md。不能因有源文件把它称为已接到当前预览。
