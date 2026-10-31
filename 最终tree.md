# RoboVigor 最终代码地图（Odin1 · 单棵树）

> 合并自 `mid360版本tree.md`（现状：已有代码与行数）+ `odin1 的tree.txt`（目标：要建的包）；雷达统一为 Odin1。
> 状态：✅ 已有　⬜ 待建（M1→M4 顺序）　📦 第三方　🚫 暂不建　▢ 资源文件
> 基线：ROS 2 Humble / Ubuntu 22.04 原生 / Gazebo Classic 11 + RViz。

```text
F:\RoboVigor\
├── README.md                              3 行导航，指向 sentinel_ws/README.md
├── .gitignore                             忽略 build/ install/ log/ __pycache__/ data/*
├── mid360版本tree.md                       历史：Mid-360 时期的现状快照（存档）
├── odin1 的tree.txt                        历史：Odin1 目标草案（存档）
├── 最终tree.md                             ← 本文件
│
├── Autoaim/                               📦 独立 Python 自瞄工程，不经 colcon，与仿真完全解耦
│   ├── README.md                          大恒 Galaxy SDK 安装顺序 + autoaim_start 用法
│   ├── setup.py                           pip install -e . → 控制台命令 autoaim_start
│   ├── MANIFEST.in                        打包权重：weight/*.pt|onnx|engine
│   ├── .gitignore                         忽略 __pycache__ / *.log
│   └── RV_Autoaim_2026/
│       ├── __init__.py             22 行  统一导出 9 个类（re-export）
│       ├── start.py               258 行  入口：解析相机/兵种颜色/网页端口 → 装配模块 → 主循环
│       ├── autoaim.py             305 行  主循环：取帧 → 检测 → PnP → 卡尔曼 → 弹道 → 发布/推流
│       ├── camera.py              204 行  大恒取流线程，只保留最新帧
│       ├── detector.py             73 行  YOLOv8 推理（onnx / TensorRT engine）
│       ├── pnp_solver.py           76 行  solvePnP：像素框 → 相机系 3D 位姿
│       ├── kalman_tracker.py       99 行  角度卡尔曼 + 目标卡尔曼
│       ├── ballistic_solver.py     87 行  弹道补偿：初速/重力 → pitch 补偿角
│       ├── publisher.py            72 行  按兵种组帧，串口或 ROS 发 yaw/pitch
│       ├── monitor.py             205 行  Flask + MJPEG 网页监视
│       ├── logger.py               22 行  极简文件日志
│       └── weight/                  ▢ 9 个模型 ~220 MB
│
└── sentinel_ws/                           ROS 2 Humble 工作区（colcon）
    ├── README.md                          入口命令、按键表、包职责
    ├── dependencies.repos                 ⚙ vcstool 清单（Odin 驱动来源 + 固定提交）
    │
    ├── docs/
    │   ├── architecture.md                入口链、包职责、TF 原则
    │   ├── interfaces.md                  话题/服务注册表（新增 /lidar/points、/scan 要登记）
    │   ├── frames_and_time.md             TF 树、时间源、map→odom 由谁发
    │   ├── simulation.md                  怎么起仿真、怎么看
    │   ├── commissioning.md               验收流程
    │   ├── chassis_protocol.md            真机串口协议
    │   ├── mapping_and_localization.md    Odin 建图、加载地图、定位验证
    │   ├── hardware.md                    Odin1 数量、固件、安装方式
    │   ├── sentry_urdf_import.md          CAD→URDF 方法与坑
    │   ├── project_tree.md                现状目录（历史）
    │   ├── target_tree.md                 目标树（历史）
    │   └── validation/                    ▢ 每次改动的证据：截图 + metrics + probe 脚本
    │
    ├── scripts/
    │   ├── build.sh                       6 行  source Humble + colcon build --base-paths src
    │   ├── sim.sh                        11 行  source install + launch sim_teleop
    │   ├── mapping.sh                     ⬜ 建图入口
    │   ├── nav.sh                         ⬜ 导航入口
    │   ├── bag_record.sh                  ⬜ 录 /scan /odom /tf /cmd_vel
    │   └── replay.sh                      ⬜ 回放（不重复启动真实设备）
    │
    ├── deploy/                            ⬜ 真机才用
    │   ├── sentry-nav@.service            ⬜ systemd 开机自启
    │   └── udev/
    │       ├── 99-sentry.rules            ⬜ 底盘设备权限
    │       └── 99-odin.rules              ⬜ Odin 设备权限
    │
    ├── tools/                             COLCON_IGNORE，开发期脚本，不进包
    │   ├── import_sentry_cad.py   219 行  CAD 一键导入：SLDASM → 底盘/云台/4 轮 + 118 个 STL
    │   ├── sentry_wheels.py       162 行  滚子识别：轴线匹配、球碰撞与惯量
    │   ├── sentry_frames.py        79 行  从 CAD 实例反算 6 个传感器坐标系 → frames.yaml
    │   ├── sentry_model_layout.py  53 行  把完整模型拆成 description（纯）+ sim（Gazebo）
    │   ├── tests/                         ✓ 3 个：CAD 解析、包边界与模型指纹、轮轴手性
    │   └── vendor/sldprt/                 ▢ MIT SolidWorks 解析器（保留 LICENSE）
    │
    ├── data/                              COLCON_IGNORE，本机数据
    │   ├── README.md
    │   ├── bags/                          ▢ rosbag 录制
    │   ├── mapping/                       ▢ 建图中间数据
    │   └── odin_runtime/                  ▢ 设备标定/日志（不写入源码）
    │
    ├── build/ install/ log/               生成物，不提交，重新 build 会重建
    │
    └── src/
        │
        ├── rm_arena/                                        ✅ 场地
        │   │   功能：Gazebo world + RMUL 2027 场地模型 + 场地 Marker + RViz 预览（只给仿真）
        │   ├── launch/simulation.launch.py          81 行  场地总启动：gzserver/gzclient + marker + rviz2
        │   ├── launch/world.launch.py               13 行  只开 Gazebo
        │   ├── launch/arena_preview.launch.py       13 行  只开 RViz 预览
        │   ├── rm_arena/arena_marker.py             59 行  一条 latched MESH_RESOURCE → /arena_marker
        │   ├── models/rmul_2027/                     ▢ model.sdf + 32 个 DAE + 1 张纹理（44 MB）
        │   ├── worlds/arena.world                   18 行  只 include model://
        │   ├── rviz/arena.rviz                     205 行  场地预览视角
        │   └── test/                                 ✓ 资源自包含 + launch 环境/退出联动
        │
        ├── sentry_description/                              ✅ 模型层
        │   │   功能：纯 URDF —— 车体、云台、传感器坐标系；一个 <gazebo> 都没有
        │   ├── urdf/sentry.urdf.xacro                6 行  唯一入口，只 include 三个文件
        │   ├── urdf/chassis.xacro                  241 行  车体 + 4 轮 + 112 滚子（宏化；精简版 96 行去滚子）
        │   ├── urdf/gimbal.xacro                    24 行  chassis →(0,0,0.051)→ gimbal_yaw_link
        │   ├── urdf/sensors.xacro                   19 行  6 个纯坐标系，位姿全部来自 frames.yaml
        │   ├── config/frames.yaml                   46 行  ★ lidar_link / camera / gun / muzzle 的 xyz·rpy
        │   ├── meshes/                               ▢ 118 个 STL / 44 MB
        │   ├── launch/description.launch.py         96 行  显示模型（无滚子）+ 物理模型（latched）
        │   ├── scripts/description_publisher.py     37 行  发 /sentry_description/robot_description_physics
        │   └── test/                                 ✓ 网格与地面间隙、坐标系正交性、显示模型折叠
        │
        ├── sentry_sim/                                      ✅ 仿真层
        │   │   功能：Gazebo 外壳 —— 材质、接触参数、两个 C++ 插件、虚拟传感器
        │   ├── urdf/sentry_sim.urdf.xacro          181 行  include 模型 + 灰色材质 + 两个插件 + 滚子接触
        │   ├── urdf/gazebo/lidar.xacro               ⬜ 待加：Odin1 仿真替身 → /lidar/points
        │   ├── src/omni_drive.cpp                  193 行  四轮力矩驱动 + /odom + TF + /joint_states
        │   ├── src/gimbal_stabilizer.cpp           121 行  云台锁世界朝向 + /gimbal_pose
        │   ├── include/sentry_sim/omni_kinematics.hpp 15 行 全向轮公式
        │   ├── include/sentry_sim/gimbal_math.hpp     17 行 hold_heading()
        │   ├── launch/simulation.launch.py          44 行  场地 + 机器人（gazebo/gui/rviz 开关）
        │   ├── launch/spawn_robot.launch.py         77 行  展开 xacro → 校验 mesh/.so → spawn_entity
        │   ├── config/simulation.yaml                3 行  出生点 (1.25, 6.75, 0.118)
        │   └── test/                                 ✓ 轮速符号、云台绕圈收敛
        │
        ├── sentry_motion/                                   ✅ 遥控层
        │   │   功能：Qt 键盘窗口 + 同进程速度看门狗，唯一发 /cmd_vel 的地方
        │   ├── scripts/keyboard_control.py         305 行  窗口 20 ms 节拍 → 限速 1.2 m/s → /cmd_vel
        │   ├── launch/motion.launch.py              27 行  只起这一个节点（keyboard + 三个速度）
        │   ├── config/velocity_mux.yaml              7 行  超时 0.5 s / max_linear 1.2 / max_angular 4.0
        │   └── test/                                 ✓ 限速、失联、状态机、直线纠偏、窗口事件
        │
        ├── sentry_bringup/                                  ✅ 组合层
        │   │   功能：把各包拼成可运行入口 + 默认参数 + RViz；不写逻辑
        │   ├── launch/sim_teleop.launch.py          38 行  唯一入口：include sim + motion
        │   ├── launch/sim_navigation.launch.py       ⬜ 仿真 + Nav2
        │   ├── launch/sim_mapping.launch.py          ⬜ 仿真 + 建图
        │   ├── launch/robot_navigation.launch.py     ⬜ 真机：Odin 定位 + 感知 + Nav2
        │   ├── launch/robot_mapping.launch.py        ⬜ 真机建图
        │   ├── launch/replay.launch.py               ⬜ bag 回放
        │   ├── config/sim.yaml                       7 行  gui/rviz/keyboard + 三个速度
        │   ├── config/robot.yaml                     ⬜ 定位来源 + Odin 配置
        │   └── rviz/navigation.rviz                245 行  默认视角（雷达显示加这里）
        │
        ├── sentry_perception/                               ⬜ M1 现在做
        │   │   功能：把 3D 点云变成导航能吃的 2D 数据
        │   ├── launch/pointcloud_to_scan.launch.py  25 行  /lidar/points → /scan
        │   ├── config/pointcloud_to_scan.yaml       15 行  ★ 高度带 / 角度 / 量程
        │   ├── src/cloud_filter.cpp                  ⬜ 去车体点、范围裁剪
        │   ├── config/cloud_filter.yaml              ⬜
        │   ├── src/terrain_analysis.cpp              ⬜ 地形（坡度、可通行性）
        │   └── config/terrain.yaml                   ⬜
        │
        ├── sentry_localization/                             ⬜ M2
        │   │   功能：回答“车在地图哪里”——设备位姿 → odom + map→odom，含失效监测
        │   ├── src/odometry_adapter.cpp              ⬜ 设备位姿 → 车体里程计（处理安装外参）
        │   ├── src/localization_monitor.cpp          ⬜ 数据超时、初始化、定位有效性
        │   ├── src/relocalization_client.cpp         ⬜ 重定位请求与状态
        │   ├── launch/localization.launch.py         ⬜
        │   ├── launch/mapping.launch.py              ⬜
        │   ├── config/odometry_adapter.yaml          ⬜ 源话题 / 源坐标系 / TF 开关
        │   └── test/test_frame_conversion.cpp        ⬜ 外参与位姿转换
        │
        ├── sentry_maps/                                     ⬜ M3（纯资产，无代码）
        │   │   功能：地图与航点的仓库，让 launch 能按名字加载
        │   └── maps/rmul_2027/
        │       ├── navigation/map.pgm + map.yaml     ⬜ Nav2 二维地图（12.3×8.3 m，0.05 m/格）
        │       ├── odin/prior.bin + metadata.yaml    ⬜ Odin 原生先验地图
        │       ├── geometry/prior.pcd                ⬜ 可选几何点云
        │       ├── regions.yaml                      ⬜ 区域划分
        │       ├── waypoints.yaml                    ⬜ 巡逻点
        │       └── manifest.yaml                     ⬜ 资源清单
        │
        ├── sentry_navigation/                               ⬜ M4
        │   │   功能：回答“怎么过去”——Nav2 参数与启动（costmap / planner / controller / BT）
        │   ├── launch/navigation.launch.py           ⬜ 只起 Nav2 节点
        │   ├── params/nav2.yaml                      ⬜ ⚠ 全向底盘先跑差速行为（vy=0）
        │   ├── params/costmap.yaml                   ⬜ footprint 按 0.534×0.534（含保险杠）
        │   └── params/behavior.yaml                  ⬜ 恢复行为
        │
        ├── sentry_sensors/                                  ⬜ 真机时建
        │   │   功能：把设备变成标准话题——拉起官方 odin_ros_driver，统一话题名 / QoS / 时间源
        │   ├── launch/odin.launch.py                 ⬜
        │   ├── config/sensor_topics.yaml             ⬜ 关键：官方话题 → /lidar/points
        │   ├── config/odin_odometry.yaml             ⬜ 里程计模式
        │   ├── config/odin_mapping.yaml              ⬜ 建图模式
        │   ├── config/odin_localization.yaml         ⬜ 定位模式
        │   └── rviz/odin_debug.rviz                  ⬜ 看点云、位姿与设备坐标系
        │
        ├── sentry_chassis_bridge/                           ⬜ 真机时建
        │   │   功能：串口/CAN ↔ /cmd_vel, /odom, /joint_states（仿真里由 omni_drive 扮演这个角色）
        │   └── src/ + config/chassis.yaml            ⬜ 协议见 docs/chassis_protocol.md
        │
        ├── odin_ros_driver/                                 📦 第三方
        │   │   功能：厂商官方驱动，保留原包名、按 dependencies.repos 固定版本，不改源码
        │   └── ...                                   📦 clone 到 src/ 下参与构建
        │
        ├── sentry_tasks/                                    🚫 最后
        │   │   功能：比赛逻辑——巡逻、决策、状态机（等 Nav2 能跑再写）
        │   └── ...
        │
        ├── sentry_interfaces/                               🚫 按需
        │   │   功能：自定义 msg/srv/action（标准消息够用就别建）
        │   └── ...
        │
        └── sentry_nav_plugins/                              🚫 可永不建
            │   功能：自研 Nav2 插件（后期可选，不提前写）
            └── ...
```
