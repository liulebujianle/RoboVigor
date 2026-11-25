# RViz 仅显示轮组中心的历史计划（2026-10-30）

该计划未完成勾选，随后改为四轮独立旋转 TF，见 2026-10-30-per-wheel-tf.md。以下保留当时的问题和拟执行顺序。

当时公共 TF 已经过滤，但 RViz 为显示 RobotModel 动画仍订阅内部完整总线。新增或启用 TF 显示时，仍会暴露 116 个内部主轮/滚子坐标系。

计划让所有标准 RViz TF 显示（包括新建的 All Enabled 显示）只看到轮组的 wheels_link，同时保留物理关节和实际车轮动画。

## 当时计划

- [ ] 添加精简显示描述，去掉内部主轮/滚子链接，保留底盘、云台和部件参考链接；完整物理 URDF 不变。
- [ ] 将 116 个实际主轮/滚子网格用 MarkerArray 渲染，位置来自实测内部完整 TF，仅锚定到 wheels_link。检查 visual origin 的旋转、平移和网格缩放。
- [ ] RViz 恢复使用公共 /tf、/tf_static 和精简描述，添加 Wheel Visuals MarkerArray 显示。新 TF 显示不能访问内部轮系；完整内部 TF 继续用于诊断和 Marker 位姿查询。
- [ ] 构建安装，执行回归和运行检查，确认可视数量仍为两个 RobotModel 网格加 116 个 Marker、轮子位姿旋转、公共 TF 精简且无缺失变换；完成后重启当时管理的 launch 和配置。
