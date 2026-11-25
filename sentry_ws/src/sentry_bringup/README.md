# sentry_bringup

组合启动场地、机器人、RViz、普通键盘和点云转扫描。在 `sentry_ws` 构建并加载环境后运行：

```bash
ros2 launch sentry_bringup sentry_sim_teleop.launch.py
```

默认会打开 Gazebo、RViz 和「RoboVigor 键盘控制」三个窗口。Gazebo 显示物理仿真，RViz 显示 TF 和传感器数据。

先点击键盘窗口。W/S 前进、后退，A/D 左移、右移，Q/E 向左、向右转。按住移动，松键停止对应方向。切到 Gazebo 或 RViz 会松开移动键。X 开启小陀螺，C 或空格全停。

开关参数为 `gazebo`、`gui`、`rviz`、`keyboard`、`perception`；
`x`、`y`、`z` 设置初始位置，`linear_speed`、`angular_speed`、`spin_speed` 设置键盘速度。
默认值见 `config/sentry_sim.yaml` 和 `sentry_sim/config/sentry_simulation.yaml`。

键盘使用普通 Qt 窗口，没有第一人称视角控制。Nav2、决策、裁判通信和实车底盘通信
目前只有包骨架，未接入此入口；实车总启动也尚未实现。各包现状见仓库根目录 README。

## RViz 左栏怎么读

左侧只保留 `Displays`。勾选一行会显示对应内容，展开小三角可以看它的设置。两个预览共用以下项目。

| 左栏项目 | 用途 |
| --- | --- |
| Global Options | 控制整个三维视图。正常驾驶时参考系 `Fixed Frame` 用 `world`。 |
| Global Status | 总体状态。出现黄色或红色时展开，看提示里缺哪个坐标变换或话题。 |
| 车体模型 | 看机器人外形和关节姿态，读取 `/robot_description`。 |
| 场地 | 看赛场的位置和障碍物外形，读取 `/arena_marker`。 |
| 坐标系 TF | 默认开启。四轮各在轮心显示一组轴，底盘、转台、两台雷达及上装外观参考系也可见。展开 `Frames` 可单独开关每个坐标系。红、绿、蓝依次代表 X、Y、Z。 |

轮号 1、2、3、4 依次对应左后、左前、右前、右后。Odin 上默认只画点云扫描轴 `odin1_lite_link`，外壳轴 `odin1_lite_mount_link` 可以在 `Frames` 里手动打开。勾选 `Show Names` 可直接查看每组轴的名称。[TF 树与发布关系](../../docs/frames_and_time.md)

总启动还会显示 **Odin1 Lite 点云**（青色，`/lidar/points`）和 **Mid-360S 点云**（橙色，`/mid360s/points`）。勾掉其中一项就能单看另一台雷达，Gazebo 仍继续发布两路数据。独立模型预览里改为 **俯仰角示意**，用来读预览表盘的度数。

RViz 顶部保留 `Move Camera`，操作鼠标可查看模型和缩放。驾驶前先点一下独立的键盘窗口，将输入焦点给它。此次去掉了网格，以及 Selection、Tool Properties、Views、Time 面板和交互选点工具。

### 查看镜头自身的坐标轴

镜头目前提供 `front_camera_link → front_camera_optical_frame` 局部关系。光学系的 X 向图像右边，Y 向下，Z 朝镜头前方。可在已加载工作空间的终端检查：

```bash
ros2 run tf2_ros tf2_echo front_camera_link front_camera_optical_frame
```

联合启动运行时，可以在另一个已加载相同环境的终端打开镜头局部视图。短粗轴表示镜头本体，长细轴表示光学系，长蓝轴指向镜头前方。左栏可以分别开关这两组轴。镜头自身的原点与车体之间的安装位姿尚未定义。

```bash
rviz2 -d "$(ros2 pkg prefix --share sentry_description)/rviz/sentry_front_camera.rviz"
```
