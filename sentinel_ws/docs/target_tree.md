# 用户目标目录摘录

来源：/home/ethan/桌面/算法导航提示词.md；保留规划状态，不表示所有文件已实现。

七、完整目标目录树

状态标记：

【已有】：之前已经查看到。
【修改】：已有文件需要调整。
【迁入】：已有资源建议放到此位置，尚未执行迁移。
【新增】：计划创建，尚未创建。
【后期】：后续阶段按需要加入。

以下是完整目标结构，不能一次性全部创建。

RoboVigor/                                               # 项目根目录：之前为 F:/RoboVigor/
├── README.md                                            # 【新增】自瞄、导航、环境与启动总说明
├── .gitignore                                           # 【新增或补充】忽略构建产物、录包、缓存
│
├── Autoaim/                                             # 【已有】自瞄项目，独立维护
│   ├── README.md                                        # 自瞄使用说明
│   ├── setup.py                                         # 普通 Python 项目安装配置
│   └── RV_Autoaim_2026/
│       ├── __init__.py
│       ├── start.py                                     # 启动入口
│       ├── autoaim.py                                   # 自瞄主流程
│       ├── camera.py                                    # 相机接入
│       ├── detector.py                                  # 目标检测
│       ├── pnp_solver.py                                # 位姿解算
│       ├── ballistic_solver.py                          # 弹道解算
│       ├── kalman_tracker.py                            # 目标跟踪
│       ├── publisher.py                                 # 数据发布
│       ├── monitor.py                                   # 监控显示
│       └── logger.py                                    # 日志记录
│
└── sentinel_ws/                                         # 【已有】沿用现有导航工作空间名
    ├── README.md                                        # 【新增】导航编译、仿真、建图、真机操作
    ├── dependencies.repos                               # 【新增】外部仓库与固定版本
    │
    ├── docs/                                            # 【新增】设计与调试文档
    │   ├── architecture.md                              # 模块结构、数据流和语言分工
    │   ├── interfaces.md                                # Topic/Action/Service、单位、类型、QoS
    │   ├── frames_and_time.md                           # TF 发布者、时间戳与同步约定
    │   ├── hardware.md                                  # 底盘、Mid-360S、IMU、主机、网络
    │   ├── simulation.md                                # Gazebo 版本、场地与机器人仿真
    │   ├── mapping_and_localization.md                  # 建图、地图对齐、定位和重定位
    │   ├── chassis_protocol.md                          # 与电控确认的底盘协议
    │   └── commissioning.md                             # 分阶段验收和排错
    │
    ├── scripts/                                         # 【新增】工作空间级脚本
    │   ├── build.sh                                     # 编译和驱动构建准备
    │   ├── sim.sh                                       # 启动仿真导航
    │   ├── mapping.sh                                   # 启动指定建图模式
    │   ├── nav.sh                                       # 启动真机导航
    │   ├── bag_record.sh                                # 录制传感器、TF、定位、速度与状态
    │   └── replay.sh                                    # rosbag2 回放及仿真时间配置
    │
    ├── deploy/                                          # 【后期】真机部署
    │   ├── sentry-nav@.service                           # systemd 自启模板
    │   └── udev/
    │       └── 99-sentry.rules                           # 实际串口设备稳定命名
    │
    ├── tools/                                           # 【新增】调试工具
    │   ├── check_tf.py                                  # TF 连通、重复发布与时间新鲜度
    │   ├── check_topics.py                              # 类型、频率、QoS 和延迟
    │   └── waypoint_convert.py                          # CSV/YAML 航点转换和检查
    │
    ├── data/                                            # 【新增】本机调试数据，默认不提交
    │   ├── README.md                                    # 数据存放与归档规则
    │   ├── bags/                                        # rosbag2 数据
    │   └── mapping/                                     # 建图中间结果
    │
    ├── src/
    │   │
    │   ├── rm_arena/                                    # 【已有】场地仿真与预览；ament_python
    │   │   ├── package.xml                              # 【修改】元数据与实际运行依赖
    │   │   ├── setup.py                                 # 【修改】安装 worlds/meshes 等资源
    │   │   ├── setup.cfg                                # 【已有】可执行程序安装位置
    │   │   ├── resource/
    │   │   │   └── rm_arena                             # 【已有】包发现标记
    │   │   ├── rm_arena/
    │   │   │   ├── __init__.py                          # 【已有】Python 模块标记
    │   │   │   └── arena_marker.py                      # 【修改】从包安装目录读取网格
    │   │   ├── launch/
    │   │   │   ├── simulation.launch.py                 # 【修改】沿用场地＋可选 RViz 入口
    │   │   │   ├── world.launch.py                      # 【新增】单独启动 Gazebo 场地
    │   │   │   └── arena_preview.launch.py              # 【新增】仅 RViz＋场地 Marker
    │   │   ├── worlds/
    │   │   │   ├── arena.world                          # 【迁入】原外部 gazebo_arena/worlds/
    │   │   │   └── empty.world                          # 【新增】底盘调试空场
    │   │   ├── meshes/
    │   │   │   └── rmul_2027.stl                        # 【迁入】原外部 gazebo_arena/meshes/
    │   │   ├── rviz/
    │   │   │   └── arena.rviz                           # 【已有】场地预览
    │   │   └── test/
    │   │       ├── test_copyright.py                    # 【已有】包规范检查
    │   │       ├── test_flake8.py                       # 【已有】代码风格检查
    │   │       └── test_pep257.py                       # 【已有】文档字符串检查
    │   │
    │   ├── sentry_description/                          # 【新增】机器人描述；ament_cmake
    │   │   ├── CMakeLists.txt                           # 安装模型和资源
    │   │   ├── package.xml
    │   │   ├── urdf/
    │   │   │   ├── sentry.urdf.xacro                    # 机器人总装
    │   │   │   ├── chassis.xacro                        # 底盘、车轮、碰撞与惯性
    │   │   │   ├── gimbal.xacro                         # 按实际结构加入云台关节
    │   │   │   └── sensors.xacro                        # Mid-360S/IMU 安装外参
    │   │   ├── meshes/
    │   │   │   └── chassis.stl                          # 有真实模型后加入，初期可用几何体
    │   │   ├── launch/
    │   │   │   └── description.launch.py                # robot_state_publisher
    │   │   └── rviz/
    │   │       └── model.rviz                           # 模型与坐标轴检查
    │   │
    │   ├── sentry_sim/                                  # 【新增】机器人仿真集成，不重复存场地
    │   │   ├── CMakeLists.txt
    │   │   ├── package.xml
    │   │   ├── urdf/
    │   │   │   └── sentry_sim.urdf.xacro                 # 引用描述，添加仿真插件和传感器
    │   │   ├── launch/
    │   │   │   ├── simulation.launch.py                 # 调用 rm_arena，生成机器人与控制
    │   │   │   ├── spawn_robot.launch.py                # 出生位姿和机器人生成
    │   │   │   └── sensors.launch.py                    # 仿真传感器接口适配
    │   │   └── config/
    │   │       ├── simulation.yaml                      # 模式、出生点、噪声和频率
    │   │       ├── controllers.yaml                     # 匹配实际底盘运动方式
    │   │       └── sensors.yaml                         # 雷达、IMU 仿真参数
    │   │
    │   ├── sentry_bringup/                              # 【新增】系统组合启动；ament_cmake
    │   │   ├── CMakeLists.txt
    │   │   ├── package.xml
    │   │   ├── launch/
    │   │   │   ├── sim_navigation.launch.py             # 仿真＋定位模式＋感知＋Nav2
    │   │   │   ├── sim_mapping.launch.py                # 仿真建图
    │   │   │   ├── robot_navigation.launch.py           # 真机驱动＋定位＋通信＋导航
    │   │   │   ├── robot_mapping.launch.py              # 真机采图和地图保存
    │   │   │   └── replay.launch.py                     # 离线回放处理
    │   │   ├── config/
    │   │   │   ├── sim.yaml                             # 场地、里程计来源、模块开关
    │   │   │   └── robot.yaml                           # 传感器数量、定位模式、模块开关
    │   │   └── rviz/
    │   │       └── navigation.rviz                      # 地图、机器人、点云、路径、代价地图
    │   │
    │   ├── sentry_navigation/                           # 【新增】Nav2 集成；ament_cmake
    │   │   ├── CMakeLists.txt
    │   │   ├── package.xml
    │   │   ├── launch/
    │   │   │   ├── navigation.launch.py                 # Nav2 服务和生命周期
    │   │   │   ├── map_server.launch.py                 # 加载指定场地栅格地图
    │   │   │   ├── mapping_2d.launch.py                 # 可选 slam_toolbox 建图
    │   │   │   └── localization_2d.launch.py            # 可选 AMCL，与三维定位互斥
    │   │   ├── config/
    │   │   │   ├── nav2_sim.yaml                        # 完整仿真参数基线
    │   │   │   ├── nav2_robot.yaml                      # 完整真机参数基线
    │   │   │   ├── slam_toolbox.yaml                    # 二维建图参数
    │   │   │   └── amcl.yaml                            # 二维定位路线按需使用
    │   │   └── behavior_trees/
    │   │       ├── navigate_to_pose.xml                 # 单点导航、重规划与恢复
    │   │       └── navigate_through_poses.xml           # 多点导航
    │   │
    │   ├── sentry_maps/                                 # 【新增】正式地图资源；ament_cmake
    │   │   ├── CMakeLists.txt
    │   │   ├── package.xml
    │   │   └── maps/
    │   │       └── rmul_2027/                           # 按实际赛场确认名称
    │   │           ├── README.md                        # 地图来源、制作方法和基准
    │   │           ├── manifest.yaml                    # 自定义资源清单，由代码显式读取
    │   │           ├── map.yaml                         # 建图后生成的地图元数据
    │   │           ├── map.pgm                          # 建图后生成的二维栅格图
    │   │           ├── prior.pcd                        # 后期生成的定位先验点云
    │   │           ├── regions.yaml                     # 禁区、限速区、补给区等语义
    │   │           └── waypoints.yaml                   # 航点、朝向、停留与失败策略
    │   │
    │   ├── sentry_tasks/                                # 【新增】任务决策；Python/ament_python
    │   │   ├── package.xml
    │   │   ├── setup.py                                 # 安装资源并注册入口
    │   │   ├── setup.cfg
    │   │   ├── resource/
    │   │   │   └── sentry_tasks
    │   │   ├── sentry_tasks/
    │   │   │   ├── __init__.py
    │   │   │   ├── navigation_client.py                 # Nav2 Action、取消、反馈和结果
    │   │   │   ├── goal_sender.py                       # 单点目标调试
    │   │   │   ├── waypoint_runner.py                   # 基础巡航
    │   │   │   ├── task_manager.py                      # 后期任务抢占、切换和失败处理
    │   │   │   ├── blackboard.py                        # 后期比赛、定位和目标状态
    │   │   │   └── fsm.py                               # 后期比赛策略状态机
    │   │   ├── config/
    │   │   │   └── rules.yaml                           # 后期状态转移和任务规则
    │   │   └── launch/
    │   │       ├── patrol.launch.py                     # 基础巡航入口
    │   │       └── decision.launch.py                   # 后期比赛决策入口
    │   │
    │   ├── sentry_motion/                               # 【新增】速度输出管理；配置集成包
    │   │   ├── CMakeLists.txt
    │   │   ├── package.xml
    │   │   ├── launch/
    │   │   │   └── motion.launch.py                     # 仲裁、平滑和碰撞监测
    │   │   └── config/
    │   │       ├── velocity_mux.yaml                    # 手动/自主优先级与超时
    │   │       ├── velocity_smoother.yaml               # 速度和加速度限制
    │   │       └── collision_monitor.yaml               # 按实际版本设置停止/减速区域
    │   │
    │   ├── sentry_sensors/                              # 【后期】真机传感器；ament_cmake
    │   │   ├── CMakeLists.txt
    │   │   ├── package.xml
    │   │   ├── launch/
    │   │   │   └── livox.launch.py                      # 验证过的 Mid-360S 驱动入口
    │   │   └── config/
    │   │       ├── mid360s.json                         # 匹配驱动版本的设备与网络配置
    │   │       └── sensor_topics.yaml                   # 启动代码读取的话题与 frame 配置
    │   │
    │   ├── sentry_localization/                         # 【后期】LIO 和地图定位；C++/ament_cmake
    │   │   ├── CMakeLists.txt
    │   │   ├── package.xml
    │   │   ├── include/sentry_localization/
    │   │   │   ├── odometry_adapter.hpp
    │   │   │   ├── map_localizer.hpp
    │   │   │   └── localization_monitor.hpp
    │   │   ├── src/
    │   │   │   ├── odometry_adapter.cpp                 # LIO 位姿到车体 odom 的外参转换
    │   │   │   ├── map_localizer.cpp                    # 地图匹配、初值、验收、map→odom
    │   │   │   └── localization_monitor.cpp             # 超时、质量和定位有效性检查
    │   │   ├── launch/
    │   │   │   ├── lio.launch.py                        # 启动所选 ROS 2 LIO 实现
    │   │   │   ├── localization.launch.py               # LIO＋先验地图定位＋监测
    │   │   │   └── mapping.launch.py                    # 点云地图采集与保存
    │   │   ├── config/
    │   │   │   ├── lio_mid360s.yaml                     # 字段、逐点时间、IMU 单位和外参
    │   │   │   └── localization.yaml                    # 配准、初值、阈值与重定位策略
    │   │   └── test/
    │   │       └── test_frame_conversion.cpp            # 位姿和外参转换验证
    │   │
    │   ├── sentry_perception/                           # 【按需新增】感知；C++/ament_cmake
    │   │   ├── CMakeLists.txt
    │   │   ├── package.xml
    │   │   ├── include/sentry_perception/
    │   │   │   ├── cloud_filter.hpp
    │   │   │   ├── terrain_analysis.hpp
    │   │   │   └── cloud_fusion.hpp
    │   │   ├── src/
    │   │   │   ├── cloud_filter.cpp                     # 去车体点、裁剪、降采样
    │   │   │   ├── terrain_analysis.cpp                 # 后期地面、障碍、高度和坡度分析
    │   │   │   └── cloud_fusion.cpp                     # 可选双雷达同步与运动补偿融合
    │   │   ├── launch/
    │   │   │   └── perception.launch.py                 # 组合过滤及现成点云转扫描节点
    │   │   └── config/
    │   │       ├── cloud_filter.yaml                    # 按真实车体尺寸配置
    │   │       ├── terrain.yaml                         # 地形阈值
    │   │       └── pointcloud_to_scan.yaml              # 需要 LaserScan 时使用
    │   │
    │   ├── sentry_interfaces/                           # 【后期按需】自定义接口；ament_cmake
    │   │   ├── CMakeLists.txt                           # rosidl 生成与依赖声明
    │   │   ├── package.xml
    │   │   ├── action/
    │   │   │   └── ExecuteTask.action                   # 上层任务、反馈、结果和取消
    │   │   ├── msg/
    │   │   │   ├── NavStatus.msg                        # 导航状态和失败原因
    │   │   │   ├── LocalizationStatus.msg               # 定位质量、有效性和重定位状态
    │   │   │   ├── ChassisState.msg                     # 下位机反馈和连接状态
    │   │   │   ├── SiteRegion.msg                       # 单区域几何和通行语义
    │   │   │   └── SiteMap.msg                          # 带 frame 和版本的区域集合
    │   │   └── srv/
    │   │       ├── ResetLocalization.srv                # 重定位请求，最终状态另行反馈
    │   │       └── SetSite.srv                          # 停用导航后协调切换场地资源
    │   │
    │   ├── sentry_chassis_bridge/                       # 【后期】通信；Python/ament_python
    │   │   ├── package.xml
    │   │   ├── setup.py
    │   │   ├── setup.cfg
    │   │   ├── resource/
    │   │   │   └── sentry_chassis_bridge
    │   │   ├── sentry_chassis_bridge/
    │   │   │   ├── __init__.py
    │   │   │   ├── chassis_bridge.py                    # 速度、反馈、超时与断连处理
    │   │   │   ├── referee_bridge.py                    # 按真实链路接入裁判数据
    │   │   │   └── protocol/
    │   │   │       ├── __init__.py
    │   │   │       ├── chassis_protocol.py              # 与电控确认帧格式、单位和坐标系
    │   │   │       ├── referee_protocol.py              # 对应赛季裁判协议
    │   │   │       └── crc.py                           # 按协议与已知报文验证
    │   │   ├── config/
    │   │   │   └── comm.yaml                            # 设备、速率、周期、超时与话题
    │   │   ├── launch/
    │   │   │   └── chassis.launch.py
    │   │   └── test/
    │   │       └── test_protocol.py                     # 已知帧、错误帧、拆包与粘包
    │   │
    │   ├── sentry_nav_plugins/                          # 【后期可选】自研插件；C++/ament_cmake
    │   │   ├── CMakeLists.txt
    │   │   ├── package.xml
    │   │   ├── plugins/
    │   │   │   ├── planner_plugins.xml
    │   │   │   ├── controller_plugins.xml
    │   │   │   └── costmap_plugins.xml
    │   │   ├── include/sentry_nav_plugins/
    │   │   │   ├── global_planner.hpp                   # 有必要时实现自研规划器
    │   │   │   ├── omni_controller.hpp                  # 自研全向控制器接口
    │   │   │   ├── terrain_layer.hpp                    # 地形代价层接口
    │   │   │   └── site_prior_layer.hpp                 # 特殊区域代价层接口
    │   │   ├── src/
    │   │   │   ├── global_planner.cpp                   # 搜索、碰撞检查和路径生成
    │   │   │   ├── omni_controller.cpp                  # 跟踪、碰撞检查和运动约束
    │   │   │   ├── terrain_layer.cpp                    # 更新、清除和未知区域处理
    │   │   │   └── site_prior_layer.cpp                 # 区域代价，不清除真实障碍
    │   │   └── test/
    │   │       ├── test_global_planner.cpp
    │   │       ├── test_omni_controller.cpp
    │   │       └── test_costmap_layers.cpp
    │   │
    │   └── third_party/                                 # 【后期】上游源码，本目录不是 ROS 包
    │       ├── livox_ros_driver2/                       # 固定验证过、支持 Mid-360S 的版本
    │       ├── <选定的 ROS 2 LIO 仓库>/                  # 占位，确认真实仓库与分支后引入
    │       └── small_gicp/                              # 可选配准库
    │
    ├── build/                                           # 【已有】自动生成
    ├── install/                                         # 【已有】自动生成
    └── log/                                             # 【已有】自动生成

补充说明：

- 原 RoboVigor/gazebo_arena/ 是迁移来源，目前不能假设已经移走。
- arena.world.bak 是旧备份，不作为必须安装的运行资源。
- 迁移时先保留原资源，更新安装和路径并验证成功后，再处理重复文件。
- 每次具体开发前展示相关部分的 tree，标明已有、新增、修改和用途。
- 目标树中的地图、点云、机器人网格及尚未选定的外部仓库，不要伪装成已存在的文件。
- 允许依据实际工程调整结构，但要先解释原因，不随意推翻已完成工作。

