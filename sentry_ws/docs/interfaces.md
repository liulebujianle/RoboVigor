# 话题和服务

## Gazebo 仿真

| 话题 | 类型 | 发布者 → 接收者 | 说明 |
| --- | --- | --- | --- |
| `/cmd_vel` | geometry_msgs/Twist | 键盘控制 → 底盘插件 | 车体坐标，x 前、y 左，m/s、rad/s |
| `/spin_mode` | std_msgs/Bool | 键盘控制 → 云台插件 | 请求小陀螺航向保持 |
| `/odom` | nav_msgs/Odometry | 底盘插件 → 键盘控制、调试 | Gazebo 世界真值；odom 与 world 重合 |
| `/joint_states` | sensor_msgs/JointState | 底盘、云台插件 → robot_state_publisher | 四轮和 yaw/pitch，rad、rad/s |
| `/gimbal_pose` | geometry_msgs/PoseStamped | 云台插件 → 键盘控制 | world 中的实际 yaw 云台姿态 |
| `/lidar/points` | sensor_msgs/PointCloud2 | Gazebo 雷达 → 点云转扫描、RViz | lidar_link，10 Hz、240×180、0.15–25 m |
| `/scan` | sensor_msgs/LaserScan | pointcloud_to_laserscan → 调试 | 默认在 base_link 内裁剪，导航待接 |
| `/robot_description` | std_msgs/String | robot_state_publisher → RViz | 车体显示描述 |
| `/sentry_description/robot_description_physics` | std_msgs/String | sentry_description_publisher → spawn_entity | 含插件和仿真传感器的完整描述 |
| `/arena_marker` | visualization_msgs/Marker | sentry_map → RViz | world，米；Reliable、TransientLocal，depth=1 |

普通键盘节点把小陀螺平移方向转换到车体坐标后发送 `/cmd_vel`。当前只有一个手动速度来源，多来源仲裁还没写。输入窗口和速度看门狗在同一进程中，超时使用接收端单调时钟。

`perception:=false` 只关闭点云转扫描，`keyboard:=false` 关闭输入窗口。当前不启动选手视角或相机图像话题。TF 与时间见 [frames_and_time.md](frames_and_time.md)。

## 实体 Odin1 Lite

入口是 `ros2 launch sentry_sensors sentry_odin1_lite.launch.py`，需要先安装并 source 与固件匹配的 `odin_ros_driver_rev1`。默认关闭扫描转换，安装 TF 和裁剪参数检查后再开启。

默认前缀是 `/manifold/device0/`，设备索引从厂家 device_online 信息确认。

| 默认路径 | 类型 | 用途 |
| --- | --- | --- |
| `/manifold/device0/cloud/raw` | sensor_msgs/PointCloud2 | 原始点云，默认 frame_id=lidar |
| `/manifold/device0/cloud/slam` | sensor_msgs/PointCloud2 | 厂家 SLAM 点云 |
| `/manifold/device0/imu` | sensor_msgs/Imu | 厂家 IMU 输出 |
| `/manifold/device0/odometry_lf`、`odometry_hf` | nav_msgs/Odometry | 厂家位姿，机器人 TF 融合待写 |
| `/manifold/device0/device_mode` | odin_ros_driver_rev1/srv/DeviceMode | 1=Normal、3=SLAM、4=Relocation、5=ReMap |
| `/manifold/device0/save_map` | odin_ros_driver_rev1/srv/SaveMap | 保存厂家二进制地图 |
| `/manifold/device0/load_map` | odin_ros_driver_rev1/srv/LoadMap | 加载已有地图 |
| `/manifold/device0/exploy_map` | odin_ros_driver_rev1/srv/ExployMap | 导出地图，拼写沿用厂家接口 |

地图客户端是 `ros2 run sentry_localization sentry_odin_control`，按顺序调用服务并检查 success/error_code。超时或失败后停止后续步骤，重试前先看设备状态；服务成功后还要观察定位是否收敛。完整命令见 [建图定位](mapping_and_localization.md)。

实机服务、点云和 TF 还没有完成设备联调。Nav2 Action、比赛决策接口、裁判和底盘报文等实现后再补充到本页。