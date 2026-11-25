# 工程结构

工作空间共 13 个包，完整分工见 [工作空间说明](../README.md)。场地模型放 `sentry_map`，车体模型放 `sentry_description`，建图结果放 `sentry_maps`。调导航时直接调用固定模型，仿真插件和参数放在 `sentry_sim`。

Python 代码放各包的 `src/包名/`。Gazebo 底盘、云台插件使用 C++，其余现有程序和启动文件使用 Python。Autoaim 独立维护。

## 仿真启动链

总入口是 `ros2 launch sentry_bringup sentry_sim_teleop.launch.py`：

1. `sentry_sim/sentry_sim.launch.py` 调用 `sentry_map/sentry_map.launch.py`，加载场地、Gazebo 和 RViz。
2. `sentry_sim/sentry_spawn_robot.launch.py` 展开仿真 Xacro，检查安装资源和插件，生成机器人。
3. `sentry_description/sentry_description.launch.py` 启动 robot_state_publisher 和物理描述发布节点。
4. `sentry_motion/sentry_motion.launch.py` 启动普通 Qt 键盘窗口，限速和输入超时处理也在这个进程中。
5. `sentry_perception/sentry_pointcloud_to_scan.launch.py` 将 `/lidar/points` 转为 `/scan`。

`gazebo`、`gui`、`rviz`、`keyboard` 控制对应部分。`perception:=false` 只关闭点云转扫描，雷达仍在仿真模型中。当前没有选手视角控制。

## 模型和坐标

默认模型使用轻量几何，四个圆柱轮通过方向摩擦近似全向运动。四轮轴、云台 yaw 和 pitch 共六个活动关节，实际角度由插件发布到 `/joint_states`，再由 robot_state_publisher 发布车体 TF。

底盘发布 `odom → base_link`，仿真启动文件保留重合的 `world → odom`。`/odom` 来自 Gazebo 世界真值。导航计划使用 `map`，但旧 `world` 坐标还没统一，`map → odom` 定位融合也没接入。

场地使用 29 个近似碰撞盒。车体上部的云台、雷达、相机和枪管没有对应碰撞体；质量、惯量、摩擦和控制参数还需要标定。模型中保留的相机参考系不表示启动了相机或视角窗口。

## 实体雷达

`sentry_sensors/sentry_odin1_lite.launch.py` 调用单独安装的 Odin1 Lite 厂家驱动。地图服务客户端位于 `sentry_localization`，提供建图、保存、重定位、ReMap 和导出操作。算法由厂家 SDK 提供，设备安装外参和机器人 TF 还需要联调。

## 后面要接的模块

```text
裁判数据 → sentry_referee_bridge → sentry_decision
                                      ↓ 导航目标
                               sentry_navigation
                                      ↓ 速度指令
                                 sentry_motion
                                      ↓
                       sentry_chassis_bridge / sentry_sim
```

Nav2、比赛决策、裁判通信和实车底盘通信目前是包骨架。手动和自动速度仲裁、完整建图定位、实车总启动还没写，`sentry_maps` 也没有实际地图。

运行与调试见 [仿真说明](simulation.md)、[调试步骤](commissioning.md) 和 [建图定位](mapping_and_localization.md)。旧版本运行数据保存在 `validation/`。