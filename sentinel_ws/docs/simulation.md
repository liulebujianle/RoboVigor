# 仿真维护

## 模型、配置和资源

系统入口和操作见 [工作空间README](../README.md)。默认参数分别来自
sentry_bringup/config/sim.yaml（开关与速度）、sentry_sim/config/simulation.yaml（出生位置）、
sentry_motion/config/velocity_mux.yaml（超时和速度限制）。launch 参数覆盖已公开的默认值。

sentry_description/urdf/sentry.urdf.xacro 引用 chassis、gimbal、sensors，当前默认模型使用基础几何，
四轮使用圆柱及方向摩擦近似全向运动。活动关节为4轮、yaw和pitch共6个；没有112个被动滚子。
sentry_sim/urdf/sentry_sim.urdf.xacro 追加Gazebo接触、驱动、雷达和枪口相机配置。
spawn_robot.launch.py 在安装目录展开Xacro，将资源转换为安装目录绝对路径，发布物理描述供spawn_entity生成。

所有构建和运行资源从ament安装目录读取，修改后重新构建并source。旧CAD提取/模型生成工具面向原始模型，
不能保证重建当前FPS、Odin1 Lite与轻量几何；重新提取后需审查差异并运行回归，不能直接覆盖发布。

## 场地

当前场地显示为RMUL2027 DAE，已从固定GitHub提交恢复原始材质和贴图，并修复Classic索引/绕序兼容性。
model.sdf 仍使用29个封闭盒体碰撞，包含地台、围挡与平台。保留的field_collision.stl并未被当前SDF引用。
恢复工具、STEP/STL转换和来源见 [rm_arena说明](../src/rm_arena/README.md)。
场地碰撞是近似；机器人上部云台、雷达、相机、枪管没有对应碰撞体，不能保证上部不会视觉穿模。

## FPS与旧键盘

默认 fps:=true，点击就绪画面捕获鼠标；WASD按实际相机水平朝向移动，X小陀螺，C/空格停车，Esc释放并停车。
失焦、窗口停用和图像/位姿失联会停止FPS输出。旧模式 fps:=false 使用原Qt键盘窗口，
支持Q/E旋转，且旧模式失焦不主动停车。keyboard:=false 关闭输入窗口；底盘另有指令超时制动。
FPS相机和雷达仍可能运行，关闭窗口不会关闭渲染传感器。

/fps/look 使用world坐标，x为yaw，y为ROS pitch，单位rad。命令pitch限制约±60°；
物理pitch关节范围±90°用于容纳原CAD名义姿态。相机位于枪口前2cm，挂载物理pitch link。
/fps/view_pose 为实测物理相机姿态，不是目标视角；动力学仍使用有限力矩，不直接设置底盘姿态。
惯量与控制参数为仿真假设，实际画面、鼠标捕获、制动距离、接触行为需Ubuntu验收。

## Odin1 Lite

主雷达lidar_link为10Hz、240×180、120°×90°、0.15–25m的gpu_ray仿真，/lidar/points输出PointCloud2。
辅助lidar_aux_link仅为无外形TF别名。perception:=false只关闭点云转/scan，不能关闭激光传感器。
range_min/max在lidar.xacro和pointcloud_to_scan.yaml中保持一致；25m是仿真默认，
不复现真实反射率、光照、置信度或厂家RGB/IMU/SLAM。
实体设备使用独立入口，见 [Odin1 Lite说明](../src/sentry_perception/README.md)。

## 启动故障与验收

先关闭旧gzserver再启动，否则会因端口占用退出。当前场地launch在gzserver异常退出时记录警告，
不保证其他窗口同时退出；关闭Gazebo客户端窗口会结束组合launch。不要裸跑gzserver绕过资源路径设置。
无界面运行仍可能需要GPU/显示渲染配置；gui:=false不保证gpu_ray或相机可在任意机器运行。

当前验证结果和无法在Windows执行的项目见 [2026-11-14记录](validation/update_2026-11-14.md)。
目标环境需要执行colcon build、colcon test及test-result，并实际检查TF、点云、相机、轮地接触和停车。
