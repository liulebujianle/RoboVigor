# sentry_sim

Gazebo Classic 仿真集成包。Python 启动文件组合 `sentry_map` 场地和
`sentry_description` 机器人模型；两个 C++ 插件参与 Gazebo 物理更新，负责
四轮力矩驱动与雷达转台稳定。模型几何、网格和惯量维护在 `sentry_description`。

```bash
ros2 launch sentry_sim sentry_sim.launch.py
```

该入口启动场地、机器人和 RViz。单独生成机器人使用
`ros2 launch sentry_sim sentry_spawn_robot.launch.py`，需要已有 Gazebo 场地。
键盘操作通过 `ros2 launch sentry_bringup sentry_sim_teleop.launch.py` 启动，
输入和保护逻辑维护在 `sentry_motion`。初始位置和实体名见 `config/sentry_simulation.yaml`。

## 物理插件

- `src/chassis/sentry_omni_drive.cpp` → `libsentry_omni_drive.so`：
  订阅 `/cmd_vel`，发布 `/odom`、`odom → base_link` 和实测车轮 `/joint_states`。
  命令失联 0.5 秒后制动，超时使用单调接收时钟。
- `src/gimbal/sentry_gimbal_stabilizer.cpp` → `libsentry_gimbal_stabilizer.so`：
  订阅 `/spin_mode`，开启时保持上装的世界航向，关闭时保持转台相对底盘的当前角度。
  以 50 Hz 向 `/joint_states` 发布大 yaw 和空载小 yaw 的实测关节状态。`/gimbal_pose` 描述承载两台雷达的大 yaw。小 yaw 在 Gazebo 中自由转动。

两个插件只施加有界关节力矩，不直接修改机器人或 link 位姿。
`test/test_omni_kinematics.cpp` 验证轮地接触运动学，
`test/test_gimbal_math.cpp` 验证持续底盘旋转时的航向保持和力矩边界。

## 激光与运行环境

`urdf/gazebo/lidar.xacro` 定义两个 `gpu_ray`，各自发布 `sensor_msgs/msg/PointCloud2`。

| 设备 | 话题 | 点云 frame_id | 仿真设置 |
| --- | --- | --- | --- |
| Odin1 Lite | `/lidar/points` | `odin1_lite_link` | 10 Hz，240 × 180，水平 120°、垂直 90°，0.15–25 m |
| Mid-360S | `/mid360s/points` | `mid360s_link` | 10 Hz，水平 360°、垂直 −7° 到 +52°，0.1–40 m |

Livox 的 500 × 40 规则采样近似每秒 20 万次测距，实物使用随时间变化的扫描轨迹。40 m 取自 10% 反射率、100 klx 时的典型值；实际截止量程是 100 m。Odin 的默认 25 m 对应 10% 反射率、低于 50 klx，固定 3 cm 高斯噪声是近似。设备规格和 `/scan` 的输入见 [点云处理说明](../sentry_perception/README.md)。

Gazebo 默认画出两组射线。Odin 的扫描原点在右侧 TX 窗正前方的亚克力护板外表面，和 `/lidar/points` 的 `odin1_lite_link` 重合。传感器插件的位姿相对这个坐标系是零。查看安装偏移可以运行 `ros2 run tf2_ros tf2_echo odin1_lite_mount_link odin1_lite_link`，预期平移为 (0.041, 0.015, 0) m。

Gazebo Classic 用黑色半透明扇面画最小量程内的盲区，蓝色从盲区的外缘开始。检查 Odin 是否对准时看扇面尖端，蓝线从离窗口 15 cm 处开始。两组射线在 Gazebo 中可以重叠，按设备区分回波可以看 RViz 的两路点云。

总启动的 RViz 会分别订阅这两个话题。在另一个已加载工作空间的终端可检查帧名和转台到雷达的 TF。

```bash
ros2 topic echo /lidar/points --once --field header --qos-reliability best_effort
ros2 topic echo /mid360s/points --once --field header --qos-reliability best_effort
ros2 run tf2_ros tf2_echo gimbal_yaw_link mid360s_link
```

目标环境为 Ubuntu 22.04、ROS 2 Humble、Gazebo 11。场地碰撞盒是几何近似，
机器人部分上部显示件没有对应碰撞体。C++ 插件构建、激光数据和轮地接触效果
仍需在 Ubuntu/ROS 环境验证。
