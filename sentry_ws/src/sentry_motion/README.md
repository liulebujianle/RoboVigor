# sentry_motion

普通 Qt 键盘窗口和同进程速度看门狗，使用 `ament_python` 构建。

```text
sentry_motion/
├── src/sentry_motion/teleop/sentry_keyboard_control.py
├── launch/sentry_motion.launch.py
├── config/velocity_mux.yaml
├── resource/sentry_motion
├── setup.py
├── setup.cfg
└── package.xml
```

在 `sentry_ws` 中构建并加载环境：

```bash
source /opt/ros/humble/setup.bash
colcon build --base-paths src --packages-up-to sentry_motion
source install/setup.bash
ros2 launch sentry_motion sentry_motion.launch.py
```

随场地和机器人一起启动时，使用组合入口：

```bash
ros2 launch sentry_bringup sentry_sim_teleop.launch.py
```

单独运行键盘节点：

```bash
ros2 run sentry_motion sentry_keyboard_control
```

启动参数为 `keyboard`（默认 `true`）、`linear_speed`（默认 `0.8` m/s）、
`angular_speed`（默认 `1.5` rad/s）、`spin_speed`（默认 `3.0` rad/s）。
`keyboard:=false` 关闭输入节点。直接运行时对应的速度选项是
`--linear`、`--angular`、`--spin-speed`。

点击键盘窗口后操作：

- 按住 W/S 前后、A/D 横移，松开即停；Q/E 普通旋转。
- X 开启小陀螺；C/空格清空按键并全停；启动时小陀螺关闭。
- 斜向合速度不超过设置的平移速度；看门狗默认限制平移 1.2 m/s、旋转 4 rad/s。
- 小陀螺时，平移方向锁定到开始旋转时的实际云台世界航向，并保留直线横向纠偏。
- 输入或小陀螺心跳超过 0.5 秒未更新时归零；小陀螺需要新鲜的底盘与云台位姿。
- 切到 RViz 或 Gazebo 窗口会立即松开移动键。X 开启的小陀螺继续旋转，按 C、空格或关闭键盘窗口即可全停。

节点名为 `simulation_velocity_guard`，发布 `/cmd_vel` (`geometry_msgs/Twist`)
和 `/spin_mode` (`std_msgs/Bool`)，订阅 `/odom` (`nav_msgs/Odometry`)
和 `/gimbal_pose` (`geometry_msgs/PoseStamped`，世界坐标系)。
看门狗使用单调时钟；参数在 `config/velocity_mux.yaml` 中配置。
当前只处理键盘输入，尚未实现 Nav2 等多来源速度仲裁。键盘窗口没有第一人称视角控制。

依赖由 `package.xml` 声明，包括 `rclpy`、消息包、launch 和 `python3-pyqt5`。
`test/test_keyboard_control.py` 覆盖按键、限速、看门狗、直线纠偏及 Qt 窗口事件，
需要安装 ROS 2 与 PyQt5。在 `sentry_ws` 中运行：

```bash
python3 -m unittest discover -s src/sentry_motion/test -p 'test_keyboard*.py'
```

Qt 窗口输入和 Gazebo 实际运动效果仍需在 Ubuntu 上验证。
