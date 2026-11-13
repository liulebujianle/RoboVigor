# RoboVigor 哨兵工作空间

当前源码包含 RMUL 2027 场地、轻量四轮全向机器人、云台 yaw/pitch、第一人称枪口相机、FPS/旧键盘控制、Odin1 Lite 激光仿真和实体驱动/地图服务接入入口。
Nav2 自动导航、机器人定位融合、底盘硬件通信、比赛任务与自瞄联动仍未完成。实体设备接入依赖厂家软件和安装标定，本仓库不包含厂家算法二进制。

## 环境与构建

完整仿真目标环境为 Ubuntu 22.04、ROS 2 Humble、Gazebo Classic 11、RViz2、PyQt5。
实体 Odin1 Lite 官方驱动另支持 Ubuntu 24.04/ROS 2 Jazzy；这不表示本项目的 Gazebo Classic 仿真已完成 Jazzy 适配。

在 ROS 已安装的环境中，从工作空间根目录安装依赖并构建：

```bash
source /opt/ros/humble/setup.bash
# 已初始化过 rosdep 的环境：
rosdep install --from-paths src --ignore-src -r -y
./scripts/build.sh
./scripts/sim.sh
```

已经构建好时直接运行 `./scripts/sim.sh`。等价启动命令：

```bash
source /opt/ros/humble/setup.bash
source install/setup.bash
ros2 launch sentry_bringup sim_teleop.launch.py
```

资源从 ament 包安装目录读取，修改 Xacro、配置、启动文件或脚本后应重新构建并 source。
先关闭旧仿真，避免旧 gzserver 占用端口。src 是源码，build/install/log 为生成产物。

## 默认 FPS 控制

默认 `fps:=true`。等待相机图像、世界视角和底盘位姿就绪，点击 FPS 窗口捕获鼠标。

| 操作 | 行为 |
| --- | --- |
| 鼠标左右/上下 | 控制世界 yaw/pitch，pitch 命令限制约 ±60° |
| W/S、A/D | 按实际相机水平朝向前后/横移，松开停止对应移动 |
| X | 开启底盘小陀螺 |
| C/空格 | 停车并关闭小陀螺 |
| Esc | 释放鼠标并停车 |
| 失焦、窗口停用、图像/位姿失联、关窗 | 释放控制或停止输出，不保证物理瞬时静止 |

默认平移 0.8 m/s、小陀螺 3 rad/s，可追加 `linear_speed:=1.0 spin_speed:=3.5`。
枪口相机位于枪口前 2 cm，输出 `/fps/image_raw` 和 `/fps/camera_info`。
接口与限制见 [sentry_motion](src/sentry_motion/README.md) 和 [sentry_sim](src/sentry_sim/README.md)。鼠标操作不执行开火或自瞄。

旧键盘模式：

```bash
./scripts/sim.sh fps:=false
```

旧模式支持 WASD、Q/E 旋转、X 小陀螺、C/空格全停；旧模式点窗口外不会主动停车。FPS 模式与旧模式的失焦行为不同。
`keyboard:=false` 关闭输入窗口，`fps:=false` 仅切换输入方式，不停用 Gazebo 枪口相机。
无界面运行可追加 `gui:=false rviz:=false keyboard:=false`，仍需可用的传感器渲染环境。
`gazebo:=false` 跳过机器人 spawn；独立模型预览应使用下方 description 入口。

## Odin1 Lite

仿真主雷达 lidar_link 使用 10 Hz、240×180、水平120°×垂直90°、0.15–25 m。
主雷达外形改为近似盒体；lidar_aux_link 仅保留兼容 TF，无外形和扫描传感器。
原安装坐标来自旧 CAD，不是新雷达已标定外参。

默认数据链为 `/lidar/points` → `/scan`。`perception:=false` 关闭转换节点，不会关闭激光传感器。
切片高度、角度和测距范围在 `src/sentry_perception/config/pointcloud_to_scan.yaml`，高度与角度在目标坐标系中计算。

实体设备入口在 source 厂家驱动和本工作空间后使用：

```bash
ros2 launch sentry_perception odin1_lite.launch.py
ros2 run sentry_perception odin_control.py slam
ros2 run sentry_perception odin_control.py save --path /tmp/odin_map.bin
ros2 run sentry_perception odin_control.py relocate --path /tmp/odin_map.bin
```

官方驱动需从厂家取得并与固件匹配，地图操作还依赖主机上的 manifold-lc-sdk。
实体入口默认关闭导航扫描，完成实际 TF 标定与高度切片验证后再开启。
.bin 是厂家重定位地图，不能直接作为 Nav2 的 YAML/PGM 地图。
完整部署、服务超时、原始点云分辨率差异及参数依据见 [Odin1 Lite 接入说明](src/sentry_perception/README.md)。

## 包与独立入口

| 包 | 职责与说明 |
| --- | --- |
| [rm_arena](src/rm_arena/README.md) | 场地显示、29个盒体碰撞、资源恢复/转换、场地预览 |
| [sentry_description](src/sentry_description/README.md) | 轻量几何、CAD来源、六个活动关节、部件TF |
| [sentry_sim](src/sentry_sim/README.md) | Gazebo驱动、云台控制、激光与枪口相机 |
| [sentry_motion](src/sentry_motion/README.md) | FPS/键盘输入、速度限制、失联制动 |
| [sentry_bringup](src/sentry_bringup/README.md) | 系统组合入口、默认参数、RViz配置 |
| [sentry_perception](src/sentry_perception/README.md) | 点云转扫描、实体Odin1 Lite驱动与地图服务入口 |

```bash
ros2 launch rm_arena world.launch.py                    # 场地
ros2 launch rm_arena arena_preview.launch.py            # 场地预览
ros2 launch sentry_sim simulation.launch.py             # 场地+车，不带输入窗口
ros2 launch sentry_description description.launch.py    # 独立模型发布/预览
```

机器人四轮使用圆柱和方向摩擦近似全向运动；当前6个活动关节为4轮、云台yaw和pitch。
不包含112个独立被动滚子，也没有底部 wheels_link 聚合坐标系。
枪管俯仰轴与0.25kg近似惯量为仿真假设，相机、雷达以及动力学参数均需实车标定。
场地当前采用29个盒体碰撞，保留的STL资源不表示当前碰撞已切换成三角网格。

## 验证与待验收

离线 Python/Xacro/场地资源检查与运行验收分开记录，最新记录见 [2026-11-14更新验证](docs/validation/update_2026-11-14.md)。
当前仍需在 Ubuntu 完成 colcon/C++ 构建、Qt交互、Gazebo GPU射线、轮地接触及FPS相机验收；实体设备还需驱动/算法安装、数据话题和服务联调、外参标定与重定位状态检查。
docs/validation/ 其他目录是历史证据，不能用其截图或测试数量证明当前版本已验收。

系统职责见 [docs/architecture.md](docs/architecture.md)，维护说明见 [docs/simulation.md](docs/simulation.md)，源码导航见 [docs/project_tree.md](docs/project_tree.md)。
规划文档描述未来目标，不代表功能已实现。Autoaim 保持为独立 Python 工程，不参与本工作空间 colcon 构建。
