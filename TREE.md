# RoboVigor_WS 工程结构

哨兵导航放在 `sentry_ws`，共 13 个包。原来的 Autoaim 独立维护，不参与这次调整。包名统一用 `sentry_` 开头，包里的代码再按功能分目录。

能用 Python 写的就用 Python。Gazebo 的底盘和云台插件继续用 C++。

## 目录

这里只列包和主要目录。模型零件、通用构建文件不展开。

```text
RoboVigor_WS/
├── README.md
├── TREE.md
└── sentry_ws/
    ├── src/
    │   ├── sentry_map/                       # 场地模型
    │   │   ├── models/
    │   │   ├── scenes/
    │   │   ├── launch/
    │   │   └── src/sentry_map/                # 场地发布、预览工具
    │   │
    │   ├── sentry_description/               # 车体模型
    │   │   ├── urdf/
    │   │   ├── meshes/
    │   │   ├── config/
    │   │   ├── launch/
    │   │   └── src/sentry_description/        # 模型发布
    │   │
    │   ├── sentry_maps/                      # 建图后保存的地图
    │   │   └── maps/rmul_2027/
    │   │       ├── pointcloud/               # 点云地图
    │   │       ├── occupancy/                # 栅格地图
    │   │       └── odin/                     # Odin 原生地图
    │   │
    │   ├── sentry_sensors/                   # 实体传感器
    │   │   ├── launch/                       # 调用厂家驱动
    │   │   └── src/sentry_sensors/drivers/    # 后面需要的驱动适配
    │   │
    │   ├── sentry_sim/                       # Gazebo 仿真
    │   │   ├── launch/
    │   │   ├── config/
    │   │   ├── urdf/                         # 仿真插件配置
    │   │   └── src/
    │   │       ├── chassis/                  # 底盘插件，C++
    │   │       └── gimbal/                   # 云台插件，C++
    │   │
    │   ├── sentry_perception/                # 点云处理
    │   │   ├── launch/
    │   │   ├── config/
    │   │   └── src/sentry_perception/
    │   │       └── filtering/                # 点云过滤，待写
    │   │
    │   ├── sentry_localization/              # 建图、定位
    │   │   └── src/sentry_localization/
    │   │       ├── mapping/                  # 建图和地图服务调用
    │   │       └── localization/             # 定位数据接入，待写
    │   │
    │   ├── sentry_navigation/                # Nav2，待写
    │   │   ├── config/                       # 规划器、控制器、代价地图参数
    │   │   ├── launch/
    │   │   ├── behavior_trees/               # 导航执行和恢复流程
    │   │   └── src/sentry_navigation/
    │   │
    │   ├── sentry_motion/                    # 键盘控制、速度限制
    │   │   ├── config/
    │   │   ├── launch/
    │   │   └── src/sentry_motion/teleop/
    │   │
    │   ├── sentry_decision/                  # 比赛决策，待写
    │   │   ├── behavior_trees/               # 比赛策略
    │   │   ├── config/                       # 策略参数、任务点位
    │   │   ├── launch/
    │   │   └── src/sentry_decision/
    │   │       ├── conditions/               # 判断比赛阶段、车辆状态
    │   │       ├── actions/                  # 发目标、取消任务等动作
    │   │       └── runtime/                  # 运行行为树、保存共享状态
    │   │
    │   ├── sentry_referee_bridge/            # 裁判通信，待写
    │   │   ├── config/
    │   │   ├── launch/
    │   │   └── src/sentry_referee_bridge/
    │   │       ├── transport/                # 数据收发
    │   │       └── protocol/                 # 报文解析、校验
    │   │
    │   ├── sentry_chassis_bridge/            # 实车底盘通信，待写
    │   │   ├── config/
    │   │   ├── launch/
    │   │   └── src/sentry_chassis_bridge/
    │   │       ├── transport/                # 与电控收发数据
    │   │       └── protocol/                 # 编码速度指令、解析底盘反馈
    │   │
    │   └── sentry_bringup/                   # 总启动
    │       ├── launch/
    │       ├── config/
    │       └── rviz/
    │
    ├── scripts/                              # 构建、运行脚本
    ├── tools/                                # 开发和检查工具
    ├── data/                                 # 录包、临时数据
    └── docs/                                 # 项目说明、调试记录
```

Python 代码主要放在各包的 `src/包名/` 下面，参数放 `config/`，启动文件放 `launch/`。`package.xml`、`setup.py`、`setup.cfg`、`__init__.py` 这些文件保留标准名字。

## 模型和地图分开放

`sentry_map` 放赛场模型，`sentry_description` 放车体 URDF 和三维模型。这两部分平时直接调用，调导航时不进去改零件。仿真需要的配置放在 `sentry_sim`，方便和原模型分开。

建图得到的点云、栅格地图和设备原生地图放在 `sentry_maps`。原始录包和临时结果先放 `data/`，整理好后再保存到地图目录。目前地图目录还是空的。

场地相关命名用 `map`。旧仿真里还留着 `world`，坐标系这部分留到接定位时统一处理，导航的全局坐标系用 `map`。

## 决策、导航和裁判怎么接

比赛决策单独写在 `sentry_decision`。它读裁判状态，判断比赛是否开始，再决定去哪个点、什么时候换任务。目标交给 `sentry_navigation`，由 Nav2 规划路线、控制机器人到达。

两个包都有 `behavior_trees/`：决策包里放比赛策略，导航包里放导航执行和失败后的恢复流程。

裁判报文的收发、校验和解析放在 `sentry_referee_bridge`。解析后的数据通过 ROS 消息交给决策。具体接哪个接口、是否由电控转发，等接线和报文格式确定后再写。

后面要接成这样：

```text
裁判数据 → sentry_referee_bridge → sentry_decision
                                      ↓ 导航目标
                               sentry_navigation
                                      ↓ 速度指令
                                 sentry_motion
                                      ↓
                       sentry_chassis_bridge / sentry_sim
                              实车底盘 / 仿真底盘
```

`sentry_motion` 现在已有普通键盘控制、限速和输入超时停车，不再使用之前的选手视角。自动导航接进来后，还要补手动和自动指令的切换。目前还没有多来源的速度仲裁。

## 怎么启动

车放到赛场上后，打算从 `sentry_bringup` 启动传感器、定位、导航、裁判通信和决策。程序先运行起来，决策等裁判状态确认比赛开始，再下发任务。

实车的总启动还没写。目前可以调用的是仿真遥控入口：

```bash
ros2 launch sentry_bringup sentry_sim_teleop.launch.py
```

## 后面怎么写

1. 先把工作空间和 Python 包的结构弄清楚，自己建包、编译、运行一个节点。
2. 加载场地和车体模型，用普通键盘控制仿真车。
3. 接传感器，检查点云和坐标变换，再做需要的过滤。
4. 做建图、地图保存和定位，把地图整理到 `sentry_maps`。
5. 接 Nav2，先让车到达一个目标点，再试多个点。
6. 写决策，先用模拟的裁判状态测试比赛开始判断和任务切换。
7. 接真实的裁判、底盘通信，最后补上实车总启动，一起调试。

每一步先确认输入、输出和运行结果，再接下一个模块。

目前已有场地和车体模型、键盘控制、Gazebo 插件、仿真雷达和点云转扫描的代码。Odin 部分有厂家驱动启动文件和地图服务客户端，还需要接设备调试。导航、决策、裁判通信和实车底盘通信都只是建好了包，具体程序还没写。Ubuntu 下的完整运行和实车效果也还没验证。
