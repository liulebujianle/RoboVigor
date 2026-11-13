# sentry_description

轻量机器人模型、四个独立轮轴与雷达/相机/枪管参考坐标的维护包。默认模型使用
基础几何保留主要尺寸和装配关系，原始CAD与网格资源作为来源保留。

- `urdf/chassis.xacro`：wheel_1_link～wheel_4_link，保留新装配体的45°布局，原点位于各自轮轴中心，随实测轮角旋转。
- `urdf/gimbal.xacro`：主云台关节。
- `urdf/sensors.xacro`、`config/frames.yaml`：一个Odin1 Lite仿真占位、旧辅助雷达兼容TF、相机/光学及枪管/枪口参考。雷达沿用旧CAD安装位置，需实车标定。
- `launch/description.launch.py`：生成标准RViz/TF描述，启动唯一原生robot_state_publisher。
- `scripts/description_publisher.py`：保留Gazebo完整物理模型的话题发布。

不再有底部聚合 wheels_link、每个滚子的TF、wheel_visuals.py或MarkerArray车轮显示。
RViz直接用标准RobotModel；每个主轮的可视几何随其独立TF旋转。当前使用4个圆柱轮的方向摩擦近似，不再计算112个被动滚子。

`/robot_description`供RViz/TF，`/sentry_description/robot_description_physics`供Gazebo。
完整启动仍为 `ros2 launch sentry_bringup sim_teleop.launch.py`。
名义传感器位姿不是实车标定值。详细树及话题职责见
[frames_and_time.md](../../docs/frames_and_time.md)。

当前为轻量全向底盘：轮径152.2 mm、宽39.798 mm；数据见 config/wheel_dimensions.json。
轮子用圆柱可视/碰撞，轴向低摩擦近似全向自由度。普通实心轮胎若使用各向同性摩擦，并不能在此布局下实现全向运动。
当前车体为盒体、云台为圆柱和盒体组合；默认Xacro不加载三角网格。
原始及低面数网格仍保留，不能把它们的外形或碰撞精度当作当前默认模型的精度。
共有6个活动关节（4轮+云台yaw/pitch），雷达/名义摄像头等固定TF保留。
底盘和车轮具有碰撞体，云台、相机与枪管显示部件未配置对应碰撞体，可能出现上部视觉穿模。

FPS新增pitch轴位于原gun_link的CAD安装原点，零角时gun_link、muzzle_link位姿不变。
原config/frames.yaml仍记录完整CAD名义安装；gun_link的原固定变换被等价拆成
gimbal_pitch_joint原安装变换与gun_link_fixed恒等变换。仅枪管/枪口与新FPS相机跟随pitch，
原camera_link、camera_optical_frame、lidar_link、lidar_aux_link保持原安装。
雷达外形已换为Odin1 Lite近似盒体；lidar_aux_link仅保留TF，无外形和传感器。
实体驱动及地图服务入口见 [sentry_perception](../sentry_perception/README.md)。
新增fps_camera_link位于枪口前2cm；fps_camera_optical_frame为X右、Y下、Z前。
仿真惯量、关节限位及相机话题详见 [sentry_sim](../sentry_sim/README.md)；不代表实车机械或传感器标定。

模型与坐标检查位于 `test/`。涉及展开Xacro的测试需要 `xacro`、`numpy`、`PyYAML`
和ROS包索引；源文件解析通过不等于Gazebo物理接触或传感器外参已经验收。
