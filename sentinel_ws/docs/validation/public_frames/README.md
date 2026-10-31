> 历史实现，已被用户最终要求的四轮独立TF替代；当前以 docs/frames_and_time.md 为准。

> 本目录是上一版记录。2026-10-30 已修正 RViz 仍订阅完整TF的遗漏；当前方案见 ../rviz_wheel_center/README.md。

# 精简轮组 TF 与 CAD 部件参考验收 · 2026-10-29

实现与配置归属 sentry_description；完整语义见 docs/frames_and_time.md。
公开只有 wheels_link，不公开 wheel_N_link / roller_N_link；物理关节和视觉网格没有合并。
保留 chassis_link，并新增两颗 radar、相机/光学、枪管/出口的 CAD 名义固定参考。

## 检查

- Python 工具、模型、TF 路由、部件及控制检查共31 passed。
- 全部五个实际 ROS 包 colcon test 通过；description 内部8个检查，motion内部16个检查。
- 原车体/关节语义签名比较排除新增的七个明确质量为零的参考链接，其余模型数据保持一致。
  完整模型仍为118个网格、117个活动关节。CAD 导出布局保留已有 sensors.xacro 模板。
- 独立审查确认路由归属、静态QoS、环路防止和CAD米/毫米换算，指出默认RViz与文档遗漏，均补齐。
- 观察到退出时 guard 在 ROS context 关闭瞬间发布的竞态，增加失败→通过单测并修复；
  实际重跑关闭后无 ERROR/Traceback，运行时真实异常仍会抛出。

## 隔离实际仿真

ROS_DOMAIN_ID=183、Gazebo端口11479，从安装后的完整 sim_teleop.launch.py 启动，
关闭 GUI/键盘，用当前会话原始输入测试。监听器在机器人生成后才加入，以验证静态保留快照。

公开 /tf 与 /tf_static 总计11个 child（加world根为12帧）：
base_link、chassis_link、gimbal_yaw_link、wheels_link、lidar_link、lidar_aux_link、
camera_link、camera_optical_frame、gun_link、muzzle_link、odom。
完整显示通道检测到127个 child，含全部116个真实轮子/滚子帧。
公开可查询 world→muzzle_link，完整通道可查询 world→roller_112_link；
公开查询 world→wheel_1_link 按设计不可用，没有泄漏单轮帧。

实际移动期间 wheel_1_joint 转动约-1.894rad，轮地动力学保留。
小陀螺时 camera/gun/lidar 世界航向偏差分别约-0.000832、-0.000644、-0.0000263rad。
公开/完整消息数约404/555，未发生反馈环路。测量与世界坐标见 metrics.json。

安装 xyz/rpy 是当前原生CAD实例的机械参考；相机光心、雷达厂家驱动轴、真机外参未标定。
相机 optical frame 使用标准 x右/y下/z前，但原点仍为名义CAD原点。没有生成相机/雷达数据。
枪口是发射轴与测速模块前机械平面的名义交点，当前小yaw/pitch固定在保存姿态。

## 默认界面

官方机器人仿真中的 RViz 订阅完整显示总线，因此仍能显示转动的各个轮子；
TF 显示只启用部件参考轴，避免把112个滚子箭头画出来。
默认 GUI 的后续验证数据与截图存放 gui_metrics.json、desktop.png（完成后复制）。
独立 rm_arena 预览默认普通TF话题，保持不依赖机器人包。
