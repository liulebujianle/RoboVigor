# sentry_bringup

组合场地、机器人、Gazebo、RViz、FPS/键盘控制与点云转扫描节点。速度等默认参数从 `config/sim.yaml` 显式读取，出生位置来自 `sentry_sim/config/simulation.yaml`。
此入口用于仿真；实体 Odin1 Lite 使用独立的 [雷达入口](../sentry_perception/README.md)，尚未集成 Nav2 或完整实车系统启动。

完整入口与包职责见 [工作空间 README](../../README.md)。

## FPS 仿真操作

默认 `fps:=true`，启动：

```bash
ros2 launch sentry_bringup sim_teleop.launch.py
```

等待枪口相机画面后，点击 FPS 窗口捕获鼠标。画面中央显示十字准星。
鼠标左右转动枪口世界朝向，上下控制俯仰（世界俯仰范围约±60°）。
W/S 沿当前实际视角水平朝向前后，A/D 左右平移；斜向合速度有限幅。
X 开启底盘小陀螺；视角不随底盘自转。鼠标不动时按住 W 保持直线，
按住 W 再转鼠标时，移动方向跟随实际相机朝向转弯。
C/空格全停，Esc 释放鼠标并停车；失焦、最小化或相机/位姿超时同样停车。
关闭窗口会发送全停。鼠标控制不会触发开火、自瞄或真实硬件接口。

`fps:=false` 使用原键盘窗口；`keyboard:=false` 不启动输入窗口。
枪口相机在 `fps:=false` 或 `keyboard:=false` 时仍配置为30Hz，会保留渲染开销。

默认平移速度为0.8m/s，普通键盘旋转为1.5rad/s，小陀螺为3rad/s，可通过
`linear_speed`、`angular_speed`、`spin_speed`调整。无输入窗口运行可使用：

```bash
ros2 launch sentry_bringup sim_teleop.launch.py gui:=false rviz:=false keyboard:=false
```

仿真默认包含 Odin1 Lite 激光扫描，输出 `/lidar/points`，并转换为 `/scan`。
`perception:=false` 仅关闭点云转扫描节点，不关闭激光传感器；`gazebo:=false`
关闭Gazebo及机器人生成，也就没有仿真传感器数据。扫描范围为0.15–25m，
更新频率10Hz；配置位置和实体驱动条件见 [sentry_perception](../sentry_perception/README.md)。

内部接口：`/fps/image_raw`、`/fps/camera_info`、`/fps/view_pose`、`/fps/look`。
view_pose 是实际相机 +X 向前的机械方向；图像消息使用标准光学坐标系。
仿真新增俯仰关节，零角保留原枪口 CAD 位姿，雷达和原相机安装参考不变。
俯仰惯量与力矩参数为仿真假设，不能作为真实机构标定或控制参数使用。

更新源码后，在 `sentinel_ws` 中构建组合入口所需的包及其依赖：

```bash
source /opt/ros/humble/setup.bash
colcon build --base-paths src --packages-up-to sentry_bringup
source install/setup.bash
ros2 launch sentry_bringup sim_teleop.launch.py
```

验收：先静止测试鼠标和准星，再 X 开陀螺按 W 检查直线，再按住 W 转鼠标。
检查 Esc、失焦、关闭窗口和暂停仿真时停车。当前 Windows 侧的离线检查
不能替代 Ubuntu 上的完整构建、Qt 交互、Gazebo 渲染及实际运动验证。
