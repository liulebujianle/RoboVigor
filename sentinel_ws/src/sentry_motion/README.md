# sentry_motion

在 `sentinel_ws` 中构建并加载环境后，通过组合入口运行：

```bash
source /opt/ros/humble/setup.bash
colcon build --base-paths src --packages-up-to sentry_bringup
source install/setup.bash
ros2 launch sentry_bringup sim_teleop.launch.py
```

默认 `fps:=true` 启动 `fps_control.py`：一个 Qt 枪口第一视角窗口和同进程速度看门狗。
图像按比例显示并带中央准星；点击画面捕获并隐藏鼠标，左右控制世界 yaw，上下控制俯仰（±60°）。
WASD 沿 **实际画面** 的水平朝向移动，X 开小陀螺，C/空格全停；没有开火功能。
Esc、失焦、关窗或图像/位姿超过 0.5 秒未更新都会清空按键和小陀螺并停车；恢复后需再次点击捕获。
保持鼠标不动时保留直线横向纠偏，转向时重置参考线以跟随实际视角。

接口：订阅 `/fps/image_raw` (`sensor_msgs/Image`，支持 rgb8/bgr8/rgba8 及行填充)、
`/fps/view_pose` (`geometry_msgs/PoseStamped`，`frame_id=world`)、`/odom`；
发布 `/fps/look` (`geometry_msgs/Vector3Stamped`，`frame_id=world`，x=世界 yaw，y=ROS pitch，负数朝上)、
`/cmd_vel` 和 `/spin_mode`。图像与位姿采用接收端单调时钟看门狗，不把仿真时间与墙上时钟混用。

`fps:=false` 保留旧键盘窗口；`keyboard:=false` 关闭整个输入节点。
`linear_speed`、`angular_speed`、`spin_speed` 启动参数保持兼容；FPS 使用鼠标转动视角，不使用 Q/E。

旧键盘模式：

```bash
ros2 launch sentry_bringup sim_teleop.launch.py fps:=false
```

一个进程、一个节点：`keyboard_control.py` = Qt 键盘窗口 + 同进程速度看门狗。
窗口读真实按下/松开事件，直接调用看门狗的 `receive()` / `update()`，由该节点发 `/cmd_vel`
与 `/spin_mode`。

- 启动 gyro=false；X 开启小陀螺，C/空格全停；关窗会先发一帧全停。
- W/S前后、A/D横移、Q/E普通旋转；点击旧键盘窗口后操作。
- 按住移动键连续走，松开即停；斜向合速度不超过 `--linear`。
- 看门狗仍做限速（1.2 m/s、4 rad/s）、0.5 s 失联归零，以及小陀螺下按云台朝向直线平移。
- 旧键盘窗口失焦不会主动清空状态；停止时使用松键、C/空格或关窗。FPS模式另有失焦停车保护。

不再有 `/teleop/<会话>/` 中转话题，也没有独立 guard 进程（`sim_teleop` 的 `keyboard:=false`
可直接关掉整个键盘节点）。当前没有 Nav2 多源仲裁/速度平滑/碰撞监测后端。
雷达更新不意味着已加入自动避障；FPS视角控制也不会触发开火或真实硬件控制。
完整操作见 [工作空间 README](../../README.md)。

逻辑测试位于 `test/test_keyboard*.py`、`test/test_fps_logic.py`，窗口测试位于
`test/test_fps_window.py`，需要ROS2及PyQt5。离线逻辑检查不能代替Ubuntu上的
Qt捕获/释放鼠标、暂停仿真停车和Gazebo实际运动验收。
