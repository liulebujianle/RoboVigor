# RoboVigor 哨兵工作空间

当前已实现：RMUL 2027 场地、真实 CAD 哨兵、四轮及 112 滚子物理驱动、RViz、键盘控制与云台小陀螺。
本次按桌面《算法导航提示词.md》的职责拆包。导航、建图、真机雷达、定位、通信及自瞄联动尚未实现；不将目录或启动成功视为具备这些功能。

```bash
cd /home/ethan/RoboVigor/sentinel_ws
./scripts/build.sh
./scripts/sim.sh
```

已经构建好时可直接 `./scripts/sim.sh`。等价的 ROS 入口：

```bash
source /opt/ros/humble/setup.bash
source install/setup.bash
ros2 launch sentry_bringup sim_teleop.launch.py
```

先关闭旧仿真。点击 RoboVigor 键盘控制窗口：按住 W/S 前后、A/D 横移，松开即停止平移；Q/E 普通旋转。
启动默认关闭小陀螺，按一次 X 开启，C/空格全停；切换窗口也全停。
默认平移 0.8 m/s，小陀螺 3 rad/s。可追加 `linear_speed:=1.0`、`spin_speed:=3.5`。
无界面回归可追加 `gui:=false rviz:=false keyboard:=false`。

| 包 | 维护位置与职责 |
| --- | --- |
| rm_arena | 场地 world、完整模型材质、场地 Marker、场地预览 |
| sentry_description | CAD 网格、chassis/gimbal/sensors Xacro、robot_state_publisher |
| sentry_sim | Gazebo 插件、仿真 Xacro、出生配置、模型生成 |
| sentry_motion | 键盘源、速度限制、失联制动、小陀螺坐标转换 |
| sentry_bringup | 已验证模块的组合、系统仿真默认参数和 RViz 配置 |

场地单独启动：`ros2 launch rm_arena world.launch.py`；场地预览：
`ros2 launch rm_arena arena_preview.launch.py`；车与场地不带键盘：
`ros2 launch sentry_sim simulation.launch.py`；模型发布：
`ros2 launch sentry_description description.launch.py`。

完整文件列表与迁移对应见 [docs/project_tree.md](docs/project_tree.md)，模块状态见
[docs/architecture.md](docs/architecture.md)。旧包 sentry_simulation 已退出源码与安装索引，
其旧启动命令应换为上述入口。Autoaim 保持独立，未改动。

每次启动使用独立 control_session 原始输入话题，旧键盘窗口不能控制新仿真。
新键盘窗口由 launch 直接管理，关闭主启动后会一起退出，不再留下 GNOME 终端孤儿进程。

`src` 是维护的源码，`build/install/log` 是生成产物。运行资源全部从 ament 包安装目录读取。
当前环境为 Ubuntu 22.04、ROS 2 Humble、Gazebo Classic 11；不需要下载新的外部算法仓库。

部件TF维护在 `src/sentry_description`。四个轮子各有独立的 wheel_1_link～wheel_4_link，
直接跟随实际轮角；定义在 urdf/chassis.xacro。雷达/相机/枪管定义在 sensors.xacro 与 frames.yaml。
没有底部 wheels_link 和独立滚子TF；不再使用专门的车轮Marker绘制。见 docs/frames_and_time.md。
