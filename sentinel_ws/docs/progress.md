# RoboVigor 导航开发记录

## 当前轮子TF（用户最终要求）
- 已删除wheel_visuals.py和底盘底部wheels_link。
- 四个wheel_i_link在各自真实轮轴中心独立旋转；由原生RSP读取实际轮角。
- RViz为标准RobotModel，每轮含轮毂/滚子外观；Gazebo保留112被动滚子物理。
- 以下先前聚合轮组/私有TF/Marker显示记录均已被本版本替代。


## 当前部件 TF
- sentry_description 定义CAD名义轮组、两颗雷达、相机/光学和枪管/枪口参考。
- 对外只有 wheels_link；完整物理/动画关节保留在单独显示总线，官方 RViz 已配置。
- 31项Python检查及实际TF/轮子/云台验证通过；详见 frames_and_time.md 和 validation/public_frames。


## 当前目录重构
- 按桌面《算法导航提示词.md》将已有功能迁入 rm_arena、sentry_description、sentry_sim、sentry_motion、sentry_bringup。
- 当前统一启动入口为 sentry_bringup/sim_teleop.launch.py；旧 sentry_simulation 不再提供运行入口。
- 工具和全部文档移入 sentinel_ws，旧顶层场地源归档 data/legacy_gazebo_arena，Autoaim 未修改。
- 以下历史记录中的包名/工具路径按 docs/project_tree.md 迁移表对应，不是当前操作命令。


## 2026-10-29 全向轮物理驱动（当前版本）
- 四个真实 CAD 轮毂独立驱动，112 个橡胶滚子使用真实轴线的被动关节；电机外壳、支架固定在底盘。
- 移除 planar_move；底盘由有限轮轴力矩和 Gazebo 接触摩擦驱动，实际关节角同步到 RViz。
- 云台改用有限力矩反馈电机，保留 X 小陀螺和世界航向保持。
- 有效接触半径约 76.1 mm；质量总计约 10 kg。质量、惯量、摩擦尚未标定，滚子采用拟合球碰撞。
- 构建成功，CTest 10/10；colcon 汇总 31 tests、0 errors、0 failures、6 skipped（含工具默认跳过项）。
- 当前验证与物理近似说明：validation/wheel_physics/README.md。
- 以下为历史记录；旧版的理想平面运动、固定轮子及理想云台执行器已被本节版本替代。


## 2026-10-29 键盘加速与小陀螺
- 真实 CAD 拆为底盘和上方云台两个网格，零角保留原外观。
- 删除旧 sentry_simple.urdf（源码与安装目录），底盘碰撞改为方盒。
- gimbal_yaw_joint 使用原 URDF z=0.051 m 主 yaw 轴；Gazebo 插件在仿真步内
  根据真实云台世界姿态反向补偿，发布实际 joint_states 与 gimbal_pose。
- 完整控制入口：ros2 launch sentry_simulation sim_teleop.launch.py。
  同时加载场地、真实车、Gazebo、RViz、看门狗和键盘终端。
- W/S/A/D 默认 0.8 m/s；Q/E 1.5 rad/s；X 开启 3 rad/s 小陀螺；
  C 关闭并停车，空格全停。X 重复输入保持开启。
- 平移输入 0.3 秒超时，小陀螺保持至 C/空格；键盘失联 0.5 秒全停。
  小陀螺中的平移参考实际云台世界航向，反馈采样仍有小量侧偏。
- 构建通过，Python 测试 10 项通过，完整 CTest 9/9 通过。
- 真实键盘伪终端实测：前后移动成功；底盘转 7.032 rad，云台航向最大偏差
  1.183e-6 rad；C、空格、失联停车均成功，实际里程计最终速度为零。
- 参数为仿真近似：底盘 8 kg、云台 2 kg，理想平面移动与理想 yaw 执行器；
  小 yaw、pitch、轮子和滚子暂不独立驱动。
- 详见 validation/sentry_spin/README.md、metrics.json 和控制包 README。


## 2026-10-29 用户 CAD 整车接入
- 用户原始 URDF 已原样保存在 src/sentry_simulation/urdf/sentry_original.urdf。
- 从用户授权的 大小yaw哨兵/哨兵总装.SLDASM 原生显示缓存恢复整车；
  默认入口使用派生 sentry_cad.urdf 与随包安装的 sentry_cad.stl。
- 全部可见零件实例均有缓存，没有用缺少配置的零件默认网格补位。
  移除两个 MID-360 雷达的扫描范围辅助外壳，保留硬件；1 mm 顶点栅格简化。
- 默认使用 CAD 保存姿态，云台/滚子暂不独立驱动。底盘保留理想全向移动接口；
  质量、惯量与碰撞包络仍是临时仿真参数。
- 新完整入口：ros2 launch sentry_simulation simulation.launch.py。
  同时启动场地、整车、Gazebo 和 RViz，不需要 GNOME 键盘终端。
- 默认出生 (1.25,6.75,0.118)，world → odom → base_link → body_link；
  Gazebo 与 RViz 共用解析到安装目录 mesh file URI 的 robot_description。
- Gazebo 服务端和客户端均收到场地模型路径；新增真实子进程环境回归检查。
  arena_marker 正常退出时使用 try_shutdown，避免 Ctrl+C 后重复关闭报错。
- 构建通过；rm_arena 包 pytest 为 6 passed、1 skipped；sentry_simulation
  包 pytest 为 5 passed；原生目录解析回归 1 passed。sentry_simulation
  完整 CTest 全部通过，colcon 汇总 15 tests、0 errors、0 failures。
  XML schema 验证需联网，已在沙箱外执行通过。工具链弃用警告仍存在。
