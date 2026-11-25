# sentry_ws

## 13 个包的分工

| 包 | 内容 | 当前状态 |
| --- | --- | --- |
| sentry_map | 固定场地模型、场景和预览工具 | 已迁移 |
| sentry_description | 总装 URDF、车轮和转台、导航传感器安装配置 | 已更新为双雷达模型 |
| sentry_maps | 建图生成的 PCD、YAML/PGM 和设备 BIN 地图 | 等待实际地图 |
| sentry_sim | 场地与机器人组合、底盘和云台插件、仿真雷达 | 已迁移 |
| sentry_motion | 普通键盘遥控、限速和指令超时处理 | 已迁移 |
| sentry_perception | 点云转 LaserScan，后续加入过滤 | 转换入口已有 |
| sentry_sensors | 实体传感器驱动启动 | Odin 厂家驱动调用入口已有 |
| sentry_localization | 建图、定位和设备位姿适配 | Odin 地图服务客户端已有，定位集成待写 |
| sentry_navigation | Nav2 配置和导航入口 | 包骨架 |
| sentry_decision | 比赛决策行为树 | 包骨架 |
| sentry_referee_bridge | 裁判数据收发和协议解析 | 包骨架 |
| sentry_chassis_bridge | 实车底盘数据收发和协议解析 | 包骨架 |
| sentry_bringup | 系统组合启动 | 仿真遥控入口已有 |

## 目录约定

```text
sentry_ws/
├── src/
│   ├── sentry_map/models/、scenes/                 场地资源
│   ├── sentry_description/urdf/、meshes/、config/  机器人资源
│   ├── sentry_maps/maps/                         实际建图结果
│   ├── sentry_sim/src/chassis/、gimbal/           C++ 物理插件
│   ├── sentry_motion/src/sentry_motion/teleop/    Python 键盘控制
│   ├── sentry_perception/src/sentry_perception/filtering/
│   ├── sentry_localization/src/sentry_localization/mapping/、localization/
│   ├── sentry_decision/src/sentry_decision/conditions/、actions/、runtime/
│   ├── sentry_referee_bridge/src/sentry_referee_bridge/transport/、protocol/
│   └── sentry_chassis_bridge/src/sentry_chassis_bridge/transport/、protocol/
├── scripts/                                      构建与运行脚本
├── tools/                                        CAD 工具和离线检查
├── data/                                         录包和中间数据
└── docs/                                         使用说明、开发与调试记录
```

车体外观按本版总装简化，底盘与四轮使用圆角显示网格，两台雷达随大转台转动。当前运行配置使用双点云与普通键盘输入。

在构建并加载工作空间后，运行 `ros2 launch sentry_bringup sentry_sim_teleop.launch.py`，即可启动 Gazebo、RViz 和键盘窗口。[RViz 左栏、两路点云与按键说明](src/sentry_bringup/README.md) · [车体结构与镜头坐标](src/sentry_description/README.md)

Python 包通过 setup.py 安装模块、launch、配置和资源，通过 setup.cfg 设置 ROS 可执行入口路径。
package.xml、setup.py、setup.cfg 和 __init__.py 使用工具要求的名称。

## 调用入口

先按照仓库根目录 README 构建并加载工作空间。

```bash
ros2 launch sentry_bringup sentry_sim_teleop.launch.py
ros2 launch sentry_sim sentry_sim.launch.py
ros2 launch sentry_map sentry_map_preview.launch.py
ros2 launch sentry_perception sentry_pointcloud_to_scan.launch.py
ros2 run sentry_motion sentry_keyboard_control
```

Odin 通过 `/lidar/points` 接到 `/scan`，Mid-360S 单独发布 `/mid360s/points`。底盘接收 `/cmd_vel` 并发布 `/odom`。
`perception:=false` 关闭点云转换，`keyboard:=false` 关闭键盘节点。
同一机器人只运行一个遥控入口。多来源速度仲裁还没写，接自动导航时需要补上手动与自动切换。

实体 Odin 入口需要先安装并 source 与设备固件匹配的厂家驱动。
地图服务还需要厂家算法 SDK，安装外参与 TF 需实测确认。

```bash
ros2 launch sentry_sensors sentry_odin1_lite.launch.py
ros2 run sentry_localization sentry_odin_control slam
ros2 run sentry_localization sentry_odin_control save --path /绝对路径/map.bin
```

## 后续填写顺序

模型调用与普通遥控 → 点云检查 → 建图和地图保存 → 定位 → Nav2 → 决策行为树 → 裁判与底盘通信 → 真机组合启动。
裁判数据通过 ROS 消息进入决策，决策通过导航接口下发任务。
裁判接线、实际赛季协议和电控报文确定后，再实现相应通信包。

旧运行数据保存在 `docs/validation/`。这次目录调整后的编译和运行按 [调试步骤](docs/commissioning.md) 在 Ubuntu 中检查。
