# sentry_sim

Gazebo Classic 机器人仿真集成包：引用 sentry_description 模型并添加接触、轻量全向圆柱轮力矩及云台插件。
`ros2 launch sentry_sim simulation.launch.py` 启动场地、车和 RViz。
完整FPS/键盘入口：`ros2 launch sentry_bringup sim_teleop.launch.py`，默认 `fps:=true`；
追加 `fps:=false` 切换旧键盘窗口，`keyboard:=false` 关闭输入节点。
模型网格维护在 sentry_description，键盘与保护维护在 sentry_motion。
详细配置、操作和物理限制见 [工作空间 README](../../README.md) 与
[simulation.md](../../docs/simulation.md)。

激光雷达为Odin1 Lite仿真：10Hz、240×180、120°×90°、0.15–25m，
`/lidar/points`输出PointCloud2。只有主lidar_link配置扫描；辅助TF仅保留兼容。
参数依据、实体驱动、地图服务入口及仿真限制见
[sentry_perception](../sentry_perception/README.md)。`perception:=false`仅关闭
点云转扫描节点；它不会关闭Gazebo中的激光扫描或枪口相机。

FPS仿真接口：`/fps/look` (`geometry_msgs/Vector3Stamped`) 的 `frame_id` 必须为
`world`，x为世界yaw、y为ROS世界pitch（负数向上），单位rad，z不用但必须有限。
无效坐标系或非有限分量会被拒绝；pitch限制为±60°。最后有效命令按单调接收时间
保持0.5秒，与暂停/回退的仿真时钟无关。失联后保持实际相对关节角；
`/spin_mode` 为true时恢复原有云台世界yaw保持。ROS消息stamp只作信息，不作跨时钟超时计算。

`/fps/view_pose` (`PoseStamped`, world, 50Hz) 是实际枪口相机位姿，
使用相机机械坐标约定：X前、Y左、Z上。它来自物理pitch link的实测姿态，
包含实际俯仰，绝不使用目标角冒充画面方向。旧 `/gimbal_pose` 继续报告yaw link。
插件发布两个云台轴的 `/joint_states`，与底盘插件的四个车轮状态互补。

相机在枪口前2cm，与枪管X轴对齐：`/fps/image_raw`、`/fps/camera_info`，
640×480、30Hz、80°水平视场；消息坐标系 `fps_camera_optical_frame` 为X右、Y下、Z前。
传感器直接挂载有惯量的 `gimbal_pitch_link`，固定TF别名被Gazebo合并也不丢相机。
`fps:=false` 关闭FPS输入窗口后相机仍按30Hz运行，会保留渲染开销。
ROS 2话题按camera_name前缀完整重映射，依据
[gazebo_ros_camera上游实现](https://github.com/ros-simulation/gazebo_ros_pkgs/blob/ros2/gazebo_plugins/src/gazebo_ros_camera.cpp)。

俯仰为新增仿真自由度，非实车CAD关节标定。零角严格复用原枪管CAD安装变换，
主雷达继续使用旧CAD安装位置作为占位，名义相机和光学参考保持原安装，均需实车标定。
物理关节±90°用于容纳原枪管约+18.13°的名义pitch，
从而覆盖FPS的世界pitch±60°；底盘大幅倾斜时不保证全部世界视向可达。
新增0.25kg、长0.144m、半径0.014m的圆柱惯量是仿真假设，尚未实测；
pitch反馈增益4Nm/rad、阻尼0.085Nm·s/rad，补偿此新增部件重力，力矩上限1Nm；
yaw仍为80Nm/rad、4Nm·s/rad、上限5Nm。控制器用实测枪口方向及两个实际关节轴
解世界yaw/pitch的Jacobian，并用世界角速度阻尼抵消底盘自转；不设置模型/底盘姿态。
这些参数需在ROS 2 Humble/Gazebo Classic上进一步验收和调谐。

Gazebo Classic仿真的目标环境为Ubuntu22.04/ROS2 Humble/Gazebo11；实体雷达入口
可以按厂商文档部署于Humble或Jazzy，不代表本仿真已迁移到新版Gazebo。
原29个场地碰撞盒为几何近似，机器人云台/相机/枪管缺少相应碰撞体；不能将画面中
所有上部重叠都视为场地碰撞失效。Windows离线逻辑、语法和资源检查不能替代
Ubuntu上的C++插件构建、GPU传感器、实际接触与FPS交互验收。
