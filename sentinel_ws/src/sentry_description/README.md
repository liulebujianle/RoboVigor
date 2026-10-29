# sentry_description

机器人模型、四个独立轮轴与雷达/相机/枪管参考坐标的维护包。

- `urdf/chassis.xacro`：wheel_1_link～wheel_4_link，原点位于各自实际轮轴中心，随实测轮角旋转。
- `urdf/gimbal.xacro`：主云台关节。
- `urdf/sensors.xacro`、`config/frames.yaml`：两颗雷达、相机/光学、枪管/枪口CAD名义参考。
- `launch/description.launch.py`：生成标准RViz/TF描述，启动唯一原生robot_state_publisher。
- `scripts/description_publisher.py`：保留Gazebo完整物理模型的话题发布。

不再有底部聚合 wheels_link、每个滚子的TF、wheel_visuals.py或MarkerArray车轮显示。
RViz直接用标准RobotModel；每个主轮的可视几何随其独立TF旋转。Gazebo仍计算112个被动滚子物理。

`/robot_description`供RViz/TF，`/sentry_description/robot_description_physics`供Gazebo。
完整启动仍为 `ros2 launch sentry_bringup sim_teleop.launch.py`。
名义传感器位姿不是实车标定值。详细树及话题职责见工作空间 docs/frames_and_time.md。
