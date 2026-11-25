# 源码目录

完整目录和搭建顺序见 [根目录 TREE.md](../../TREE.md)，各包状态见 [工作空间说明](../README.md)。这里记录常用的查找位置。

| 内容 | 位置 |
| --- | --- |
| 固定场地 | `src/sentry_map/models/`、`scenes/` |
| 固定车体 | `src/sentry_description/urdf/`、`meshes/`、`config/` |
| 建图结果 | `src/sentry_maps/maps/`，目前没有实际地图 |
| Gazebo 插件 | `src/sentry_sim/src/chassis/`、`gimbal/` |
| 仿真总启动 | `src/sentry_bringup/launch/sentry_sim_teleop.launch.py` |
| 普通键盘控制 | `src/sentry_motion/src/sentry_motion/teleop/` |
| 实体雷达启动 | `src/sentry_sensors/launch/sentry_odin1_lite.launch.py` |
| 点云转扫描 | `src/sentry_perception/launch/sentry_pointcloud_to_scan.launch.py` |
| 地图服务客户端 | `src/sentry_localization/src/sentry_localization/mapping/` |
| Nav2 | `src/sentry_navigation/`，待写 |
| 比赛行为树 | `src/sentry_decision/`，待写 |
| 裁判与底盘通信 | `src/sentry_referee_bridge/`、`src/sentry_chassis_bridge/`，待写 |
| 构建脚本、开发工具 | `scripts/`、`tools/` |
| 本地数据 | `data/` |
| 历史调试结果 | `docs/validation/` |

共 13 个 ROS 包。Python 模块放各包的 `src/包名/`，Gazebo 原生插件使用 C++。模型和场地直接调用，厂家驱动、算法 SDK 另行安装。

[target_tree.md](target_tree.md) 保存早期规划，其中的包名、语言选择和文件清单已不完全适用。