# TF与时间：四轮、云台yaw/pitch与传感器

默认模型每个轮子在实际轮轴中心有一个独立TF，随该轮旋转；没有 `wheels_link`
聚合坐标或独立滚子TF。当前仿真主树如下：

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
                ├── lidar_link              # Odin1 Lite仿真占位
                ├── lidar_aux_link          # 旧兼容别名，无外形/扫描
                ├── camera_link
                │   └── camera_optical_frame
                └── gimbal_pitch_link       # 新增俯仰自由度
                    └── gun_link
                        └── muzzle_link
                            └── fps_camera_link
                                └── fps_camera_optical_frame
```

## 文件归属与发布者

- `sentry_description/urdf/chassis.xacro`：四轮link/joint/origin/axis及底盘。
- `urdf/gimbal.xacro`：主yaw云台；`urdf/sensors.xacro`：pitch、传感器/枪管/枪口与FPS相机参考。
- `config/frames.yaml`：原CAD名义参考，主雷达安装占位及辅助别名状态。
- `launch/description.launch.py`：可视/TF描述生成、唯一robot_state_publisher。
- `scripts/description_publisher.py`：Gazebo完整物理描述发布。

`world → odom`由 `spawn_robot.launch.py` 的静态发布者提供，二者在仿真中重合。
`odom → base_link`由底盘插件以Gazebo实际姿态发布；车体内部TF由robot_state_publisher
读取 `/joint_states` 发布。底盘插件提供四轮状态，云台插件提供yaw/pitch状态，二者覆盖不同关节。

模型有两个话题：`/robot_description`供RViz与原生TF，
`/sentry_description/robot_description_physics`供Gazebo生成。两者均有六个活动关节，
使用轻量基础几何，四轮接触采用方向摩擦近似，不创建112个滚子刚体。
RViz采用标准RobotModel与 `/tf`、`/tf_static`，不依赖私有TF或MarkerArray轮子动画。

## 安装和坐标约定

四轮中心相对chassis_link为(±0.167317,±0.167317,-0.036283)m，轴线保留CAD的45°布局，
圆柱半径76.1mm、轴向宽39.798mm。CAD参考的单位为米/弧度。

新增pitch关节零角复用原gun_link的安装变换，枪管与枪口随pitch运动。
原 `camera_link` 与雷达直接挂在yaw部分，不随新增pitch关节运动。
`camera_optical_frame`为x右/y下/z前，仍是名义CAD相机参考，未经真实光心标定。
枪口为发射轴与测速模块前机械平面的名义交点。

FPS相机在枪口前2cm，`fps_camera_link`机械轴为x前/y左/z上；其光学帧为x右/y下/z前。
`/fps/view_pose`报告实际物理pitch部件导出的相机姿态，不是鼠标目标角。
`/fps/look`要求world帧，x=世界yaw、y=ROS pitch（负数向上），单位弧度。

实体Odin1 Lite由独立厂家驱动输出，默认原始点云frame_id为 `lidar`。
它与仿真 `lidar_link`不是自动等价关系；不能只改消息标签来冒充安装变换。
必须使用实测标定连接机器人与厂家TF，检查单一父节点，并提供可转云台的真实关节状态。
内置相机/Body外参从设备标定读取，不复制手册示例到任意设备。

## 时间与验收边界

仿真状态、图像及RSP/RViz使用仿真时钟 `/clock`；FPS/键盘失联和插件命令保持
使用接收端单调墙钟，暂停/回退仿真不会无限延长命令有效期。
实体雷达转换启动显式使用 `use_sim_time:=false`。

本项目尚未接入机器人定位融合或Nav2的 `map → odom`。厂家地图帧与当前机器人TF之间
需按实际定位方案集成，不能把Gazebo真值里程计当作实车定位结果。
详见 [接口](interfaces.md)及[雷达说明](../src/sentry_perception/README.md)。
