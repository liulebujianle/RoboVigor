# 当前话题与服务接口

以下区分Gazebo仿真和实体Odin1 Lite入口。源码中的接口定义不表示设备联调已完成。

## 仿真话题

| 话题 | 类型 | 发布者 → 接收者 | 说明 |
| --- | --- | --- | --- |
| `/cmd_vel` | geometry_msgs/Twist | fps_control或keyboard_control → omni drive | m/s、rad/s；底盘插件按车体坐标执行，输入节点先完成视角/云台方向转换 |
| `/spin_mode` | std_msgs/Bool | 输入节点 → gimbal stabilizer | 小陀螺时的云台世界航向保持请求 |
| `/odom` | nav_msgs/Odometry | omni drive → 输入节点/调试 | Gazebo实际姿态；odom/world重合，不是编码器或实车定位 |
| `/joint_states` | sensor_msgs/JointState | 底盘与云台插件 → RSP | 分别发布四轮与yaw/pitch，单位rad、rad/s |
| `/gimbal_pose` | geometry_msgs/PoseStamped | 云台插件 → 旧键盘控制 | world中的yaw云台实际姿态 |
| `/fps/look` | geometry_msgs/Vector3Stamped | fps_control → 云台插件 | world帧，x=世界yaw、y=ROS pitch，负pitch向上，z不用但须有限 |
| `/fps/view_pose` | geometry_msgs/PoseStamped | 云台插件 → fps_control | 50Hz，world中实际枪口相机机械姿态，x轴向前 |
| `/fps/image_raw` | sensor_msgs/Image | Gazebo相机 → fps_control | 640×480、30Hz；frame为fps_camera_optical_frame |
| `/fps/camera_info` | sensor_msgs/CameraInfo | Gazebo相机 → 调试/视觉处理 | 相机内参及光学帧 |
| `/lidar/points` | sensor_msgs/PointCloud2 | Gazebo激光插件 → 点云转扫描/RViz | Odin1 Lite近似，10Hz、240×180、0.15–25m，frame为lidar_link |
| `/scan` | sensor_msgs/LaserScan | pointcloud_to_laserscan → 调试/后续导航 | 默认base_link中的高度/角度切片，尚未接入Nav2 |
| `/robot_description` | std_msgs/String | RSP → RViz | 六活动关节、四轮独立TF的显示描述 |
| `/sentry_description/robot_description_physics` | std_msgs/String | physics_description_publisher → spawn_entity | Gazebo完整物理描述，包含插件和仿真传感器 |
| `/arena_marker` | visualization_msgs/Marker | rm_arena → RViz | world、米、嵌入材质；Reliable/TransientLocal，depth=1 |

FPS命令限制世界pitch为±60°，物理pitch关节范围±90°。图像光学坐标为x右/y下/z前，
与view_pose的机械坐标x前/y左/z上不同。命令超时按接收端单调墙钟计算，仿真消息stamp用 `/clock`。
输入窗口和速度看门狗同进程，一次launch只启动一个输入节点，没有 `/teleop/<会话>/` 中转。

`perception:=false`只关闭转扫描节点；不关闭Gazebo激光传感器。
`fps:=false`只切换旧键盘输入，不关闭相机。接口和TF细节见 [frames_and_time.md](frames_and_time.md)。

## 实体Odin1 Lite

入口：`ros2 launch sentry_perception odin1_lite.launch.py`，需要已经安装并source匹配固件的
官方 `odin_ros_driver_rev1`。默认 `/scan`转换关闭，避免未标定的数据进入导航。
话题/服务前缀默认 `/manifold/device0/`，实际设备索引应从device_online确认。

| 名称（默认完整路径） | 类型 | 含义 |
| --- | --- | --- |
| `/manifold/device0/cloud/raw` | sensor_msgs/PointCloud2 | 原始点云；默认frame_id=lidar，不能直接等同机器人lidar_link |
| `/manifold/device0/cloud/slam` | sensor_msgs/PointCloud2 | 厂家SLAM点云 |
| `/manifold/device0/imu` | sensor_msgs/Imu | 厂家原始IMU输出 |
| `/manifold/device0/odometry_lf`、`odometry_hf` | nav_msgs/Odometry | 厂家位姿/里程计；未自动融合到本机器人TF |
| `/manifold/device0/device_mode` | odin_ros_driver_rev1/srv/DeviceMode | 本客户端使用1=Normal、3=SLAM、4=Relocation、5=ReMap |
| `/manifold/device0/save_map` | odin_ros_driver_rev1/srv/SaveMap | 保存厂家二进制地图 |
| `/manifold/device0/load_map` | odin_ros_driver_rev1/srv/LoadMap | 加载已有地图 |
| `/manifold/device0/exploy_map` | odin_ros_driver_rev1/srv/ExployMap | 导出；服务拼写来自厂家接口，格式由算法插件决定 |

`odin_control.py`按顺序调用模式与地图服务，检查success/error_code，失败或超时停止。
超时不表示设备没有执行，重试前检查状态；服务成功也不代表重定位已收敛。
建图/重定位需要额外 `manifold-lc-sdk` 算法deb。图像、标定、更多数据通道与服务由
厂家驱动提供，完整步骤见 [雷达接入README](../src/sentry_perception/README.md)。
本项目没有伪造这些服务，也没有实现完整实车底盘协议、Nav2 Action或定位融合。