- 全仓根目录 pytest 的自瞄 gxipy 缺失问题已记录，未改动自瞄功能。
- 实际安装入口已验证整车生成、网格 URI、里程计与 TF；实测 TF 约
  (1.25,6.75,0.1164)。测试使用独立 ROS 域 178、Gazebo 端口 11474，结束后关闭。
- 详见 sentry_urdf_import.md 和 validation/cad_sentry/ 中的验证记录。


## 2026-10-28 rm_arena 包补齐
- models、worlds、来源说明和 README 已加入 setuptools 安装清单。
- Gazebo world 和 RViz Marker 均从 ament 的 rm_arena 安装目录解析，
  不再依赖 ~/RoboVigor/gazebo_arena 或 ROBOVIGOR_ROOT。
- 保留 Gazebo ROS 初始化、factory 插件、原有 GAZEBO_MODEL_PATH 和 RViz 开关。
- 补齐 launch、launch_ros、gazebo_ros、rviz2 运行依赖及 ament_python 构建声明；
  package.xml 与 setup.py 版本统一为 0.0.1。
- 新增安装资源闭包测试，覆盖 world → model → mesh → texture 及模型配置引用。
- 临时隔离安装和当前 sentinel_ws 的 colcon build 均成功；包目录完整 pytest
  为 4 passed、1 skipped（原有版权模板检查跳过），有工具链弃用警告。
- 标准 colcon test 的结果汇总：5 tests、0 errors、0 failures、1 skipped。
- 在 /tmp 中只 source 隔离安装，真实验证 Marker 的晚加入订阅接收、
  安装网格 URI、Gazebo /clock、/spawn_entity 服务及 rmul_2027 模型查询成功。
  运行测试使用独立 ROS 域 176 和 Gazebo 端口 11472，测试进程已退出。
- 从工作空间根目录运行 pytest 时，test_flake8/test_pep257 会扫描整个工作空间，
  因其他包的旧构建链接和已有文档格式报错；包目录测试通过，未改动其他包。
- Gazebo/RViz 图形外观仍待人工验收；本次没有推进雷达、导航或自瞄迁移。
- 启动：在 sentinel_ws 中 source /opt/ros/humble/setup.bash 和 install/setup.bash，
  然后执行 ros2 launch rm_arena simulation.launch.py。

## 已确认
- PC：Ubuntu 22.04、ROS 2 Humble、Gazebo Classic 11；车载平台计划为 Jetson Orin Nano。
- 保留现有 sentinel_ws 工作空间与 rm_arena 场地包。
- 麦克纳姆轮全向底盘，包含突出部分的整车最大直径为 580 mm。
- 导航复用成熟 C++ 组件；决策和任务管理优先 Python。
- 正式 URDF 尚未提供，先使用简化模型推进仿真；A 板协议后续确认。
- 参考项目：/home/ethan/桌面/sentry26；按需参考架构，外参、赛场坐标和硬件接口需重新核实。

## 当前模型
- src/sentry_simulation/urdf/sentry_simple.urdf：半径 0.29 m 的圆柱包络。
- 高度 0.20 m、质量 10 kg 为临时仿真参数，惯量按均匀圆柱计算。
- 用户已在 PC 验证 URDF 到 SDF 转换成功，半径和惯量正确。
- 已添加 launch/spawn_robot.launch.py：在运行中的 Gazebo 生成模型，x/y/z 可配置。
- rm_arena 的 Gazebo 启动入口已增加 ROS 初始化和 factory 插件。
- 用户已确认模型出现，且没有穿透、持续抖动或翻倒。
- 已配置 gazebo_ros_planar_move：订阅 /cmd_vel (Twist)，发布 /odom (Odometry) 和 odom -> base_link TF，反馈目标频率 30 Hz，使用仿真时间戳；运行表现待用户验证。
- /cmd_vel 分量为车体坐标 x 前、y 左、z 上，线速度 m/s，角速度 rad/s。插件是现成 C++ 实现。
- 插件反馈来自 Gazebo 世界位姿，不是真实编码器里程计；不模拟麦轮打滑，且没有指令超时停车功能，测试需显式发送零速度。
- 尚未添加雷达。插件会设置竖直速度为零，加载位置高度需要接近实际支撑面加车体半高，不能依赖初始悬空后自然下落。

## 下一步
- 用户已验证 /cmd_vel 有订阅者、/odom 输出正常，低速前进和零速度停车成功。
- 已添加 sim_teleop.launch.py 一键启动原场地、模型、键盘控制终端及独立看门狗。
- W/S 前后、A/D 横移、Q/E 旋转，空格或 X 停车；一次一个方向；默认 0.2 m/s、0.5 rad/s。
- 键盘无新输入 0.3 秒后发送零速度；看门狗输入失联 0.5 秒后输出零速度。终端依赖系统按键重复，不支持真正的 key-up 事件。
- 看门狗运行时应独占 /cmd_vel 发布；后续 Nav2 接入时需重新设计速度源选择，不能同时运行手动发布命令。
- 当前任务等待用户验证新窗口、按键运动、松键停车及关闭键盘窗口后的失联停车。尚未验证图形界面端到端效果。
- 后续依次验证全向运动、仿真里程计与 TF、雷达、地图与定位、Nav2、Python 决策任务。
- 每次只推进一个明确任务，等待用户运行反馈后继续。
