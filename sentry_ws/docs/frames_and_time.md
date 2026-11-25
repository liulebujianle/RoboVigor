# TF 和时间

Gazebo 联合启动以 `world` 为固定坐标系。独立模型预览由静态发布者直接连接 `world → base_link`。下图列出联合启动时 RViz 接收的 TF。

```text
world
└── odom
    └── base_link
        └── chassis_link
            ├── wheel_1_link
            ├── wheel_2_link
            ├── wheel_3_link
            ├── wheel_4_link
            └── gimbal_yaw_link
                ├── small_yaw_link
                ├── barrel_mesh_frame
                ├── odin1_lite_mount_link
                │   └── odin1_lite_link
                │       └── lidar_link
                └── mid360s_link

front_camera_link
└── front_camera_optical_frame
```

`wheel_1_link` 到 `wheel_4_link` 依次对应左后、左前、右前和右后轮。独立模型预览、键盘联合仿真和场地仿真三个 RViz 配置均默认启用四个轮心的坐标轴。只启动场地预览时，场地节点只发布场地数据。

## 文件和发布者

| 内容 | 文件或发布者 |
| --- | --- |
| 四轮、底盘及轮轴 | `sentry_description/urdf/chassis.xacro` |
| 大 yaw 和小 yaw | `sentry_description/urdf/gimbal.xacro` |
| 雷达外壳、扫描原点和兼容名 | `sentry_description/urdf/sensors.xacro` 与 `config/frames.yaml` |
| 枪管外观参考系 | `sentry_description/src/sentry_description/sentry_display_description.py` 使用上装 visual 的原点 |
| 镜头本体到光学系 | `sentry_description/launch/sentry_description.launch.py` 中的静态发布者 |
| 车体内部 TF | `sentry_description/launch/sentry_description.launch.py` 中的 robot_state_publisher |
| `world → odom` | `sentry_sim/launch/sentry_spawn_robot.launch.py` 中的静态发布者，变换为零 |
| `odom → base_link` | Gazebo 底盘插件，使用世界真值 |

仿真中底盘插件发布四轮角度，转台插件发布大 yaw 和小 yaw 角度。独立模型预览使用 joint_state_publisher 或其滑块窗口产生关节状态。robot_state_publisher 读取 `/joint_states` 后更新各活动关节的 TF。

`/robot_description` 用于 RViz 显示，`/sentry_description/robot_description_physics` 用于 Gazebo 生成。后者由 `sentry_description_publisher` 发布，包含仿真插件和传感器。

## 坐标和安装

四轮中心相对 `chassis_link` 为 (±0.167317, ±0.167317, -0.036188) m，轴线保留 CAD 的 45° 布局。圆柱轮半径 76.1 mm，轴向宽 39.798 mm。长度用米，角度用弧度。

枪管与前相机外壳的外观合并在 `sentry_turntable.dae` 中。`barrel_mesh_frame` 位于该网格原点。Odin 默认只显示 `odin1_lite_link` 扫描轴，外壳到扫描原点的 TF 仍用于点云。使用 `ros2 launch sentry_description sentry_description.launch.py camera_view:=true` 可同时查看整车与前相机的局部坐标轴。

实体 Odin1 Lite 原始点云默认使用厂家 `lidar` 坐标。安装时需要测量它到机器人参考系的变换，核对厂家 TF 与机器人 TF 的父子关系。雷达随云台转动时，还需要真实关节状态。设备内部相机与 Body 外参从实际标定数据读取。

## 时间

仿真状态、robot_state_publisher 和 RViz 使用 `/clock`。键盘输入超时和插件命令超时使用接收端单调时钟，Gazebo 暂停或时间回退时仍会过期。实体雷达点云转换使用 `use_sim_time:=false`。

机器人定位融合、厂家地图帧与机器人 TF 的连接、`map → odom` 都还没实现。接定位时先统一坐标与时间，再检查点云、里程计和扫描在机器人运动时是否对齐。接口见 [interfaces.md](interfaces.md)。
